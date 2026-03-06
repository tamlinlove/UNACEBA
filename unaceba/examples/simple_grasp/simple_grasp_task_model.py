from unaceba.explainer.probabilistic_task_model import ProbabilisticTaskModel
from unaceba.examples.simple_grasp.simple_grasp_state import SimpleGraspState
from unaceba.examples.simple_grasp.simple_grasp_environment import GRASP_SUCCESS_PROBS

from pgmpy.factors.discrete.CPD import TabularCPD

from typing import Dict,List

import copy

class SimpleGraspTaskModel(ProbabilisticTaskModel):
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
    PROBABILISTIC ELEMENTS
    '''
    def determinstic_node(self, node):
        if node == "Grasp":
            return False
        return True
    
    def stochastic_cpds(self):
        '''
        TODO: Robustly handle continuous variables in the parents
        '''
        grasp_cpd = TabularCPD(
            "grasp_success",
            2,
            GRASP_SUCCESS_PROBS,
            evidence=["discrete_object_distance","grasp_strategy","target_object"],
            evidence_card=[2,2,3],
            state_names={
                "grasp_success":["success","failure"],
                "discrete_object_distance":["close","far"],
                "grasp":SimpleGraspState.get_ranges()["grasp_strategy"].values,
                "object":SimpleGraspState.get_ranges()["target_object"].values,
            }
        )

        return {
            "return_Grasp":grasp_cpd,
        }

    
    '''
    UTILITY
    '''
    def copy_state(self,state:SimpleGraspState):
        '''
        Create a new instance of the state with the same values
        '''
        return SimpleGraspState(values=copy.deepcopy(state.values))
    