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
    ):
        super().__init__(name, values, value, func, category)

        self.deterministic = deterministic

class ProbabilisticCausalModel(CausalModel):
    def __init__(self, state_model, ros_node = None):
        super().__init__(state_model, ros_node)

        




    