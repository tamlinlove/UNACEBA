from unaceba.task.state import State

from typing import Dict,List

class TaskModel:
    def __init__(self):
        pass

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
    
    def can_intervene(self,node:str):
        '''
        Given the name of the node, return True if a causal model is allowed to intervene on its value
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