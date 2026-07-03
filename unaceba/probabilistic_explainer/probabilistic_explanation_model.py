from unaceba.explainer.explanation_model import ExplanationModel

class ProbabilisticExplanationModel(ExplanationModel):
    def __init__(self, episodic_memory, task_model, probabilistic = True, ros_node = None):
        super().__init__(episodic_memory, task_model, probabilistic, ros_node)

        # TODO: Handle any probabilistic initialisation here
        pass