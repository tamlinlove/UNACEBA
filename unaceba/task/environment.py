from rclpy.node import Node

class Environment:
    '''
    Abstract interface for task environments
    '''
    def __init__(self):
        pass

    def inject_ros_node(self,ros_node:Node):
        self.ros_node = ros_node

    def log(self,text:str):
        self.ros_node.get_logger().info(text)