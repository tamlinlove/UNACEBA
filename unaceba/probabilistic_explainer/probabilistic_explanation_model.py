from unaceba.explainer.explanation_model import ExplanationModel,ExplanationModelNode,EXECUTION_CATEGORY,RETURN_CATEGORY,STATE_CATEGORY
from unaceba.probabilistic_explainer.probabilistic_causal_model import ProbabilisticCausalModel,ProbabilisticCausalNode


class ProbabilisticExplanationModel(ExplanationModel):
    def __init__(self, episodic_memory, task_model, probabilistic = True, ros_node = None):
        super().__init__(episodic_memory, task_model, probabilistic, ros_node)

        self.explanation_nodes_ordered = self.calculate_ordering()

    '''
    CAUSAL MODELS
    '''
    def build_execution_node(self,xnode:ExplanationModelNode) -> ProbabilisticCausalNode:
        raise NotImplementedError
    
    def build_return_node(self, xnode:ExplanationModelNode) -> ProbabilisticCausalNode:
        raise NotImplementedError

    def build_state_var_node(self, xnode:ExplanationModelNode) -> ProbabilisticCausalNode:
        raise NotImplementedError

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
