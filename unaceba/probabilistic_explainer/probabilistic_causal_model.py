from unaceba.explainer.causal_model import CausalModel

class ProbabilisticCausalModel(CausalModel):
    def __init__(self, state_model, ros_node = None):
        # TODO
        super().__init__(state_model, ros_node)