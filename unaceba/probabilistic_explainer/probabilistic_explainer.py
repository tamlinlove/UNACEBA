from unaceba.explainer.explainer import Explainer
from unaceba.probabilistic_explainer.probabilistic_explanation_model import ProbabilisticExplanationModel

class ProbabilisticExplainer(Explainer):
    def __init__(self,explanation_model:ProbabilisticExplanationModel):
        self.explanation_model = explanation_model