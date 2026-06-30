class Explanation:
    def __init__(self):
        pass

    '''
    DISPLAY
    '''
    def text(self,variable_names:dict[str,str]=None) -> str:
        raise NotImplementedError

class CounterfactualExplanation(Explanation):
    def __init__(
            self,
            interventions:dict[str],
            foils:dict[str],
            model_state:dict[str],
            tick:int=None,
            time:int=None
    ):
        super().__init__()

        self.reasons = {node:model_state[node] for node in interventions}
        self.counterfactual_interventions = interventions
        self.counterfactual_foils = foils
        self.model_state = model_state
        self.tick = tick
        self.time = time

    def __str__(self):
        return self.text()

    def text(self, variable_names: dict[str, str] = None) -> str:
        def name(var):
            if variable_names and var in variable_names:
                return variable_names[var]
            return var

        # Build the "target = real_value because reason = real_value, ..." clause
        target_clauses = []
        for target_var, foil_value in self.counterfactual_foils.items():
            real_value = self.model_state[target_var]
            target_clauses.append(f"{name(target_var)} = {real_value}")

        reason_clauses = []
        for reason_var, real_value in self.reasons.items():
            reason_clauses.append(f"{name(reason_var)} = {real_value}")

        targets_str = " and ".join(target_clauses)
        reasons_str = " and ".join(reason_clauses)

        explanation = f"{targets_str} because {reasons_str}"

        # Add timestep info if available
        if self.tick is not None and self.time is not None:
            explanation += f" at timestep {self.tick}:{self.time}"

        explanation += "."

        # Build the counterfactual clause
        intervention_clauses = []
        for reason_var, cf_value in self.counterfactual_interventions.items():
            intervention_clauses.append(f"{name(reason_var)} = {cf_value}")

        foil_clauses = []
        for target_var, foil_value in self.counterfactual_foils.items():
            foil_clauses.append(f"{name(target_var)} = {foil_value}")

        interventions_str = " and ".join(intervention_clauses)
        foils_str = " and ".join(foil_clauses)

        explanation += f" If {interventions_str}, then {foils_str}."

        return explanation

