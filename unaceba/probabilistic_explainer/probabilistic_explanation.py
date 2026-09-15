from unaceba.explainer.explanation import CounterfactualExplanation

class ProbabilisticCounterfactualExplanation(CounterfactualExplanation):
    def __init__(self, interventions, foils, model_state, tick = None, time = None):
        # TODO
        super().__init__(interventions, foils, model_state, tick, time)