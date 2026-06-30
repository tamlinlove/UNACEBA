from unaceba.explainer.explanation_model import ExplanationModel,ExplanationModelNode
from unaceba.explainer.explanation import Explanation,CounterfactualExplanation
from unaceba.explainer.query import Query
from unaceba.utils.util import diff_dicts

from typing import List
import networkx as nx
import copy
import itertools

class Explainer:
    def __init__(self,explanation_model:ExplanationModel):
        self.explanation_model = explanation_model

    '''
    EXPLAIN
    '''
    def explain(
            self,
            query:Query,
            max_depth:int=1
    ) -> List[Explanation]:
        # We begin by reducing the search space to only the ancestors to the node in question
        search_space = self.calculate_search_space(query=query)
        search_graph = self.reduce_graph(query,search_space)

        # Calculate depth of explanations
        if max_depth is None:
            max_depth = len(search_space.keys())
        else:
            max_depth = min(max_depth,len(search_space.keys()))

        # Test interventions to generate explanations, starting with one variable at a time
        explanations:List[Explanation] = []
        for d in range(max_depth):
            new_exps = self.explain_to_depth(query,search_space,search_graph,depth=d+1)

            explanations += new_exps

            if len(explanations) > 0:
                break

        return explanations

    def explain_to_depth(
            self,
            query:Query,
            search_space:dict[str,list],
            search_graph:nx.DiGraph,
            depth:int=1
    ) -> List[Explanation]:
        # Determine all possible intervention combinations
        search_combos = self.generate_combinations(search_space,depth)

        explanations:List[Explanation] = []
        for combo in search_combos:

            # Perform intervention
            new_graph,new_model_state = self.explanation_model.intervene(combo,search_graph,query.model_state)
            
            # Check for satisfaction
            if query.satisfies_query(new_model_state):
                counterfactual_foils = {k:new_model_state[k] for k in query.foils}
                explanation = CounterfactualExplanation(combo,counterfactual_foils,query.model_state)
                explanations.append(explanation)

        return explanations

    '''
    SEARCH SPACE
    '''
    def calculate_search_space(self,query:Query) -> dict[str,list]:
        # Get all possible explanation variables:
        ancestors = []
        for qvar in query.foils:
            ancestors += nx.ancestors(self.explanation_model.explanation_graph,qvar)
        ancestors = list(set(ancestors))
        
        # Remove any variables that are marked as un-intervenable
        potential_exp_vars = [anc for anc in ancestors if self.explanation_model.can_intervene(anc)]

        # Calculate search space
        search_space:dict[str,list] = {}
        for xvar in potential_exp_vars:
            xvar_vals = self.explanation_model.var_ranges[xvar].values
            search_space[xvar] = copy.deepcopy(xvar_vals)
        
        # Remove real values from the search space
        for xvar in search_space:
            real_val = query.model_state[xvar]
            if real_val in search_space[xvar]:
                search_space[xvar].remove(real_val)

        return search_space
    
    def reduce_graph(self,query:Query,search_space:dict[str,list]) -> nx.DiGraph:
        allowed_nodes = list(search_space.keys()) + list(query.foil_vars())
        return self.explanation_model.explanation_graph.subgraph(allowed_nodes)
    
    def generate_combinations(self,search_space:dict[str,list], N:int):
        variable_names = list(search_space.keys())
        combinations = []

        # Generate all combinations of N variable names
        for var_combination in itertools.combinations(variable_names, N):
            # Generate all possible value combinations for the selected variables
            value_combinations = itertools.product(*[search_space[var] for var in var_combination])

            # Create a list of dictionaries representing the changes
            for values in value_combinations:
                change = {var: value for var, value in zip(var_combination, values)}
                combinations.append(change)

        return combinations

