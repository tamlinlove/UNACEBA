import py_trees

from unaceba.task.task import Task

from unaceba.examples.simple_grasp.simple_grasp_bt import simple_grasp_tree
from unaceba.examples.simple_grasp.simple_grasp_environment import SimpleGraspEnvironment
from unaceba.examples.simple_grasp.simple_grasp_state import SimpleGraspState

class SimpleGraspTask(Task):
    def __init__(self,log_dir:str,log_file:str, **kwargs):
        super().__init__(log_dir,log_file,**kwargs)

    '''
    TASK SETUP
    '''
    def setup_state(self,**kwargs) -> SimpleGraspState:
        return SimpleGraspState(values=SimpleGraspEnvironment.get_default_state())
    
    def setup_environment(self,seed:int=0,**kwargs) -> SimpleGraspEnvironment:
        return SimpleGraspEnvironment(seed=seed)
    
    def setup_tree(self,**kwargs) -> py_trees.trees.BehaviourTree:
        return py_trees.trees.BehaviourTree(root=simple_grasp_tree())
    
    '''
    TASK SPECIFIC
    '''
    def set_instruction(self,instruction:str):
        self.set_state("grasp_instruction",instruction)