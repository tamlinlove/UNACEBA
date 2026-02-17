import py_trees
from typing import List

from unaceba.task.state import State
from unaceba.bt.log_node import LogNode

class LeafNode(py_trees.behaviour.Behaviour):
    '''
    Class for leaf nodes in a BT
    '''
    def __init__(self, name: str):
        super().__init__(name)

        # Blackboard
        self.board = self.attach_blackboard_client(name=f"{name}_board")
        self.board.register_key("state", access=py_trees.common.Access.READ)

        # Logging
        self.lognode:LogNode = None

    '''
    EMPTY BOILERPLATE FUNCTIONS
    '''

    def setup(self) -> None:
        pass

    def initialise(self) -> None:
        pass

    def terminate(self, new_status) -> None:
        pass

    '''
    DEFINE VARIABLE SETS
    '''
    def input_variables(self) -> List[str]:
        '''
        This function returns a list of State variables (strings as keys) that are used as input by the node
        '''
        raise NotImplementedError
    
    def output_variables(self) -> List[str]:
        '''
        This function returns a list of State variables (strings as keys) that have their value changed by the node
        '''
        raise NotImplementedError
    
    '''
    BT NODE FUNCTIONALITY
    '''
    def execute(self,state:State) -> py_trees.common.Status:
        '''
        This function should execute the logic of the BT node in the environment and return a pytrees status
        '''
        raise NotImplementedError
    
    def update(self) -> py_trees.common.Status:
        '''
        This function executes when the node is ticked. 
        It calls the execute() function after getting the state, and handles some logging. 
        '''
        state = self.board.state

        # Logging
        # TODO
        
        return self.execute(state)
    
    '''
    LOGGING
    '''
    def add_log_node(self,lognode:LogNode):
        self.lognode = lognode
    
    '''
    SEMANTIC DESCRIPTION
    '''
    def semantic_description(self) -> str:
        return "A leaf node in a behaviour tree."
    
class ActionNode(LeafNode):
    def __init__(self, name: str):
        super().__init__(name)
        self.node_type = "Action"

class ConditionNode(LeafNode):
    def __init__(self, name: str):
        super().__init__(name)
        self.node_type = "Condition"