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
        super().__init__(values=values)

    @staticmethod
    def state_vars() -> list[str]:
        '''
        Return a list of state vars

        Output
        --------
        vars : list[str]
            list of state vars
        '''
        return [
            # Environment Properties
            "grasp_instruction",
            "target_object",
            "target_object_confidence",
            "object_distance",
            # Task Properties
            "grasp_strategy",
            "grasp_succeeded",
        ]

    @staticmethod
    def get_ranges():
        '''
        Return a dict mapping every variable name to a VarRange object describing the possible values

        Output
        --------
        range_dict : Dict[str,VarRange]
            dict mapping variable names to VarRange objects describing possible values of each variable
        '''
        return {
            # Environment Properties
            "grasp_instruction":AnyRange(var_type=str,allow_none=True),
            "target_object":CategoricalRange(values=["cup","bottle","sunglasses"]),
            "target_object_confidence":NormalisedFloatRange(allow_none=True),
            "object_distance":ContinuousRange(min=0,max=3),
            # Task Properties
            "grasp_strategy":CategoricalRange(values=["close","general"],allow_none=True),
            "grasp_succeeded":BooleanRange(allow_none=True),
        }

    '''
    SEMANTIC DESCRIPTION
    '''
    def semantic_dict(self) -> dict[str,str]:
        '''
        Output
        --------
        range_dict : dict[str,str]
            dict mapping variable names to descriptions of those variables
        '''
        return {
            # Environment Properties
            "grasp_instruction":"The instruction given by the user indicating the object they want grasped",
            "target_object":"The object the robot believes the user wants",
            "target_object_confidence":"The confidence the robot has in their belief over the target object",
            "object_distance":"The distance between the robot and the object",
            # Task Properties
            "grasp_strategy":"The selected grasp startegy used to grasp the object",
            "grasp_succeeded":"Whether or not the grasp was successful",
        }