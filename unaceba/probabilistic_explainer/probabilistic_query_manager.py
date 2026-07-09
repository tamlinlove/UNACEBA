from unaceba.explainer.query_manager import QueryManager
from unaceba.probabilistic_explainer.probabilistic_query import ProbabilisticQuery

class ProbabilisticQueryManager(QueryManager):
    def __init__(self, explainer, ros_node = None):
        super().__init__(explainer, ros_node)
        self.query_class = ProbabilisticQuery

    