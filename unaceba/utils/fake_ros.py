from unittest.mock import MagicMock

class FakeFuture:
    """A future that's already 'done' with a canned result."""
    def __init__(self, result=None):
        self._result = result
    def done(self):
        return True
    def result(self):
        return self._result

class FakeLogger:
    def info(self, *a, **k): pass
    def warn(self, *a, **k): pass
    def error(self, *a, **k): pass


class FakeClock:
    def now(self):
        m = MagicMock()
        m.nanoseconds = 0
        return m
    
class FakeRosNode:
    """Stand-in for rclpy.node.Node"""
    def get_logger(self):
        return FakeLogger()
    def get_clock(self):
        return FakeClock()
    def create_publisher(self, *a, **k):
        return MagicMock()  # publish() becomes a no-op
    def create_subscription(self, *a, **k):
        return MagicMock()
    def create_client(self, *a, **k):
        return MagicMock()
