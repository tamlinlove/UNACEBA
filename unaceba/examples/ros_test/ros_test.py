import time
import py_trees
from std_msgs.msg import String
from typing import List
from unaceba.task.environment import Environment
from unaceba.bt.rosnodes import RosActionNode, RosConditionNode
from unaceba.task.task import Task
from unaceba.task.state import State

class RosTestEnvironment(Environment):
    def __init__(self):
        super().__init__()
        
class RosTestAction1(RosActionNode):
    """
    Publishes a message to /test_topic and simulates work by sleeping.
    Runs for a fixed number of ticks before succeeding.
    """

    TICKS_TO_COMPLETE = 5  # simulate ~0.5s of "work" at 10Hz

    def __init__(self):
        super().__init__("RosTestAction1")
        self._publisher = None
        self._tick_count = 0

    def input_variables(self) -> List[str]:
        return []

    def output_variables(self) -> List[str]:
        return []

    def ros_setup(self) -> None:
        self._publisher = self._ros_node.create_publisher(
            String,
            "/test_topic",
            10
        )

    def initialise(self) -> None:
        """Reset tick counter each time the node is entered."""
        self._tick_count = 0
        self._ros_node.get_logger().info(f"[{self.name}] Starting action...")

    def execute(self, state) -> py_trees.common.Status:
        self._tick_count += 1

        # Simulate work with a short sleep (non-blocking feel in BT context)
        time.sleep(0.05)

        msg = String()
        msg.data = f"[{self.name}] tick {self._tick_count}/{self.TICKS_TO_COMPLETE}"
        self._publisher.publish(msg)
        self._ros_node.get_logger().info(f"Published: {msg.data}")

        if self._tick_count >= self.TICKS_TO_COMPLETE:
            self._ros_node.get_logger().info(f"[{self.name}] Action complete.")
            return py_trees.common.Status.SUCCESS

        return py_trees.common.Status.RUNNING


class RosTestAction2(RosActionNode):
    """
    Publishes a different message to the same /test_topic.
    Simulates a longer task and can fail if a condition is unmet.
    """

    TICKS_TO_COMPLETE = 8

    def __init__(self):
        super().__init__("RosTestAction2")
        self._publisher = None
        self._tick_count = 0

    def input_variables(self) -> List[str]:
        return []  # could read e.g. ["robot_ready"] from state

    def output_variables(self) -> List[str]:
        return []

    def ros_setup(self) -> None:
        # Reuses the same topic — both nodes share the /test_topic channel
        self._publisher = self._ros_node.create_publisher(
            String,
            "/test_topic",
            10
        )

    def initialise(self) -> None:
        self._tick_count = 0
        self._ros_node.get_logger().info(f"[{self.name}] Starting action...")

    def execute(self, state) -> py_trees.common.Status:
        self._tick_count += 1

        # Slightly longer simulated work
        time.sleep(0.1)

        msg = String()
        msg.data = f"[{self.name}] step {self._tick_count}/{self.TICKS_TO_COMPLETE}"
        self._publisher.publish(msg)
        self._ros_node.get_logger().info(f"Published: {msg.data}")

        if self._tick_count >= self.TICKS_TO_COMPLETE:
            self._ros_node.get_logger().info(f"[{self.name}] Action complete.")
            return py_trees.common.Status.SUCCESS

        return py_trees.common.Status.RUNNING
    
def ros_test_tree():
    test_sequence = py_trees.composites.Sequence(
        name = "RosTestSequence",
        memory = False,
        children = [
            RosTestAction1(),
            RosTestAction2()
        ]
    )
    
    return test_sequence

class RosTestTask(Task):
    def __init__(self, log_dir, log_file, **kwargs):
        super().__init__(log_dir, log_file, **kwargs)
        
    '''
    TASK SETUP
    '''
    def setup_state(self,**kwargs) -> State:
        return State(state_vars=[],var_ranges={},semantic_dict={})
    
    def setup_environment(self,seed:int=0,**kwargs):
        return None
    
    def setup_tree(self,**kwargs) -> py_trees.trees.BehaviourTree:
        return py_trees.trees.BehaviourTree(root=ros_test_tree())


        
    
        
