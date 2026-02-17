from unaceba.examples.simple_grasp.simple_grasp_task import SimpleGraspTask
from unaceba.explainer.causal_model import CausalModel
from unaceba.examples.simple_grasp.simple_grasp_state_model import SimpleGraspStateModel

seed = 4
task = SimpleGraspTask(log_dir="logs/simple_grasp",log_file=f"run_{seed}",seed=seed)
task.set_instruction("Fetch me a cup")
task.run()

sm = SimpleGraspStateModel()
cm = CausalModel(state_model=sm)