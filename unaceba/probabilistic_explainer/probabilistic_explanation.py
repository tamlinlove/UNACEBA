from typing import List

from unaceba.explainer.explanation import CounterfactualExplanation

class ProbabilisticCounterfactualExplanation(CounterfactualExplanation):
    def __init__(
            self, 
            interventions:dict[str], 
            foils:List[dict[str]], 
            model_state:dict[str], 
            tick:int = None, 
            time:int = None, 
            satisfaction_rate:float = 1.0
        ):
        super().__init__(interventions, foils, model_state, tick, time)

        self.satisfaction_rate = satisfaction_rate