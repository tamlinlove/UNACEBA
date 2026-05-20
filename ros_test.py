from unaceba.example.ros_test.ros_test import RosTestTask

if __name__ == "__main__":
    task = RosTestTask(log_dir="logs/ros_test",log_file="ros_test")
    task.run()