import py_trees
from unaceba.bt.nodes import ActionNode,ConditionNode
from unaceba.examples.simple_grasp.simple_grasp_environment import SimpleGraspEnvironment
from unaceba.examples.simple_grasp.simple_grasp_state import SimpleGraspState

'''
LEAF NODES
'''
class DecideObject(ActionNode):
    def __init__(self, name:str = "DecideObject"):
        super(DecideObject, self).__init__(name)

    def execute(self, state:SimpleGraspState):
        # Extract grasp instruction
        instruction = state.get_value("grasp_instruction")

        # NOTE: Dumb method follows for example purposes
        # Check if object occurs in string
        target_object = None
        possible_objects = state.var_ranges["target_object"].values
        for pobj in possible_objects:
            if pobj in instruction:
                target_object = pobj
                confidence = 0.8
                break
        # If not, pick cup
        if target_object is None:
            target_object = "cup"
            confidence = 0.3
        
        # Set state
        state.set_value("target_object",target_object)
        state.set_value("target_object_confidence",confidence)

        return py_trees.common.Status.SUCCESS
    
    def input_variables(self):
        return ["grasp_instruction"]
    
    def output_variables(self):
        return ["target_object","target_object_confidence"]
    
    def semantic_description(self):
        return "Uses the user's instruction to determine the object to grasp, also producing a confidence estimate. Always succeeds."
    
class DecideGrasp(ActionNode):
    def __init__(self, name:str = "DecideGrasp"):
        super(DecideGrasp, self).__init__(name)

    def execute(self, state:SimpleGraspState, distance_threshold:float=1):
        # Extract state info
        object_distance = state.get_value("object_distance")

        if object_distance < distance_threshold:
            grasp = "close"
        else:
            grasp = "general"
        state.set_value("grasp_strategy",grasp)

        return py_trees.common.Status.SUCCESS
    
    def input_variables(self):
        return ["object_distance"]
    
    def output_variables(self):
        return ["grasp_strategy"]
    
    def semantic_description(self):
        return "Using the distance to the object, determines an appropriate grasping strategy. Always succeeds."
    
class Grasp(ActionNode):
    def __init__(self, name:str = "Grasp"):
        super(Grasp, self).__init__(name)

        # Interacts directly with the environment
        self.board.register_key("environment", access=py_trees.common.Access.WRITE)

    def execute(self, state:SimpleGraspState):
        grasp_success = self.board.environment.execute_grasp(state)

        if grasp_success:
            state.set_value("grasp_succeeded",True)
            return py_trees.common.Status.SUCCESS
        state.set_value("grasp_succeeded",False)
        return py_trees.common.Status.FAILURE
    
    def input_variables(self):
        return []
    
    def output_variables(self):
        return ["grasp_succeeded"]
    
    def semantic_description(self):
        return "Executes the grasp. Status depends on the success or failure of the grasp."
    
class Handover(ActionNode):
    def __init__(self, name:str = "Handover"):
        super(Handover, self).__init__(name)

        # Interacts directly with the environment
        self.board.register_key("environment", access=py_trees.common.Access.WRITE)

    def execute(self, state:SimpleGraspState):
        status = self.board.environment.execute_handover(state)
        if status:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE
    
    def input_variables(self):
        return []
    
    def output_variables(self):
        return []
    
    def semantic_description(self):
        return "Executes the object handover. Status depends on the success or failure of the handover."
    
class Apologise(ActionNode):
    def __init__(self, name:str = "Apologise"):
        super(Apologise, self).__init__(name)

        # Interacts directly with the environment
        self.board.register_key("environment", access=py_trees.common.Access.WRITE)

    def execute(self, state:SimpleGraspState):
        self.board.environment.execute_apologise(state)
        return py_trees.common.Status.SUCCESS
    
    def input_variables(self):
        return []
    
    def output_variables(self):
        return []
    
    def semantic_description(self):
        return "Executes the apology skill. Always succeeds."
    
def simple_grasp_tree():
    grasp_sequence = py_trees.composites.Sequence(
        name = "GraspSequence",
        memory = False,
        children = [
            DecideObject(),
            DecideGrasp(),
            Grasp(),
            Handover()
        ]
    )

    grasp_or_apologise_fallback = py_trees.composites.Selector(
        name = "GraspOrApologiseFallback",
        memory = False,
        children = [
            grasp_sequence,
            Apologise()
        ]
    )

    return grasp_or_apologise_fallback
