from unaceba.explainer.explainer import Explainer
from unaceba.probabilistic_explainer.probabilistic_explanation_model import ProbabilisticExplanationModel

class ProbabilisticExplainer(Explainer):
    def __init__(self,explanation_model:ProbabilisticExplanationModel):
        self.explanation_model = explanation_model

    '''
    EXPLAIN
    '''
    def explain(self, query, max_depth = 1):
        # We begin by reducing the search space to only the ancestors to the node in question
        search_space = self.calculate_search_space(query=query)
        search_graph = self.reduce_graph(query,search_space)