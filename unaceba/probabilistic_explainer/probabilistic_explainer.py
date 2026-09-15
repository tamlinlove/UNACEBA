from unaceba.explainer.explainer import Explainer
from unaceba.probabilistic_explainer.probabilistic_explanation_model import ProbabilisticExplanationModel
from unaceba.probabilistic_explainer.probabilistic_query import ProbabilisticQuery
from unaceba.probabilistic_explainer.probabilistic_explanation import ProbabilisticCounterfactualExplanation

import networkx as nx

from typing import List

class ProbabilisticExplainer(Explainer):
    def __init__(self,explanation_model:ProbabilisticExplanationModel):
        self.explanation_model = explanation_model

    '''
    EXPLAIN
    '''
    def explain(self, query, max_depth = 1, samples = 10, **kwargs):
        super().explain(query,max_depth=max_depth,samples=samples, **kwargs)

    def explain_to_depth(
            self,
            query:ProbabilisticQuery,
            search_space:dict[str,list],
            search_graph:nx.DiGraph,
            depth:int=1,
            samples:int=10,
            **kwargs
    ) -> List[ProbabilisticCounterfactualExplanation]:
        pass

        