from unaceba.probabilistic_explainer.probabilistic_task_model import ProbabilisticTaskModel
from unaceba.examples.simple_grasp.simple_grasp_state import SimpleGraspState
from unaceba.examples.simple_grasp.simple_grasp_environment import SimpleGraspEnvironment,GRASP_SUCCESS_PROBS
from unaceba.utils.variables import VarRange,CategoricalRange,ContinuousRange,DiscretisedRange

from pgmpy.factors.discrete.CPD import TabularCPD

from typing import Dict,List

import copy

class SimpleGraspTaskModel(ProbabilisticTaskModel):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

        dummy_state = SimpleGraspState()
        self.state_only_variables = dummy_state.state_vars
        self.state_only_ranges = dummy_state.var_ranges
        self.state_only_semantic_dict = dummy_state.semantic_dict

        # Model Variables
        self.model_only_variables = [
            "binary_object_distance",
            "object_distance_threshold"
        ]

        self.model_var_ranges = {
            "binary_object_distance":CategoricalRange(values=["close","far"]),
            "object_distance_threshold":DiscretisedRange(min=0,max=3,size=self.discretisation_size)
        }

        self.model_semantic_dict = {
            "binary_object_distance":"The binary classification of target object distance as either close or far, determined by a threshold.",
            "object_distance_threshold":"The threshold used to determine the binary distance classification of objects",
        }

    '''
    Task model definitions
    '''

    def cm_edges(self) -> list[tuple[str,str]]:
        '''
        Return a list of edges representing the assumptions of a causal model modelling this state
        All strings in these edges represent state/model variables
        '''
        return [
            ("object_distance","binary_object_distance"),
            ("object_distance_threshold","binary_object_distance")
        ]
    
    def environment_inputs(self) -> list[tuple[str,str]]:
        '''
        Returns a list of edges representing the impact of state/model variables on BT node return statuses through environment dynamics 
        Var1 in each edge is a state variable, Var2 is a BT node name
        '''
        return [
            ("grasp_succeeded","Handover"),
            ("binary_object_distance","Grasp"),
            ("grasp_strategy","Grasp"),
            ("target_object","Grasp"),
        ]
    
    def environment_outputs(self) -> Dict[str,List[str]]:
        '''
        Returns a list of edges representing the impact of BT node execution on state variables through environment dynamics 
        Var1 in each edge is a BT node name, Var2 is a state/model variable
        '''
        return []
    
    def can_intervene(self,node:str):
        '''
        Given the name of the node, return True if a causal model is allowed to intervene on its value
        '''
        if node in ["grasp_instruction","object_distance_threshold"]:
            return False
        return True
    
    '''
    FUNCTIONS
    '''
    @staticmethod
    def calculate_binary_object_distance(state:SimpleGraspState) -> str:
        distance = state.get_value("object_distance")
        threshold = state.get_value("object_distance_threshold")

        if distance <= threshold:
            return "close"
        return "far"
    
    @staticmethod
    def calculate_object_distance_threshold(state:SimpleGraspState) -> float:
        # For now, this just returns a constant value
        return SimpleGraspEnvironment.distance_threshold


    def var_funcs(self) -> dict:
        '''
        Return a mapping from each variable in the state to a function used to compute that variable's value
        '''
        func_dict = {
            key: (lambda key: lambda state: state.get_value(key))(key)
            for key in self.state_vars()
        }

        func_dict["binary_object_distance"] = self.calculate_binary_object_distance

        return func_dict
    
    def calculate_model_var_values(self,state:SimpleGraspState):
        '''
        Given a state, calculate the values of the model variables defined by the task model
        '''
        distance_threshold = self.calculate_object_distance_threshold(state)
        state.inject_variable(
            "object_distance_threshold",
            self.model_var_ranges["object_distance_threshold"],
            self.model_semantic_dict["object_distance_threshold"],
            value=distance_threshold
        )
        binary_object_distance = self.calculate_binary_object_distance(state)

        return {
            "object_distance_threshold": distance_threshold,
            "binary_object_distance": binary_object_distance,
        }
    

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

        This can be done by inserting an extra variable s.t. Distance > Discrete Distance > Success
        Requires explicitly defining variables which cannot be read from the episodic memory but instead inferred from known observations
        '''
        grasp_cpd = TabularCPD(
            "grasp_success",
            2,
            GRASP_SUCCESS_PROBS,
            evidence=["binary_object_distance","grasp_strategy","target_object"],
            evidence_card=[2,2,3],
            state_names={
                "grasp_success":["success","failure"],
                "binary_object_distance":["close","far"],
                "grasp":self.state_only_ranges["grasp_strategy"].values,
                "object":self.state_only_ranges["target_object"].values,
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
    
    def state_vars(self):
        return self.state_only_variables + self.model_only_variables
    
    