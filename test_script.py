from unaceba.examples.simple_grasp.simple_grasp_task import SimpleGraspTask

task = SimpleGraspTask(seed=10)
task.set_instruction("Fetch me a cup")
task.run()