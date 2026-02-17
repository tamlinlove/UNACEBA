from unaceba.examples.simple_grasp.simple_grasp_task import SimpleGraspTask

seed = 0
task = SimpleGraspTask(log_dir="logs/simple_grasp",log_file=f"run_{seed}",seed=seed)
task.set_instruction("Fetch me a cup")
task.run()