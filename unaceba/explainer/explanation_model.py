from unaceba.explainer.episodic_memory import EpisodicMemory,MemoryNode
from unaceba.explainer.task_model import TaskModel
from unaceba.bt.nodes import LeafNode,ActionNode,ConditionNode
from unaceba.task.state import State
from unaceba.utils.variables import VarRange,BooleanRange,CategoricalRange

import networkx as nx
import matplotlib.pyplot as plt
import py_trees
from typing import Dict
from rclpy.node import Node

EXECUTION_CATEGORY = "Execution"
RETURN_CATEGORY = "Return"
STATE_CATEGORY = "State"

NODE_RETURNS = {
    "Status.SUCCESS":py_trees.common.Status.SUCCESS,
    "Status.FAILURE":py_trees.common.Status.FAILURE,
    "Status.RUNNING":py_trees.common.Status.RUNNING,
    "Status.INVALID":py_trees.common.Status.INVALID,
}

class ExplanationModelNode:
    def __init__(self,node_id:str,node_name:str,category:str,btnode_id:str=None,var_name:str=None,time_index:int=None):
        self.id = node_id
        self.name = node_name
        self.category = category
        self.btnode_id = btnode_id
        self.var_name = var_name
        self.time_index = time_index

    @classmethod
    def node_from_bt(cls,btnode:MemoryNode,category:str):
        node_id = f"{category}_{btnode.id}"
        node_name = f"{category}_{btnode.name}"

        if category not in [EXECUTION_CATEGORY,RETURN_CATEGORY]:
            raise ValueError(f"Invalid category {category} for node {btnode}")

        return cls(node_id,node_name,category,btnode_id=btnode.id)

    @classmethod
    def node_from_state(cls,var:str,index:int):
        node_id = f"{var}_t{index}"
        node_name = f"{var}_t{index}"

        return cls(node_id,node_name,STATE_CATEGORY,var_name=var,time_index=index)
    
    '''
    UTILS
    '''
    def is_execution(self) -> bool:
        return self.category == EXECUTION_CATEGORY
    
    def is_return(self) -> bool:
        return self.category == RETURN_CATEGORY
    
    def is_state_variable(self) -> bool:
        return self.category == STATE_CATEGORY

class ExplanationModel:
    def __init__(
            self,
            episodic_memory:EpisodicMemory,
            task_model:TaskModel,
            probabilistic:bool=True,
            ros_node:Node=None,
    ):
        '''
        Creates the explanation model combining BT structure and the task model
        '''
        self.em = episodic_memory
        self.tm = task_model
        self.probabilistic = probabilistic
        self.ros_node = ros_node

        # Create explanation model structure
        self.nodes:Dict[str,ExplanationModelNode] = {}
        self.executions:Dict[str,str] = {}
        self.returns:Dict[str,str] = {}
        self.explanation_graph = self.create_graph_from_bt(
            nodes=self.nodes,
            executions=self.executions,
            returns=self.returns
        )

        self.btnode_times = self.assign_times_to_bt_nodes()

        self.temporal_state_vars:Dict[str,str] = {}
        self.explanation_graph = self.add_states_to_graph(
            graph=self.explanation_graph,
            nodes=self.nodes,
            executions=self.executions,
            returns=self.returns,
            temporal_state_vars=self.temporal_state_vars
        )


        # Create ranges and functions(cpds)
        self.var_ranges = self.calculate_ranges()

        self.var_funcs = self.calculate_variable_functions()
        if probabilistic:
            self.var_cpds = self.calculate_variable_cpds()           


        #self.visualise_explanation_graph()

    '''
    DEBUGGING
    '''
    def log(self,text:str):
        if self.ros_node is None:
            print(text)
        else:
            self.ros_node.get_logger().info(str(text))

    '''
    EXPLANATION GRAPH
    '''
    def create_graph_from_bt(
            self,
            nodes:Dict[str,ExplanationModelNode],
            executions:dict[str,str],
            returns:dict[str,str],
        ) -> nx.DiGraph:
        graph = nx.DiGraph()

        # Start by creating nodes for every bt node
        for btnode_id in self.em.btnodes:
            btnode:MemoryNode = self.em.btnodes[btnode_id]

            execution_node = ExplanationModelNode.node_from_bt(btnode=btnode,category=EXECUTION_CATEGORY)
            nodes[execution_node.id] = execution_node
            executions[btnode_id] = execution_node.id
            graph.add_node(execution_node.id)

            return_node = ExplanationModelNode.node_from_bt(btnode=btnode,category=RETURN_CATEGORY)
            nodes[return_node.id] = return_node
            returns[btnode_id] = return_node.id
            graph.add_node(return_node.id)

        # Add edges
        for btnode_id in self.em.btnodes:
            btnode:MemoryNode = self.em.btnodes[btnode_id]

            # Add return edge
            graph.add_edge(executions[btnode.id],returns[btnode.id])
            if btnode.is_composite():
                for child in btnode.children:
                    graph.add_edge(returns[child.id],returns[btnode.id])

            # Add execution edge
            if not btnode.is_root():
                if btnode.is_leftmost_child():
                    graph.add_edge(executions[btnode.parent.id],executions[btnode.id])
                else:
                    left_sibling = btnode.left_sibling()
                    graph.add_edge(returns[left_sibling.id],executions[btnode.id])

        return graph
    
    def assign_times_to_bt_nodes(self) -> dict[str,int]:
        temporalities = {}
        i = 0
        for node_id in self.em.ordered_nodes:
            if self.em.btnodes[node_id].is_leaf():
                temporalities[node_id] = i
                i += 1
        return temporalities
    
    def add_states_to_graph(
        self,
        graph:nx.DiGraph,
        nodes:Dict[str,ExplanationModelNode],
        executions:dict[str,str],
        returns:dict[str,str],
        temporal_state_vars:dict[str,str]
    ) -> nx.DiGraph:
        
        # Create a temporal state at each timestep
        num_timesteps = len(self.em.ordered_leaf_nodes)+1
        for var in self.tm.state_vars():
            temporal_state_vars[var] = []
            for t in range(num_timesteps):
                temporal_state_var = ExplanationModelNode.node_from_state(var,t)
                temporal_state_vars[var].append(temporal_state_var.id)
                nodes[temporal_state_var.id] = temporal_state_var

        # Add edges
        for t in range(num_timesteps):
            # Create causal links within a single timestep
            for edge in self.tm.cm_edges():
                e0 = temporal_state_vars[edge[0]][t]
                e1 = temporal_state_vars[edge[1]][t]
                graph.add_edge(e0,e1)

        # Environment Inputs
        env_inputs,env_outputs = self.calculate_environment_inputs_outputs()

        # Add input/output edges
        for leaf_id in self.em.ordered_leaf_nodes:
            behaviour:LeafNode = self.em.btnodes[leaf_id].behaviour

            # Inputs
            input_vars = behaviour.input_variables() + env_inputs[leaf_id]
            output_vars = behaviour.output_variables() + env_outputs[leaf_id]

            if "" in input_vars or "" in output_vars:
                # TODO: Alternatively, remove it or something like that
                raise ValueError(f"Behaviour {behaviour.name} contains an empty string in either input or output variable set, which is not allowed.")

            # Leaf input nodes
            for input_var in input_vars:
                temporal_input_var = temporal_state_vars[input_var][self.btnode_times[leaf_id]]
                graph.add_edge(temporal_input_var,returns[leaf_id])

            # Leaf output nodes
            for output_var in output_vars:
                temporal_output_var = temporal_state_vars[output_var][self.btnode_times[leaf_id]+1]
                graph.add_edge(executions[leaf_id],temporal_output_var)

            # The effect of executing a node on the output state variables
            for input_var in input_vars:
                temporal_input_var = temporal_state_vars[input_var][self.btnode_times[leaf_id]]
                for output_var in output_vars:
                    temporal_output_var = temporal_state_vars[output_var][self.btnode_times[leaf_id]+1]
                    graph.add_edge(temporal_input_var,temporal_output_var)


        # Link all temporal versions together
        for var in self.tm.state_vars():
            for t in range(num_timesteps-1):
                graph.add_edge(temporal_state_vars[var][t],temporal_state_vars[var][t+1])

        return graph
    
    def calculate_environment_inputs_outputs(self) -> tuple[dict[str,list[str]],dict[str,list[str]]]:
        env_inputs = {leaf_id:[] for leaf_id in self.em.ordered_leaf_nodes}
        for edge in self.tm.environment_inputs():
            var_name = edge[0]
            btnode_name = edge[1]

            for btnode_id in self.em.node_name_to_ids[btnode_name]:
                #env_inputs[btnode_id].append(temporal_state_vars[var_name][self.btnode_times[btnode_id]])
                env_inputs[btnode_id].append(var_name)
                    
        env_outputs = {leaf_id:[] for leaf_id in self.em.ordered_leaf_nodes}
        for edge in self.tm.environment_outputs():
            var_name = edge[1]
            btnode_name = edge[0]

            for btnode_id in self.em.node_name_to_ids[btnode_name]:
                env_outputs[btnode_id].append(var_name)

        return env_inputs,env_outputs
    
    '''
    VARIABLE RANGES
    '''
    def calculate_ranges(self) -> Dict[str,VarRange]:
        ranges = {}
        # Start by adding ranges for BT node execution/return variables
        for btnode_id in self.em.btnodes:
            # Execution
            execution_node:ExplanationModelNode = self.nodes[self.executions[btnode_id]]
            ranges[execution_node.id] = BooleanRange()

            # Return
            return_node:ExplanationModelNode = self.nodes[self.returns[btnode_id]]
            ranges[return_node.id] = CategoricalRange([
                py_trees.common.Status.SUCCESS,
                py_trees.common.Status.FAILURE,
                py_trees.common.Status.INVALID,
            ])
            if self.em.btnodes[btnode_id].is_action_node():
                ranges[return_node.id].add_value(py_trees.common.Status.RUNNING)

        # Add state variable ranges
        state_var_ranges = self.tm.calculate_state_var_ranges()
        for var in state_var_ranges:
            for var_t in self.temporal_state_vars[var]:
                ranges[var_t] = state_var_ranges[var]

        return ranges

    '''
    FUNCTIONS
    '''
    @staticmethod
    def sequence_return(child_vals:list) -> py_trees.common.Status:
        for child_val in child_vals:
            if child_val in [py_trees.common.Status.FAILURE,py_trees.common.Status.RUNNING]:
                return child_val
            elif child_val == py_trees.common.Status.INVALID:
                # Not allowed
                raise ValueError(f"Child of an executed node cannot be invalid")
        # Must have succeeded
        return py_trees.common.Status.SUCCESS
    
    @staticmethod
    def fallback_return(child_vals:list) -> py_trees.common.Status:
        for child_val in child_vals:
            if child_val in [py_trees.common.Status.SUCCESS,py_trees.common.Status.RUNNING]:
                return child_val
            elif child_val == py_trees.common.Status.INVALID:
                # Not allowed
                raise ValueError(f"Child of an executed node cannot be invalid")
        # Must have failed
        return py_trees.common.Status.FAILURE

    def execution_function(self,node_id:str,explanation_model_vals:dict) -> bool:
        memory_node = self.em.btnodes[self.nodes[node_id].btnode_id]
        if memory_node.is_root():
            # The root of the tree is always executed
            return True
        
        # Must be the child of a composite node, function depends on position in sibling list
        if memory_node.is_leftmost_child():
            # First child, execution depends on parent's execution
            parent_execution_value = explanation_model_vals[self.executions[memory_node.parent.id]]
            return parent_execution_value
        
        # If here, we are the second child or onwards
        left_sibling_return_value = explanation_model_vals[self.returns[memory_node.left_sibling().id]]
        if memory_node.parent.is_sequence():
            # Sequence parent: node executes if the left sibling succeeds
            return left_sibling_return_value == py_trees.common.Status.SUCCESS
        elif memory_node.parent.is_fallback():
            # Fallback parent: node executes if the left sibling fails
            return left_sibling_return_value == py_trees.common.Status.FAILURE
        
        # Shouldn't be here
        raise ValueError(f"Unknown parent type: {memory_node.parent.category}")

    def return_function(self,node_id:str,explanation_model_vals:dict,dummy_state:State) -> py_trees.common.Status:
        memory_node = self.em.btnodes[self.nodes[node_id].btnode_id]
        execution_node_value = explanation_model_vals[self.executions[memory_node.id]]
        if not execution_node_value:
            # The node was never executed, cannot return a valid return status
            return py_trees.common.Status.INVALID
        
        if memory_node.is_leaf():
            # Must execute the node's function
            return memory_node.behaviour.execute(dummy_state)
        
        # Must be composite
        child_vals = [explanation_model_vals[child.id] for child in memory_node.children]
        if memory_node.is_sequence():
            return self.sequence_return(child_vals)
        elif memory_node.is_fallback():
            return self.fallback_return(child_vals)
        
        # Shouldn't be here
        raise ValueError(f"Unknown parent type: {memory_node.parent.category}")
        

    def calculate_variable_functions(self) -> Dict[str,callable]:
        pass


    '''
    PROBABILISTIC ELEMENTS
    '''
    def calculate_variable_cpds(self):
        pass

    '''
    LOADING
    '''
    def model_state_at_timestep(self,timestep_tick:int=None,timestep_time:int=None) -> dict:
        # Handle None inputs
        if timestep_tick is None:
            # Assume last tick
            timestep_tick = self.em.last_tick()
        if timestep_time is None:
            # Assume last time
            timestep_time = self.em.last_time_at_tick(timestep_tick)

        # Validation
        if not self.em.valid_timestep(timestep_tick,timestep_time):
            raise ValueError(f"Invalid timestep {timestep_tick}:{timestep_time} for file {self.em.filepath}")
        
        # Start by setting the initial state
        model_state = self.initial_state()

        # Iteratively calculate the next state
        curr_tick = 0
        curr_time = 0
        found_time = False

        self.value_history = {}
        self.update_history = {}

        while not found_time:
            next_tick,next_time = self.em.get_next_timestep(curr_tick,curr_time)
            self.log(f"At {curr_tick}:{curr_time}, next step is {next_tick}:{next_time}")
            self.log(self.em.timesteps)

            if next_tick is None:
                # Oops, this shouldn't happen
                raise ValueError(f"Reached the end of time without finding the timestep. This shouldn't happen")
            
            if next_tick == curr_tick:
                # We haven't advanced tick, no need to reset any variables
                update = self.em.get_update_at_timestep(next_tick,next_time)

                # First, update the relevant variables associated with the executed BT node
                for btnode_id in update["update"]:
                    # Node has been executed
                    model_state[self.executions[btnode_id]] = True
                    # Status has been updated
                    model_state[self.returns[btnode_id]] = NODE_RETURNS[update["update"][btnode_id]["status"]]

                    # Updating a leaf node implies all parents have been executed
                    ancestors = self.em.get_BT_ancestors(btnode_id)
                    self.log(ancestors)

                    # TODO: FINISH



            # TODO: Change once real logic implemented
            found_time = True

    def get_state_at_time(self,model_state:dict,time:int) -> State:
        state_vals = {
            state_var:model_state[self.temporal_state_vars[state_var][time]] for state_var in self.tm.state_only_variables
        }
        state = self.tm.make_state(state_vals)
        return state


    def initial_state(self) -> dict:
        model_state = {node_id:None for node_id in self.nodes}

        # Add BT node values
        for node_id in self.nodes:
            node = self.nodes[node_id]
            if node.is_execution():
                # Initial state : nothing has been executed yet
                model_state[node_id] = False
            elif node.is_return():
                # Initial state : nothing has returned a status yet
                model_state[node_id] = py_trees.common.Status.INVALID

        # Add initial timestep values for state variables
        for state_var in self.tm.state_only_variables:
            model_state[self.temporal_state_vars[state_var][0]] = self.em.get_state_var_value_at_time(state_var,0,0)

        # Add initial timestep values for model variables
        initial_state = self.get_state_at_time(model_state,time=0)
        model_var_vals = self.tm.calculate_model_var_values(initial_state)
        for model_var in self.tm.model_only_variables:
            model_state[self.temporal_state_vars[model_var][0]] = model_var_vals[model_var]
    
        return model_state
        

         
    
    '''
    VISUALISATION
    '''
    def visualise_explanation_graph(self):
        labels = {node_id: self.nodes[node_id].name for node_id in self.explanation_graph.nodes()}

        categories = [self.nodes[node_id].category for node_id in self.explanation_graph.nodes()]
        unique_cats = list(set(categories))
        
        color_palette = plt.cm.get_cmap('tab10', len(unique_cats))
        cat_to_color = {cat: color_palette(i) for i, cat in enumerate(unique_cats)}
        
        node_colors = [cat_to_color[cat] for cat in categories]

        plt.figure(figsize=(10, 8))
        pos = nx.spring_layout(self.explanation_graph, seed=42)  # Consistent layout
        
        nx.draw(
            self.explanation_graph, pos, 
            labels=labels, 
            node_color=node_colors, 
            with_labels=True, 
            node_size=2000, 
            font_size=10, 
            font_weight="bold", 
            arrowsize=20,
            edge_color="gray"
        )

        for cat, color in cat_to_color.items():
            plt.scatter([], [], c=[color], label=cat)
        plt.legend(title="Categories")

        plt.show()







            

        

        


        
            

        


