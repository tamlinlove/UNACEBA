from unaceba.explainer.task_model import TaskModel
from pgmpy.factors.discrete.CPD import TabularCPD

class ProbabilisticTaskModel(TaskModel):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

    '''
    PROBABILISTIC ELEMENTS
    '''
    def determinstic_node(self,node:str) -> bool:
        '''
        Returns True if a node is deterministic, false otherwise
        '''
        raise NotImplementedError
    
    def stochastic_cpds(self) -> TabularCPD:
        '''
        Maps every node for which self.deterministic_node(node) is False to a pgmpy TabularCPD
        '''
        raise NotImplementedError
