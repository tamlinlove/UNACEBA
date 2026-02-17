from unaceba.explainer.state_model import StateModel
from unaceba.examples.simple_grasp.simple_grasp_state import SimpleGraspState

from typing import Dict,List

import copy

class SimpleGraspStateModel(StateModel):
    def __init__(self):
        super().__init__()

    '''
    State model definitions
    '''
    def cm_edges(self) -> list[tuple[str,str]]:
        '''
        Return a list of edges representing the assumptions of a causal model modelling this state
        All strings in these edges represent state variables
        '''
        return []
    
    def environment_inputs(self) -> list[tuple[str,str]]:
        '''
        Returns a list of edges representing the impact of state variables on BT node return statuses through environment dynamics 
        Var1 in each edge is a state variable, Var2 is a BT node name
        '''
        return [
            ("grasp_succeeded","Handover"),
            ("object_distance","Grasp"),
            ("grasp_strategy","Grasp"),
            ("target_object","Grasp"),
        ]
    
    def environment_outputs(self) -> Dict[str,List[str]]:
        '''
        Returns a dict mapping the names of BT nodes to lists of variables that they indirectly impact through environment actions 
        '''
        return {}
    

    def var_funcs(self) -> dict:
        '''
        Return a mapping from each variable in the state to a function used to compute that variable's value
        '''
        func_dict = {
            key: (lambda key: lambda state: state.get_value(key))(key)
            for key in SimpleGraspState.get_ranges().keys()
        }

        return func_dict
    
    def can_intervene(self,node:str):
        '''
        Given the name of the node, return True if a causal model is allowed to intervene on its value
        '''
        if node in ["grasp_instruction"]:
            return False
        return True
    
    '''
    UTILITY
    '''
    def copy_state(self,state:SimpleGraspState):
        '''
        Create a new instance of the state with the same values
        '''
        return SimpleGraspState(values=copy.deepcopy(state.values))