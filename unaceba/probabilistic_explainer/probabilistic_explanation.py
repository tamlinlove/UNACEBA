from typing import List

from unaceba.explainer.explanation import CounterfactualExplanation

class ProbabilisticCounterfactualExplanation(CounterfactualExplanation):
    def __init__(
            self, 
            interventions:dict[str], 
            foils:List[dict[str]], 
            model_state:dict[str], 
            tick:int = None, 
            time:int = None, 
            satisfaction_rate:float = 1.0
        ):
        super().__init__(interventions, foils, model_state, tick, time)

        self.satisfaction_rate = satisfaction_rate

    def text(self, variable_names: dict[str, str] = None) -> str:
        def name(var):
            if variable_names and var in variable_names:
                return variable_names[var]
            return var

        def assignments(values: dict) -> str:
            return " and ".join(f"{name(var)} = {val}" for var, val in values.items())

        # Target variables: union of all variables appearing in any foil (order preserved)
        target_vars = list(dict.fromkeys(var for foil in self.counterfactual_foils for var in foil))

        # "target = real_value because reason = real_value [at timestep t:T]."
        targets_str = " and ".join(f"{name(var)} = {self.model_state[var]}" for var in target_vars)
        reasons_str = assignments(self.reasons)

        explanation = f"{targets_str} because {reasons_str}"
        if self.tick is not None and self.time is not None:
            explanation += f" at timestep {self.tick}:{self.time}"
        explanation += "."

        # Counterfactual clause
        interventions_str = assignments(self.counterfactual_interventions)
        foils = self.counterfactual_foils

        if len(foils) == 1:
            outcome_str = assignments(foils[0])
        else:
            # Wrap each outcome in parentheses so "and"/"or" stay unambiguous
            outcomes = [f"({assignments(foil)})" for foil in foils]
            if len(outcomes) == 2:
                outcome_str = f"either {outcomes[0]} or {outcomes[1]}"
            else:
                outcome_str = "one of " + ", ".join(outcomes[:-1]) + f", or {outcomes[-1]}"

        explanation += f" If {interventions_str}, then {outcome_str}"

        # Only mention the rate when it carries information
        if self.satisfaction_rate < 1.0:
            explanation += f" in {self.satisfaction_rate * 100:.3g}% of cases"

        explanation += "."
        return explanation