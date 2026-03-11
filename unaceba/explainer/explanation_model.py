from unaceba.explainer.episodic_memory import EpisodicMemory
from unaceba.explainer.task_model import TaskModel

class ExplanationModel:
    def __init__(
            self,
            episodic_memory:EpisodicMemory,
            task_model:TaskModel
    ):
        '''
        Creates the explanation model combining BT structure and the task model
        '''
        self.em = episodic_memory
        self.tm = task_model