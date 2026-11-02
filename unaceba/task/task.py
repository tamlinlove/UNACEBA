import py_trees
import time

from unaceba.task.state import State
from unaceba.task.environment import Environment
from unaceba.bt.logger import Logger


class Task:
    def __init__(self, log_dir: str, log_file: str, disable_logging: bool = False, **kwargs):
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
        if not disable_logging:
            self.logger = Logger(self.tree, filename=f"{log_dir}/{log_file}")
            self.tree.visitors.append(self.logger)

        # Termination bookkeeping (ensures terminate() runs only once)
        self._terminated = False

    """
    TASK SETUP
    """
    def setup_state(self, **kwargs) -> State:
        raise NotImplementedError

    def setup_environment(self, **kwargs) -> Environment:
        raise NotImplementedError

    def setup_tree(self, **kwargs) -> py_trees.trees.BehaviourTree:
        raise NotImplementedError

    """
    STATE MANAGEMENT
    """
    def set_state(self, var: str, value):
        self.state.set_value(var, value)
        self.board.state.set_value(var, value)

    """
    TERMINATION
    """
    def terminate(self, reason: str = "finished"):
        """
        Hook called once when the task ends. Override in subclasses to
        release resources, stop robots, close connections, save results, etc.

        reason: one of "finished" (tree reached a terminal status),
                "interrupted" (user pressed Ctrl+C), or
                "error" (an unexpected exception occurred).
        """
        pass

    def _terminate_once(self, reason: str):
        if self._terminated:
            return
        self._terminated = True
        self.terminate(reason)

    def is_finished(self) -> bool:
        """Return True if the tree root has reached a terminal status."""
        return self.tree.root.status in (
            py_trees.common.Status.SUCCESS,
            py_trees.common.Status.FAILURE,
        )

    """
    EXECUTION
    """
    def run(self, display_tree: bool = False):
        self._terminated = False
        reason = "finished"
        try:
            self.tree.setup()
            self.tree.tick()
            time.sleep(0.1)
            if display_tree:
                print(py_trees.display.unicode_tree(self.tree.root, show_status=True))
        except KeyboardInterrupt:
            print("KILL")
            reason = "interrupted"
        except Exception:
            reason = "error"
            raise
        finally:
            self._terminate_once(reason)