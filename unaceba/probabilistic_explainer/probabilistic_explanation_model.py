import py_trees

from unaceba.task.state import State
from unaceba.bt.nodes import LeafNode
from unaceba.explainer.explanation_model import ExplanationModel,ExplanationModelNode,EXECUTION_CATEGORY,RETURN_CATEGORY,STATE_CATEGORY
from unaceba.probabilistic_explainer.probabilistic_causal_model import ProbabilisticCausalModel,ProbabilisticCausalNode
from unaceba.probabilistic_explainer.probabilistic_task_model import ProbabilisticTaskModel


class ProbabilisticExplanationModel(ExplanationModel):
    def __init__(self, episodic_memory, task_model, probabilistic = True, ros_node = None):
        super().__init__(episodic_memory, task_model, probabilistic, ros_node)

        # Typing
        self.tm:ProbabilisticTaskModel

    '''
    CAUSAL MODELS
    '''


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
        def func(state: State, model_state: dict) -> py_trees.common.Status:
            return self.return_function(xnode.id, model_state, state)
        
        # Probabilistic
        node_name = self.em.btnodes[xnode.btnode_id].behaviour_name
        if not self.tm.deterministic_bt_node(node_name):
            # Node is probabilistic
            deterministic = False
            cpd_values = self.tm.stochastic_bt_node_return_cpd(bt_node=node_name)
        else:
            # Node is deterministic
            deterministic = True
            cpd_values = None

        return ProbabilisticCausalNode(
            name=xnode.id,
            values=self.var_ranges[xnode.id].values,
            value=None,
            func=func,
            category=RETURN_CATEGORY,
            deterministic=deterministic,
            cpd_values=cpd_values
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
                cpd_values = None
            else:
                # Node is probabilistic
                deterministic = False
                cpd_values = self.tm.stochastic_state_variable_cpd(state_var_name,parent_node_name)
        else:
            # The value of the variable depends entirely on the state
            func=self.tm.function_dict[self.state_var_names[xnode.id]]

            if deterministic_state_var:
                # Node is deterministic
                deterministic = True
                cpd_values = None
            else:
                # Node is probabilistic
                deterministic = False
                cpd_values = self.tm.stochastic_state_variable_cpd(state_var_name)


        return ProbabilisticCausalNode(
            name=xnode.name,
            values=self.var_ranges[xnode.id].values,
            value=None,
            func=func,
            category=STATE_CATEGORY,
            deterministic=deterministic,
            cpd_values=cpd_values
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
            else:
                # Oops, shouldn't be here
                raise ValueError(f"Unrecognised node category {xnode.category}")
            
            cm.add_node(cnode)

        # Add edges
        cm.add_edges(self.explanation_graph.edges)

        return cm
