from unaceba.examples.simple_grasp.simple_grasp_task import SimpleGraspTask
from unaceba.explainer.causal_model import CausalModel
from unaceba.explainer.episodic_memory import EpisodicMemory
from unaceba.explainer.explanation_model import ExplanationModel
from unaceba.examples.simple_grasp.simple_grasp_task_model import SimpleGraspTaskModel

seed = 4
task = SimpleGraspTask(log_dir="logs/simple_grasp",log_file=f"run_{seed}",seed=seed)
task.set_instruction("Fetch me a cup")
task.run()

tm = SimpleGraspTaskModel()
em = EpisodicMemory(f"logs/simple_grasp/run_{seed}.json")

exp_model = ExplanationModel(episodic_memory=em,task_model=tm)
exp_model.model_state_at_timestep(timestep_tick=None,timestep_time=None)

