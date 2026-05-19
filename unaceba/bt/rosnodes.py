import rclpy
import rclpy.node
import py_trees
from typing import List

from unaceba.bt.nodes import LeafNode

class RosLeafNode(LeafNode):
    """
    Subclass of LeafNode that provides ROS2 integration.
    Each instance shares a single rclpy Node, injected at setup().
    """

    def __init__(self, name: str):
        super().__init__(name)
        self._ros_node: rclpy.node.Node = None  # injected later

    def set_ros_node(self, node: rclpy.node.Node) -> None:
        """
        Call this before the tree is setup()-ed to inject the shared ROS node.
        Typically called by your BT runner after rclpy.init().
        """
        self._ros_node = node

    def setup(self) -> None:
        """
        Called once before ticking begins.
        Subclasses should override this to create subscribers, 
        publishers, action clients, etc. using self._ros_node.
        """
        if self._ros_node is None:
            raise RuntimeError(
                f"[{self.name}] ROS node not injected. "
                "Call set_ros_node() before setup()."
            )
        self.ros_setup()

    def ros_setup(self) -> None:
        """
        Override this instead of setup() in concrete nodes.
        self._ros_node is guaranteed to be available here.
        """
        pass
    
class RosActionNode(RosLeafNode):
    def __init__(self, name: str):
        super().__init__(name)
        self.node_type = "Action"

class RosConditionNode(RosLeafNode):
    def __init__(self, name: str):
        super().__init__(name)
        self.node_type = "Condition"