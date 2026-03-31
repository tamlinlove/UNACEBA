from unaceba.task.environment import Environment
from unaceba.examples.simple_grasp.simple_grasp_state import SimpleGraspState

from pgmpy.factors.discrete.CPD import TabularCPD

import numpy as np

MAX_SEED = 1000000000

DEFAULT_STATE = {
    # Environment Properties
    "grasp_instruction":None,
    "target_object":"bottle",
    "target_object_confidence":None,
    "object_distance":2.4,
    # Task Properties
    "grasp_strategy":None,
    "grasp_succeeded":None,
}

# distance (close-far), grasp (close-general), object (cup-bottle-sunglasses)
GRASP_SUCCESS_PROBS = [
    [0.8,0.9,0.65,0.65,0.8,0.6,0.3,0.4,0.15,0.65,0.8,0.6],
    [0.2,0.1,0.35,0.35,0.2,0.4,0.7,0.6,0.85,0.35,0.2,0.4]
]

class SimpleGraspEnvironment(Environment):
    distance_threshold = 1

    def __init__(self,seed:int=0):
        super().__init__()
        self.seed = seed

    @staticmethod
    def get_default_state() -> dict:
        return DEFAULT_STATE
    
    def robot_speak(self,text:str):
        print(f"ROBOT SAYS: {text}")

    def execute_handover(self,state:SimpleGraspState) -> bool:
        text = f"Here is your item - {state.get_value("target_object")}"
        self.robot_speak(text)

        if state.get_value("grasp_succeeded"):
            return True
        return False

    def execute_apologise(self,state:SimpleGraspState) -> bool:
        text = f"Sorry, I couldn't bring your {state.get_value("target_object")}"
        self.robot_speak(text)

        return True

    def execute_grasp(self,state:SimpleGraspState) -> bool:
        simple_distance = "close" if state.get_value("object_distance") <= self.distance_threshold else "far"
        grasp = state.get_value("grasp_strategy")
        target_object = state.get_value("target_object")

        # TODO: pgmpy is not very efficient. If we can do without it, do it
        grasp_success_cpd = TabularCPD(
            "grasp_success",
            2,
            GRASP_SUCCESS_PROBS,
            evidence=["distance","grasp","object"],
            evidence_card=[2,2,3],
            state_names={
                "grasp_success":["success","failure"],
                "distance":["close","far"],
                "grasp":state.var_ranges["grasp_strategy"].values,
                "object":state.var_ranges["target_object"].values,
            }
        )

        p_success = grasp_success_cpd.get_value(
            grasp_success="success",
            distance=simple_distance,
            grasp=grasp,
            object=target_object
        )
        p_failure = 1 - p_success
        
        # Random Process
        rng = np.random.default_rng(self.seed)
        grasp_success = rng.choice([True,False],p=[p_success,p_failure])
        self.update_seed(rng)

        return grasp_success
    
    def update_seed(self,rng:np.random._generator.Generator):
        self.seed = rng.integers(0,MAX_SEED)

