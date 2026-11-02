from unaceba.explainer.explainer import Explainer
from unaceba.probabilistic_explainer.probabilistic_explanation_model import ProbabilisticExplanationModel
from unaceba.probabilistic_explainer.probabilistic_query import ProbabilisticQuery
from unaceba.probabilistic_explainer.probabilistic_explanation import ProbabilisticCounterfactualExplanation
from unaceba.utils.util import freeze

import networkx as nx
import copy
import random

from typing import List

class ProbabilisticExplainer(Explainer):
    def __init__(self,explanation_model:ProbabilisticExplanationModel,monte_carlo_seed:int=42,display:bool=True):
        self.explanation_model = explanation_model
        self.monte_carlo_seed = monte_carlo_seed
        self.display = display

        # Initialise seed counter used to ensure every sampling has a unique seed
        self.seed_counter = 0

    '''
    EXPLAIN
    '''
    def explain(self, query, max_depth=1, samples=10, **kwargs):
        # Build the same search graph the parent will use, so the baseline is comparable
        search_space = self.calculate_search_space(query=query)
        search_graph = self.reduce_graph(query, search_space)

        # Baseline: effect of random noise alone
        baseline_rate, baseline_outcomes = self.estimate_baseline(query, search_graph, samples)

        if self.display:
            print(f"Baseline satisfaction rate (no interventions): {baseline_rate:.2f} "
            f"({len(baseline_outcomes)} samples, {samples} requested)")
            for o in baseline_outcomes:
                print(f"  sample {o['sample_index']}: satisfied={o['satisfied']}, foils={o['foils']}")

        # Dynamic threshold is passed down to explain_to_depth via kwargs
        kwargs["satisfaction_threshold"] = baseline_rate

        return super().explain(query, max_depth=max_depth, samples=samples, **kwargs)

    def explain_to_depth(
            self,
            query: ProbabilisticQuery,
            search_space: dict[str, list],
            search_graph: nx.DiGraph,
            depth: int = 1,
            samples: int = 10,
            satisfaction_threshold: float = 0.0,
            **kwargs
        ) -> List[ProbabilisticCounterfactualExplanation]:
        # Determine all possible intervention combinations
        search_combos = self.generate_combinations(search_space,depth)
        if self.display:
            print(f"Searching through {len(search_combos)} intervention assignments at depth {depth}")

        explanations:List[ProbabilisticCounterfactualExplanation] = []

        for combo in search_combos:
            probabilistic_path = self.explanation_model.probabilistic_path(list(combo.keys()), query.foil_vars())
            monte_carlo_num = samples if probabilistic_path else 1

            sample_outcomes = [
                self.run_sample(query, search_graph, combo, i)
                for i in range(monte_carlo_num)
            ]
            satisfied_count = sum(so["satisfied"] for so in sample_outcomes)
            satisfaction_rate = satisfied_count / monte_carlo_num

            # Only keep interventions that beat the no-intervention baseline
            if satisfaction_rate > satisfaction_threshold:
                explanation = ProbabilisticCounterfactualExplanation(
                    interventions=combo,
                    foils=self.unique_foils([so["foils"] for so in sample_outcomes if so["satisfied"]]),
                    model_state=query.model_state,
                    satisfaction_rate=satisfaction_rate
                )
                explanations.append(explanation)

        return explanations

    def run_sample(self, query, search_graph, combo: dict, sample_index: int):
        """Run one Monte Carlo sample under the given interventions (empty dict = noise only)."""
        sampled_model_state = self.sample_exogenous_state(query.model_state, sample_index=sample_index)
        _, new_model_state = self.explanation_model.intervene(combo, search_graph, sampled_model_state)

        satisfies = query.satisfies_query(new_model_state)
        return {
            "sample_index": sample_index,
            "satisfied": satisfies,
            "foils": {k: new_model_state[k] for k in query.foils},
        }

    def estimate_baseline(self, query, search_graph, samples: int):
        """Satisfaction rate with exogenous noise only, no targeted interventions."""
        exogenous_vars = list(self.explanation_model.exogenouses.values())

        # Noise only matters if it can reach the foils through a stochastic node
        probabilistic_path = self.explanation_model.probabilistic_path(exogenous_vars, query.foil_vars())
        monte_carlo_num = samples if probabilistic_path else 1

        outcomes = [self.run_sample(query, search_graph, {}, i) for i in range(monte_carlo_num)]
        rate = sum(o["satisfied"] for o in outcomes) / monte_carlo_num
        return rate, outcomes

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

    '''
    UTILITY
    '''
    @staticmethod
    def unique_foils(foils):
        seen = set()
        unique = []
        for foil in foils:
            key = freeze(foil)
            if key not in seen:
                seen.add(key)
                unique.append(foil)
        return unique

        

        