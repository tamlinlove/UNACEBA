import numpy as np
import pyagrum as gum

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
        super().__init__(state_model, ros_node)
        self.bn = gum.BayesNet('ExplanationCausalModel')
        self.node_ids = {}

    '''
    GRAPH OPERATIONS
    '''
    def add_node(self, node):
        super().add_node(node)
        id = self.bn.add(gum.LabelizedVariable(node.name,node.name,len(node.values)))
        self.node_ids[node.name] = id

    def add_edge(self, edge):
        super().add_edge(edge)
        #print(f"Adding arc {edge}")
        #self.bn.addArc(self.node_ids[edge[0]],self.node_ids[edge[1]])
        




    