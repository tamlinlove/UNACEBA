from unaceba.explainer.explanation_model import ExplanationModel
from unaceba.utils.util import take_closest

class Query:
    '''
    Class for a Counterfactual Query
    '''
    def __init__(self,foils:dict[str,list],explanation_model:ExplanationModel,model_state:dict):
        '''
        Input:
            foils - dictionary mapping variable names to a list of foil values
                Note: uses the specific temporal versions e.g. statevariable_t3 rather than generic statevariable
        '''
        self.foils = foils
        self.explanation_model = explanation_model
        self.model_state = model_state

    def __str__(self):
        # Fact
        fact_parts = ", ".join(
            f"{var}={self.model_state[var]}" for var in self.foils
        )

        # Foil
        def format_foil(var, vals):
            if len(vals) == 1:
                return f"{var}={vals[0]}"
            return f"{var} in [{', '.join(str(v) for v in vals)}]"

        foil_parts = ", ".join(format_foil(var, vals) for var, vals in self.foils.items())

        return f"Why {fact_parts} and not {foil_parts}?"

    def foil_vars(self) -> list[str]:
        return list(self.foils.keys())
    
    def satisfies_query(self,new_model_state:dict[str],rounding:bool=True) -> bool:
        for foil_var in self.foils:
            foil_var_val = new_model_state[foil_var]
            if rounding and self.explanation_model.var_ranges[foil_var].is_discretised():
                # Round the queried value to the nearest discretisation if applicable
                disc_vals = self.explanation_model.var_ranges[foil_var].values
                foil_var_val = take_closest(disc_vals,foil_var_val)

            if foil_var_val not in self.foils[foil_var]:
                return False
        return True

