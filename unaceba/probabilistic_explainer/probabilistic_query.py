from unaceba.explainer.query import Query
from unaceba.probabilistic_explainer.probabilistic_explanation_model import ModelStateValue
from unaceba.utils.util import take_closest

from typing import Dict

class ProbabilisticQuery(Query):
    def __init__(self, foils, explanation_model, model_state):
        super().__init__(foils, explanation_model, model_state)

    def satisfies_query(self, new_model_state:Dict[str,ModelStateValue], rounding = True) -> tuple[bool,float]:
        # NOTE: For now we assume there is only one foil variable
        # TODO: Implement logic for multiple foil variables - requires handling join probability distributions

        foil_var = self.foil_vars()[0]
        foil_var_val = new_model_state[foil_var]

        if foil_var_val.probabilistic:
            satisfy_prob = sum([foil_var_val.distribution[sat_val] for sat_val in self.foils[foil_var]])
            
            threshold = 0.6 # TODO: calculate properly
            if satisfy_prob >= threshold:
                return True
            return False

        else:
            # Deterministic, can use absolute criteria
            if rounding and self.explanation_model.var_ranges[foil_var].is_discretised():
                # Round the queried value to the nearest discretisation if applicable
                disc_vals = self.explanation_model.var_ranges[foil_var].values
                foil_var_val = take_closest(disc_vals,foil_var_val)

            if foil_var_val not in self.foils[foil_var]:
                return False
            return True