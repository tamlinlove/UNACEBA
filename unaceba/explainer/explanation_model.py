from unaceba.explainer.episodic_memory import EpisodicMemory,MemoryNode
from unaceba.explainer.task_model import TaskModel
from unaceba.bt.nodes import LeafNode,ActionNode,ConditionNode
from unaceba.task.state import State
from unaceba.utils.variables import VarRange,BooleanRange,CategoricalRange

import networkx as nx
import matplotlib.pyplot as plt
import py_trees
from typing import Dict

EXECUTION_CATEGORY = "Execution"
RETURN_CATEGORY = "Return"
STATE_CATEGORY = "State"

class ExplanationModelNode:
    def __init__(self,node_id:str,node_name:str,category:str,btnode_id:str=None,var_name:str=None):
        self.id = node_id
        self.name = node_name
        self.category = category
        self.btnode_id = btnode_id
        self.var_name = var_name

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

        return cls(node_id,node_name,STATE_CATEGORY,var_name=var)

class ExplanationModel:
    def __init__(
            self,
            episodic_memory:EpisodicMemory,
            task_model:TaskModel,
            probabilistic:bool=True
    ):
        '''
        Creates the explanation model combining BT structure and the task model
        '''
        self.em = episodic_memory
        self.tm = task_model
        self.probabilistic = probabilistic

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







            

        

        


        
            

        


