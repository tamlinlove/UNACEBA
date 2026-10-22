import py_trees
import time

import rclpy
from rclpy.node import Node

from unaceba.bt.rosnodes import RosLeafNode
from unaceba.task.state import State
from unaceba.task.environment import Environment
from unaceba.task.task import Task

class RosTask(Task):

    def __init__(
        self,
        log_dir: str,
        log_file: str,
        tick_sleep: float = 0.01,
        **kwargs,
    ):
        super().__init__(log_dir, log_file, **kwargs)

        self.tick_sleep = tick_sleep

    # ------------------------------------------------------------------ #
    #  Task setup                                                        #
    # ------------------------------------------------------------------ #

    def setup_state(self, **kwargs) -> State:
        '''
        Creates a state for the task
        '''
        raise NotImplementedError

    def setup_environment(self, **kwargs) -> Environment:
        raise NotImplementedError

    def setup_tree(self, **kwargs) -> py_trees.trees.BehaviourTree:
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    #  Injected Functions                                                #
    # ------------------------------------------------------------------ #

    def tree_done_condition(self,ros_node: Node) -> bool:
        '''
        Returns true if the BT should finish execution
        '''
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    #  ROS helpers                                                       #
    # ------------------------------------------------------------------ #

    def _iter_ros_leaves(self):
        """Walk the tree and yield every RosLeafNode."""
        for node in self.tree.root.iterate():
            if isinstance(node, RosLeafNode):
                yield node

    def _inject_ros_node(self, ros_node: Node) -> None:
        """Inject the shared ROS node into every RosLeafNode in the tree."""
        for leaf in self._iter_ros_leaves():
            leaf.set_ros_node(ros_node)
        self.environment.inject_ros_node(ros_node)

    def run(
        self,
        display_tree: bool = False,
        loop_until_done: bool = False,
        node_name: str = "bt_runner",
        **kwargs
    ):
        """Tick the behaviour tree until it finishes.

        Args:
            display_tree: If True, print the unicode tree after every tick.
            loop_until_done: If True, the runner keeps ticking even after the
                root reaches SUCCESS/FAILURE — the tree is re-ticked from the
                top on the next iteration. The loop only exits when
                self.state.get_value("sandwich_done") is truthy (or on
                Ctrl-C / rclpy shutdown). If False (default), the runner
                breaks the first time the root reports SUCCESS or FAILURE.
        """
        rclpy.init()
        ros_node = Node(node_name)

        # TODO: Inject a function here for pre-execution stuff?

        ros_node.get_logger().info(f"DISPLAY TREE: {display_tree}")

        try:
            self._inject_ros_node(ros_node)
            self.tree.setup()

            while rclpy.ok():
                rclpy.spin_once(ros_node, timeout_sec=0.0)
                self.tree.tick()
                if display_tree:
                    print(py_trees.display.unicode_tree(
                        self.tree.root, show_status=True))

                # TODO: Inject a function here for per-tick stuff?

                terminal = self.tree.root.status in (
                    py_trees.common.Status.SUCCESS,
                    py_trees.common.Status.FAILURE,
                )

                done = False
                if loop_until_done:
                    done = self.tree_done_condition(ros_node=ros_node)
                    if done:
                        break
                    
                    if terminal:
                        ros_node.get_logger().info(
                            f"Tree reached {self.tree.root.status} but "
                            f"task is not yet finished; continuing."
                        )
                else:
                    if terminal:
                        ros_node.get_logger().info(
                            f"Tree finished with: {self.tree.root.status}"
                        )
                        done = True
                        break

                time.sleep(self.tick_sleep)
            
            # TODO: Post execution injected function?

        except KeyboardInterrupt:
            print("KILL")
        finally:
            ros_node.destroy_node()
            rclpy.shutdown()