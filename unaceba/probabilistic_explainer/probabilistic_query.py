from unaceba.explainer.query import Query

class ProbabilisticQuery(Query):
    def __init__(self, foils, explanation_model, model_state):
        # TODO
        super().__init__(foils, explanation_model, model_state)