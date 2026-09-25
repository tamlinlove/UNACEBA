import py_trees
import networkx as nx
import hashlib
import random

from unaceba.task.state import State
from unaceba.bt.nodes import LeafNode
from unaceba.utils.variables import VarRange,NormalisedFloatRange
from unaceba.explainer.episodic_memory import MemoryNode
from unaceba.explainer.explanation_model import ExplanationModel,ExplanationModelNode,EXECUTION_CATEGORY,RETURN_CATEGORY,STATE_CATEGORY
from unaceba.probabilistic_explainer.probabilistic_causal_model import ProbabilisticCausalModel,ProbabilisticCausalNode
from unaceba.probabilistic_explainer.probabilistic_task_model import ProbabilisticTaskModel

from typing import TYPE_CHECKING,Dict
if TYPE_CHECKING:
    from typing import Self
else:
    try:
        from typing import Self
    except ImportError:
        from typing_extensions import Self

EXOGENOUS_CATEGORY = "Exogenous"

class ModelStateValue:
    '''
    Represents the value (or probability distribution over values) of a variable in the model state
    '''
    def __init__(self,value):
        self.add_value(value)

    def __str__(self):
        if self.probabilistic:
            return str(self.distribution)
        else:
            return str(self.value)
        
    def __eq__(self, value):
        if isinstance(value,ModelStateValue):
            return self.value == value.value
        else:
            return self.value == value

    def add_value(self,value):
        self.value = value
        self.distribution = None
        self.probabilistic = False

    def add_distribution(self,distribution:dict):
        self.value = None
        self.distribution = distribution
        self.probabilistic = True

class ProbabilisticExplanationModelNode(ExplanationModelNode):
    allowed_bt_categories = [EXECUTION_CATEGORY,RETURN_CATEGORY,EXOGENOUS_CATEGORY]

    def __init__(self, node_id, node_name, category, btnode_id = None, var_name = None, time_index = None):
        super().__init__(node_id, node_name, category, btnode_id, var_name, time_index)

    '''
    UTILS
    '''
    def is_exogenous(self):
        return self.category == EXOGENOUS_CATEGORY

class ProbabilisticExplanationModel(ExplanationModel):
    def __init__(self, episodic_memory, task_model, probabilistic = True, ros_node = None):
        super().__init__(episodic_memory, task_model, probabilistic, ros_node)

        # Typing
        self.tm:ProbabilisticTaskModel

    '''
    INITIALISATION
    '''
    def init_model_dictionaries(self):
        super().init_model_dictionaries()

        # Exogenous Variables
        self.exogenouses:Dict[str,str] = {}

    '''
    EXPLANATION GRAPH
    '''
    def create_graph_from_bt(
            self,
            nodes:Dict[str,ExplanationModelNode],
            executions:dict[str,str],
            returns:dict[str,str],
        ) -> nx.DiGraph:
        graph = super().create_graph_from_bt(nodes,executions,returns)

        # Add exogenous nodes for each stochastic BT node
        for btnode_id in self.em.btnodes:
            btnode:MemoryNode = self.em.btnodes[btnode_id]

            # Check if BT node is stochasic
            if not self.tm.deterministic_bt_node(btnode.behaviour_name):
                # Create node
                exogenous_node = ProbabilisticExplanationModelNode.node_from_bt(btnode,EXOGENOUS_CATEGORY)
                nodes[exogenous_node.id] = exogenous_node
                self.exogenouses[btnode_id] = exogenous_node.id
                graph.add_node(exogenous_node.id)

                # Add edge
                graph.add_edge(exogenous_node.id,returns[btnode.id])

        return graph


    def add_states_to_graph(
            self,
            graph:nx.DiGraph,
            nodes:Dict[str,ExplanationModelNode],
            executions:dict[str,str],
            returns:dict[str,str],
            temporal_state_vars:dict[str,list],
            state_var_names:dict[str,str]
        ) -> nx.DiGraph:
        explanation_graph = super().add_states_to_graph(graph,nodes,executions,returns,temporal_state_vars,state_var_names)

        _,env_outputs = self.calculate_environment_inputs_outputs()

        # Link exogenous nodes to output state variables for BT nodes
        for btnode_id in self.exogenouses:
            behaviour:LeafNode = self.em.btnodes[btnode_id].behaviour
            output_vars = behaviour.output_variables() + env_outputs[btnode_id]

            for output_var in output_vars:
                temporal_output_var = temporal_state_vars[output_var][self.btnode_times[btnode_id]+1]
                explanation_graph.add_edge(self.exogenouses[btnode_id],temporal_output_var)

        # TODO - what about new exogenous variables for inherently stochastic state variables?

        return explanation_graph

    '''
    VARIABLE RANGES
    '''
    def calculate_ranges(self) -> Dict[str,VarRange]:
        ranges = super().calculate_ranges()

        # Calculate ranges for exogenous variables
        for btnode_id in self.exogenouses:
            exogenous_node:ExplanationModelNode = self.nodes[self.exogenouses[btnode_id]]
            ranges[exogenous_node.id] = NormalisedFloatRange()

        return ranges


    '''
    CAUSAL MODELS
    '''
    def can_intervene(self,node:str) -> bool:
        if self.nodes[node].category == EXOGENOUS_CATEGORY:
            # Cannot intervene on exogenous variables, they are initialised differently (i.e. during Monte Carlo search)
            return False
        else:
            return super().can_intervene(node)

    def build_execution_node(self,xnode:ExplanationModelNode) -> ProbabilisticCausalNode:
        def func(state: State, model_state: dict) -> bool:
            return self.execution_function(node_id=xnode.id,explanation_model_vals=model_state)
        
        return ProbabilisticCausalNode(
            name=xnode.id,
            values=self.var_ranges[xnode.id].values,
            value=None,
            func=func,
            category=EXECUTION_CATEGORY,
        )

    
    def build_return_node(self, xnode:ExplanationModelNode) -> ProbabilisticCausalNode:
        # Probabilistic
        node_name = self.em.btnodes[xnode.btnode_id].behaviour_name
        if not self.tm.deterministic_bt_node(node_name):
            # Node is probabilistic
            return_var = self.returns[xnode.btnode_id]
            parent_cats = [self.nodes[parent].category for parent in self.parents[return_var]]
            exogenous_parent = self.parents[return_var][parent_cats.index(EXOGENOUS_CATEGORY)]
            execution_parent = self.parents[xnode.id][parent_cats.index(EXECUTION_CATEGORY)]

            deterministic = False 
            node_func = self.tm.stochastic_bt_node_return_func(
                bt_node=self.em.btnodes[xnode.btnode_id].behaviour_name,
                bt_node_return_var=return_var,
                execution_variable=execution_parent,
                exogenous_variable=exogenous_parent
            )
        else:
            # Node is deterministic

            def deterministic_func(state: State, model_state: dict) -> py_trees.common.Status:
                return self.return_function(xnode.id, model_state, state)

            deterministic = True
            node_func = deterministic_func

        return ProbabilisticCausalNode(
            name=xnode.id,
            values=self.var_ranges[xnode.id].values,
            value=None,
            func=node_func,
            category=RETURN_CATEGORY,
            deterministic=deterministic,
        )

    def build_state_var_node(self, xnode:ExplanationModelNode) -> ProbabilisticCausalNode:
        deterministic_state_var = self.tm.determinstic_state_variable(xnode.name)
        state_var_name = self.state_var_names[xnode.name]

        # Get parent categories
        parent_cats = [self.nodes[parent].category for parent in self.parents[xnode.name]]

        if EXECUTION_CATEGORY in parent_cats:
            # The value of the variable depends on a BT node function
            execution_parent = self.parents[xnode.name][parent_cats.index(EXECUTION_CATEGORY)]
            btnode:LeafNode = self.em.btnodes[self.nodes[execution_parent].btnode_id].behaviour
            
            def func(state: State, model_state: dict):
                # Execute the BT
                btnode.execute(state)
                # Extract the variable
                state_var = self.state_var_names[xnode.name]
                return state.get_value(state_var)

            parent_node_name = self.em.btnodes[self.nodes[execution_parent].btnode_id].behaviour_name
            deterministic_parent = self.tm.deterministic_bt_node(parent_node_name)

            if deterministic_parent and deterministic_state_var:
                # Node is deterministic
                deterministic = True
                node_func = func
            else:
                # Node is probabilistic
                deterministic = False
                exogenous_parent = self.parents[xnode.name][parent_cats.index(EXOGENOUS_CATEGORY)]

                parent_state_var_names = [self.state_var_names[pnode] for pnode in self.parents[xnode.name] if pnode in self.state_var_names]

                node_func = self.tm.stochastic_state_var_func(
                    state_variable=state_var_name,
                    state_variable_id=xnode.id,
                    exogenous_variable=exogenous_parent,
                    bt_node=parent_node_name,
                    bt_node_execution_var=execution_parent,
                    bt_node_inputs=parent_state_var_names,
                )
        else:
            # The value of the variable depends entirely on the state
            func=self.tm.function_dict[self.state_var_names[xnode.id]]

            if deterministic_state_var:
                # Node is deterministic
                deterministic = True
                node_func = func
            else:
                # Node is probabilistic
                deterministic = False
                node_func = self.tm.stochastic_state_var_func(
                    state_variable=state_var_name,
                    state_variable_id=xnode.id,
                    exogenous_variable=exogenous_parent
                )


        return ProbabilisticCausalNode(
            name=xnode.name,
            values=self.var_ranges[xnode.id].values,
            value=None,
            func=node_func,
            category=STATE_CATEGORY,
            deterministic=deterministic,
        )

    def build_exogenous_node(self, xnode:ExplanationModelNode) -> ProbabilisticCausalNode:
        def func(seed: int) -> bool:
            hash_bytes = hashlib.sha256(f"{seed}-{xnode.id}".encode("utf-8")).digest()
            combined_seed = int.from_bytes(hash_bytes,byteorder="big")
            rng = random.Random(combined_seed)
            return rng.random()
        
        return ProbabilisticCausalNode(
            name=xnode.id,
            values=self.var_ranges[xnode.id].values,
            value=None,
            func=func,
            category=EXOGENOUS_CATEGORY,
            deterministic=False,
        )

    def create_causal_model(self) -> ProbabilisticCausalModel:
        cm = ProbabilisticCausalModel(self.tm,self.ros_node)

        # Add nodes
        for node in self.explanation_nodes_ordered:
            xnode = self.nodes[node]
            if xnode.category == EXECUTION_CATEGORY:
                cnode = self.build_execution_node(xnode)
            elif xnode.category == RETURN_CATEGORY:
                cnode = self.build_return_node(xnode)
            elif xnode.category == STATE_CATEGORY:
                cnode = self.build_state_var_node(xnode)
            elif xnode.category == EXOGENOUS_CATEGORY:
                cnode = self.build_exogenous_node(xnode)
            else:
                # Oops, shouldn't be here
                raise ValueError(f"Unrecognised node category {xnode.category}")
            
            cm.add_node(cnode)

        # Add edges
        cm.add_edges(self.explanation_graph.edges)

        return cm

    '''
    LOADING
    '''
    '''
    #NOTE: Commenting out to remove modelstatevalue, likely will delete
    def model_state_at_timestep(self, timestep_tick = None, timestep_time = None):
        model_state = super().model_state_at_timestep(timestep_tick, timestep_time)
        for var in model_state:
            model_state[var] = ModelStateValue(model_state[var])
        return model_state
    '''