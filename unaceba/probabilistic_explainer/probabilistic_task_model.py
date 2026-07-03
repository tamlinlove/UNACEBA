from unaceba.explainer.task_model import TaskModel
import numpy as np

class ProbabilisticTaskModel(TaskModel):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

    '''
    PROBABILISTIC ELEMENTS
    '''
    def determinstic_state_variable(self,state_variable:str) -> bool:
        '''
        Returns True if a state variable is deterministic (conditioned on only state variables), false otherwise
        '''
        raise NotImplementedError
    
    def deterministic_bt_node(self,bt_node:str) -> bool:
        '''
        Returns True if the return function or the values of output variables of a bt leaf node are stochastic in any way
        '''
        raise NotImplementedError
    
    def stochastic_state_variable_cpd(self,state_variable:str,bt_node:str=None) -> np.ndarray:
        '''
        Given a state variable and, optionally, a parent BT node, return the CPD for that variable

        Case 1: bt_node = None, state variable value is conditioned only on other state variables
        Case 2: bt_node is not None, state variable value is also conditioned on the execution of the bt_node
        '''
        raise NotImplementedError
    
    def stochastic_bt_node_return_cpd(self,bt_node:str) -> np.ndarray:
        '''
        Given a BT node name, return the CPD for the return function of that node
        '''
        raise NotImplementedError
