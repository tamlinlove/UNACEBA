import numpy as np

from collections.abc import Callable

from unaceba.explainer.causal_model import CausalModel,CausalNode

class ProbabilisticCausalNode(CausalNode):
    def __init__(
            self, 
            name:str, 
            values:list, 
            value, 
            func:Callable, 
            category:str, 
            deterministic:bool=True, 
            cpd_values:np.ndarray|None=None
    ):
        super().__init__(name, values, value, func, category)

        self.deterministic = deterministic
        self.cpd_values = cpd_values

class ProbabilisticCausalModel(CausalModel):
    def __init__(self, state_model, ros_node = None):
        # TODO
        super().__init__(state_model, ros_node)