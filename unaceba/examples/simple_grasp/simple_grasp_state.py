from unaceba.task.state import State
from unaceba.utils.variables import CategoricalRange,ContinuousRange,BooleanRange,AnyRange,NormalisedFloatRange

class SimpleGraspState(State):
    '''
    Class representing the state of the simple grasp environment
    '''
    def __init__(self,values:dict=None):
        '''
        Construct a new SimpleGraspState

        Parameters
        --------------
        values : dict (default: None)
            a dict of initial values to populate the state with, or None
        '''
        # Define state
        state_vars = [
            # Environment Properties
            "grasp_instruction",
            "target_object",
            "target_object_confidence",
            "object_distance",
            # Task Properties
            "grasp_strategy",
            "grasp_succeeded",
        ]

        var_ranges = {
            # Environment Properties
            "grasp_instruction":AnyRange(var_type=str,allow_none=True),
            "target_object":CategoricalRange(values=["cup","bottle","sunglasses"]),
            "target_object_confidence":NormalisedFloatRange(allow_none=True),
            "object_distance":ContinuousRange(min=0,max=3),
            # Task Properties
            "grasp_strategy":CategoricalRange(values=["close","general"],allow_none=True),
            "grasp_succeeded":BooleanRange(allow_none=True),
        }

        semantic_dict = {
            # Environment Properties
            "grasp_instruction":"The instruction given by the user indicating the object they want grasped",
            "target_object":"The object the robot believes the user wants",
            "target_object_confidence":"The confidence the robot has in their belief over the target object",
            "object_distance":"The distance between the robot and the object",
            # Task Properties
            "grasp_strategy":"The selected grasp startegy used to grasp the object",
            "grasp_succeeded":"Whether or not the grasp was successful",
        }

        super().__init__(
            state_vars=state_vars,
            var_ranges=var_ranges,
            semantic_dict=semantic_dict,
            values=values
        )