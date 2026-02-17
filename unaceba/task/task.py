import py_trees
import time

from unaceba.task.state import State
from unaceba.task.environment import Environment
from unaceba.bt.logger import Logger

class Task:
    def __init__(self,log_dir:str,log_file:str,**kwargs):
        # Setup blackboard
        self.board = py_trees.blackboard.Client(name="Board")
        self.board.register_key("state", access=py_trees.common.Access.WRITE)
        self.board.register_key("environment", access=py_trees.common.Access.WRITE)

        # Setup State
        self.state = self.setup_state(**kwargs)
        self.board.state = self.state

        # Setup Environment
        self.environment = self.setup_environment(**kwargs)
        self.board.environment = self.environment

        # Setup Tree
        self.tree = self.setup_tree(**kwargs)

        # Setup Logging
        self.logger = Logger(self.tree,filename=f"{log_dir}/{log_file}")
        self.tree.visitors.append(self.logger)

    '''
    TASK SETUP
    '''
    def setup_state(self,**kwargs) -> State:
        raise NotImplementedError
    
    def setup_environment(self,**kwargs) -> Environment:
        raise NotImplementedError
    
    def setup_tree(self,**kwargs) -> py_trees.trees.BehaviourTree:
        raise NotImplementedError
    
    '''
    STATE MANAGEMENT
    '''
    def set_state(self,var:str,value):
        self.state.set_value(var,value)
    
    '''
    EXECUTION
    '''
    def run(self,display_tree:bool=False):
        self.tree.setup()
        try:
            self.tree.tick()
            time.sleep(0.1)
            if display_tree:
                print(py_trees.display.unicode_tree(self.tree.root, show_status=True))
        except KeyboardInterrupt:
            print("KILL")
            pass