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