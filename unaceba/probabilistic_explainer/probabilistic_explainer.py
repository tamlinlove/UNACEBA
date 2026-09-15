from unaceba.explainer.explainer import Explainer
from unaceba.probabilistic_explainer.probabilistic_explanation_model import ProbabilisticExplanationModel
from unaceba.probabilistic_explainer.probabilistic_query import ProbabilisticQuery
from unaceba.probabilistic_explainer.probabilistic_explanation import ProbabilisticCounterfactualExplanation

import networkx as nx
import copy
import random

from typing import List

class ProbabilisticExplainer(Explainer):
    def __init__(self,explanation_model:ProbabilisticExplanationModel,monte_carlo_seed:int=42):
        self.explanation_model = explanation_model
        self.monte_carlo_seed = monte_carlo_seed

        # Initialise seed counter used to ensure every sampling has a unique seed
        self.seed_counter = 0

    '''
    EXPLAIN
    '''
    def explain(self, query, max_depth = 1, samples = 10, **kwargs):
        super().explain(query,max_depth=max_depth,samples=samples, **kwargs)

    def explain_to_depth(
            self,
            query:ProbabilisticQuery,
            search_space:dict[str,list],
            search_graph:nx.DiGraph,
            depth:int=1,
            samples:int=10,
            **kwargs
    ) -> List[ProbabilisticCounterfactualExplanation]:
        # Determine all possible intervention combinations
        search_combos = self.generate_combinations(search_space,depth)

        explanations:List[ProbabilisticCounterfactualExplanation] = []
        for combo in search_combos:

            # Keep track of satisfaction rate and individual outcomes for each sample
            satisfied_count = 0
            sample_outcomes = []

            for sample_i in range(samples):
                # Sample the values of exogenous variables in the causal model
                sampled_model_state = self.sample_exogenous_state(query.model_state,sample_index=sample_i)

                # Perform intervention
                new_graph,new_model_state = self.explanation_model.intervene(combo,search_graph,sampled_model_state)

                # Check for satisfaction and add to list
                satisfies = query.satisfies_query(new_model_state)
                if satisfies:
                    satisfied_count += 1
                counterfactual_foils = {k: new_model_state[k] for k in query.foils}
                sample_outcomes.append({
                    "sample_index": sample_i,
                    "satisfied": satisfies,
                    "foils": counterfactual_foils
                })

            satisfaction_rate = satisfied_count / samples
            # TODO : Decide ultimate explanation inclusion depending on thresholds or whatever and create a final explanation
            # For now we can assume a fixed threshold of 0.8, but this will change later

            print(f"For combo {combo}, satisfaction rate: {satisfaction_rate}")
            if satisfaction_rate != 0 and satisfaction_rate != 1:
                for outcome in sample_outcomes:
                    print(outcome)

        return explanations

    '''
    PROBABILISTIC OPERATIONS
    '''
    def sample_exogenous_state(self,model_state:dict[str],sample_index:int) -> dict[str]:
        exogenous_variables = [self.explanation_model.exogenouses[key] for key in self.explanation_model.exogenouses]

        new_state = copy.deepcopy(model_state)

        for var in exogenous_variables:
            # Combined seed
            seed_tuple = (self.monte_carlo_seed, self.seed_counter, sample_index, var)
            # Sample exogenous variable
            rng = random.Random(seed_tuple)
            new_state[var] = rng.uniform(0, 1)

        return new_state

        

        