from unaceba.task.state import State
from unaceba.utils.variables import VarRange

from typing import Dict,List

class TaskModel:
    def __init__(self,discretisation_size=10,**kwargs):
        self.discretisation_size = discretisation_size
        self.state_only_variables = None

        self.model_only_variables:list[str] = []
        self.model_var_ranges:Dict[str,VarRange] = {}
        self.model_semantic_dict:Dict[str,str] = {}

    '''
    Task model definitions
    '''
    def cm_edges(self) -> list[tuple[str,str]]:
        '''
        Return a list of edges representing the assumptions of a causal model modelling this state
        All strings in these edges represent state variables
        '''
        raise NotImplementedError
    
    def environment_inputs(self) -> list[tuple[str,str]]:
        '''
        Returns a list of edges representing the impact of state variables on BT node return statuses through environment dynamics 
        Var1 in each edge is a state variable, Var2 is a BT node name
        '''
        raise NotImplementedError
    
    def environment_outputs(self) -> Dict[str,List[str]]:
        '''
        Returns a dict mapping the names of BT nodes to lists of variables that they indirectly impact through environment actions 
        '''
        raise NotImplementedError
    
    def can_intervene(self,node:str):
        '''
        Given the name of the node, return True if a causal model is allowed to intervene on its value
        '''
        raise NotImplementedError
    
    '''
    RANGES
    '''
    def calculate_state_var_ranges(self) -> Dict[str,VarRange]:
        '''
        Return a dict mapping state variable names to their ranges as VarRange objects, including necessary modelling abstractions such as discretisation
        '''
        raise NotImplementedError


    '''
    FUNCTIONS
    '''

    
    def var_funcs(self) -> dict:
        '''
        Return a mapping from each variable in the state to a function used to compute that variable's value
        '''
        raise NotImplementedError

    def run(self,node:str,state:State):
        '''
        Given the name of the node and a state, run its function and return its new value
        '''
        return self.var_funcs()[node](state)
    
    def calculate_model_var_values(self,state:State):
        '''
        Given a state, calculate the values of the model variables defined by the task model
        '''
        raise NotImplementedError
    
    
    
    '''
    UTILITY
    '''
    def copy_state(self,state:State):
        '''
        Create a new instance of the state with the same values
        '''
        raise NotImplementedError
    
    def state_vars(self):
        '''
        Return a list of all state variables in considered by the task model
        '''
        raise NotImplementedError
    
    def is_model_var(self,variable:str) -> bool:
        return variable in self.model_only_variables