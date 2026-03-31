import py_trees

from unaceba.task.task import Task

from unaceba.examples.simple_grasp.simple_grasp_bt import simple_grasp_tree
from unaceba.examples.simple_grasp.simple_grasp_environment import SimpleGraspEnvironment
from unaceba.examples.simple_grasp.simple_grasp_state import SimpleGraspState

class SimpleGraspTask(Task):
    def __init__(self,log_dir:str,log_file:str,instruction:str,**kwargs):
        self.grasp_instruction = instruction
        super().__init__(log_dir,log_file,**kwargs)

    '''
    TASK SETUP
    '''
    def setup_state(self,**kwargs) -> SimpleGraspState:
        initial_state = SimpleGraspState(values=SimpleGraspEnvironment.get_default_state())

        # Add instruction
        initial_state.set_value("grasp_instruction",self.grasp_instruction)

        return initial_state
    
    def setup_environment(self,seed:int=0,**kwargs) -> SimpleGraspEnvironment:
        return SimpleGraspEnvironment(seed=seed)
    
    def setup_tree(self,**kwargs) -> py_trees.trees.BehaviourTree:
        return py_trees.trees.BehaviourTree(root=simple_grasp_tree())