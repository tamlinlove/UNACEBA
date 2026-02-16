from unaceba.examples.simple_grasp.simple_grasp_state import SimpleGraspState
from unaceba.examples.simple_grasp.simple_grasp_environment import SimpleGraspEnvironment

state = SimpleGraspState(SimpleGraspEnvironment.get_default_state())
env = SimpleGraspEnvironment()
state.set_value("grasp_strategy","close")

success_sum = 0
for i in range(100000):
    success = env.execute_grasp(state)
    if success:
        success_sum += 1
print(success_sum)
