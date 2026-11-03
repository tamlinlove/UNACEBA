import math
from collections import defaultdict
from dataclasses import dataclass, replace
from typing import List, Optional

from unaceba.utils.variables import ContinuousRange, DiscretisedRange, IntRange


@dataclass
class _Term:
    var: str                       # raw name, or the base name once several times are merged
    values: list                   # reasons: one value; interventions: one or more
    times: Optional[list] = None   # sorted time indices, only set after merging over time


@dataclass
class _Item:
    targets: dict
    foils: list
    tick: Optional[int]
    time: Optional[int]
    rate: float
    reasons: List[_Term]
    interventions: List[_Term]
    n: int = 1    


class Aggregator:
    """
    Merges ProbabilisticCounterfactualExplanations that differ only in
    (a) the time index of their variables ("x_t0", "x_t1" -> "x"), and/or
    (b) the intervention value.
    """

    def __init__(self, explanation_model, targets, reasons, interventions,
                 foils, tick=None, time=None, satisfaction_rate=1.0):
        self.model = explanation_model
        self.targets = targets                  # {var: real value}
        self.reasons = reasons                  # List[_Term]
        self.interventions = interventions      # List[_Term]
        self.foils = foils
        self.tick = tick
        self.time = time
        self.satisfaction_rate = satisfaction_rate

    # ------------------------------------------------------------------
    # Variable helpers (delegating to the explanation model)
    # ------------------------------------------------------------------
    @staticmethod
    def get_variable(model, name: str) -> str:
        """'target_object_t3' -> 'target_object' (unchanged if not temporal)."""
        return model.state_var_names.get(name, name)

    @staticmethod
    def get_time(model, name: str) -> Optional[int]:
        """'target_object_t3' -> 3, taken from the position in temporal_state_vars."""
        base = model.state_var_names.get(name)
        if base is None:
            return None
        return model.temporal_state_vars[base].index(name)

    @classmethod
    def _split(cls, model, name):
        return cls.get_variable(model, name), cls.get_time(model, name)

    @staticmethod
    def _merged_stats(group: List[_Item]) -> dict:
        n = sum(it.n for it in group)
        return {"rate": sum(it.rate * it.n for it in group) / n, "n": n}

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------
    @classmethod
    def aggregate(cls, explanations, explanation_model,
                  over_time: bool = True, over_values: bool = True) -> list:
        if not explanations:
            return []
        items = [cls._to_item(e) for e in explanations]
        if over_values:                      # values first, so the time merge sees whole value sets
            items = cls._merge_values(items)
        if over_time:
            items = cls._merge_times(items, explanation_model)
        return [
            cls(explanation_model, i.targets, i.reasons, i.interventions,
                i.foils, i.tick, i.time, i.rate)
            for i in items
        ]

    @staticmethod
    def _to_item(e) -> _Item:
        return _Item(
            targets={v: e.model_state[v] for foil in e.counterfactual_foils for v in foil},
            foils=e.counterfactual_foils,
            tick=e.tick,
            time=e.time,
            rate=e.satisfaction_rate,
            reasons=[_Term(v, [x]) for v, x in e.reasons.items()],
            interventions=[_Term(v, [x]) for v, x in e.counterfactual_interventions.items()],
        )

    @staticmethod
    def _common_key(item: _Item):
        targets = tuple(sorted((k, repr(v)) for k, v in item.targets.items()))
        foils = tuple(sorted(
            tuple(sorted((k, repr(v)) for k, v in f.items())) for f in item.foils
        ))
        return targets, foils, item.tick, item.time

    # --- stage 1: merge intervention values ----------------------------
    @classmethod
    def _merge_values(cls, items: List[_Item]) -> List[_Item]:
        groups = defaultdict(list)
        for it in items:
            if len(it.interventions) == 1:   # merging several variables would imply a cross product
                key = (cls._common_key(it),
                       tuple(sorted((t.var, repr(t.values[0])) for t in it.reasons)),
                       it.interventions[0].var)
            else:
                key = ("keep", id(it))
            groups[key].append(it)

        out = []
        for g in groups.values():
            if len(g) == 1:
                out.append(g[0])
                continue
            values = []
            for it in g:
                v = it.interventions[0].values[0]
                if v not in values:
                    values.append(v)
            out.append(replace(
                g[0],
                interventions=[_Term(g[0].interventions[0].var, values)],
                **cls._merged_stats(g),
            ))
        return out

    # --- stage 2: merge time-shifted copies ----------------------------
    @classmethod
    def _time_shape(cls, item: _Item, model):
        """Time-independent signature of an item, or None if it can't be time-merged."""
        r = [(cls._split(model, t.var), t) for t in item.reasons]
        i = [(cls._split(model, t.var), t) for t in item.interventions]
        for side in (r, i):
            bases = [b for (b, _), _ in side]
            if len(bases) != len(set(bases)):    # same variable at two times: ambiguous
                return None
        times = [t for (_, t), _ in r + i if t is not None]
        if not times:
            return None
        shift = min(times)
        off = lambda t: None if t is None else t - shift
        reasons = tuple(sorted(
            ((b, off(t), repr(x.values[0])) for (b, t), x in r), key=repr))
        interventions = tuple(sorted(
            ((b, off(t), tuple(sorted(map(repr, x.values)))) for (b, t), x in i), key=repr))
        return reasons, interventions

    @classmethod
    def _merge_times(cls, items: List[_Item], model) -> List[_Item]:
        groups = defaultdict(list)
        for it in items:
            shape = cls._time_shape(it, model)
            key = ("shape", cls._common_key(it), shape) if shape is not None else ("keep", id(it))
            groups[key].append(it)

        def collapse(group, attr):
            merged = {}
            for it in group:
                for term in getattr(it, attr):
                    base, t = cls._split(model, term.var)
                    m = merged.setdefault(base, {"first": term, "times": set()})
                    if t is not None:
                        m["times"].add(t)
            out = []
            for base, m in merged.items():
                times = sorted(m["times"])
                if len(times) > 1:
                    out.append(_Term(base, m["first"].values, times))
                else:
                    out.append(_Term(m["first"].var, m["first"].values))
            return out

        out = []
        for g in groups.values():
            if len(g) == 1:
                out.append(g[0])
            else:
                out.append(replace(
                    g[0],
                    reasons=collapse(g, "reasons"),
                    interventions=collapse(g, "interventions"),
                    **cls._merge_stats(g) if False else cls._merged_stats(g),
                ))
        return out

    # ------------------------------------------------------------------
    # Conditions driven by the variable's range
    # ------------------------------------------------------------------
    @staticmethod
    def _index(grid, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        for i, g in enumerate(grid):
            if math.isclose(g, value, rel_tol=0, abs_tol=1e-9):
                return i
        return None

    def _condition(self, name: str, term: _Term, reason: Optional[_Term]) -> str:
        values = term.values
        if len(values) == 1:
            return f"{name} = {values[0]}"

        rng = self.model.tm.all_ranges.get(self.get_variable(self.model, term.var))

        # Ordered ranges: only claim a bound if the values form an unbroken run of the grid.
        if isinstance(rng, (ContinuousRange, IntRange)):
            grid = list(rng.values) if isinstance(rng, (DiscretisedRange, IntRange)) else None
            if grid:
                idx = [self._index(grid, v) for v in values]
                if None not in idx:
                    pairs = sorted(zip(idx, values), key=lambda p: p[0])
                    ids = [i for i, _ in pairs]
                    if ids == list(range(ids[0], ids[-1] + 1)):
                        (lo_i, lo), (hi_i, hi) = pairs[0], pairs[-1]
                        last = len(grid) - 1
                        if hi_i == last and lo_i > 0:
                            return f"{name} >= {lo}"
                        if lo_i == 0 and hi_i < last:
                            return f"{name} <= {hi}"
                        return f"{lo} <= {name} <= {hi}"

        # Unordered finite ranges: if every value except the real one was tried, say so.
        elif rng is not None and rng.values is not None and reason is not None:
            domain = list(rng.values)
            if rng.allow_none and None not in domain:
                domain.append(None)
            actual = reason.values[0]
            others = [d for d in domain if d != actual]
            if len(values) == len(others) and all(v in others for v in values):
                return f"{name} != {actual}"

        return f"{name} in {{{', '.join(map(str, values))}}}"

    # ------------------------------------------------------------------
    # Text
    # ------------------------------------------------------------------
    def __str__(self):
        return self.text()

    @staticmethod
    def _times_str(times: list) -> str:
        if times == list(range(times[0], times[-1] + 1)):
            return f"from time {times[0]} to time {times[-1]}"
        return "at times " + ", ".join(map(str, times))

    @staticmethod
    def _any_of_str(times: list) -> str:
        if times == list(range(times[0], times[-1] + 1)):
            return f"at any one of times {times[0]} to {times[-1]}"
        return "at any one of times " + ", ".join(map(str, times))

    def _name(self, var: str, variable_names: dict = None) -> str:
        if not variable_names:
            return var
        if var in variable_names:
            return variable_names[var]
        base = self.get_variable(self.model, var)
        if base in variable_names:
            return variable_names[base] + var[len(base):]
        return var

    def text(self, variable_names: dict = None) -> str:
        name = lambda v: self._name(v, variable_names)

        def assignments(values: dict) -> str:
            return " and ".join(f"{name(v)} = {x}" for v, x in values.items())

        # Reasons
        parts = []
        for t in self.reasons:
            s = f"{name(t.var)} = {t.values[0]}"
            if t.times:
                s += " " + self._times_str(t.times)
            parts.append(s)
        explanation = f"{assignments(self.targets)} because {' and '.join(parts)}"
        if self.tick is not None and self.time is not None:
            explanation += f" at timestep {self.tick}:{self.time}"
        explanation += "."

        # Interventions
        parts = []
        for t in self.interventions:
            reason = next((r for r in self.reasons if r.var == t.var), None)
            s = self._condition(name(t.var), t, reason)
            if t.times:
                s += " " + self._any_of_str(t.times)
            parts.append(s)
        interventions_str = " and ".join(parts)

        # Outcome
        foils = self.foils
        if len(foils) == 1:
            outcome_str = assignments(foils[0])
        else:
            outcomes = [f"({assignments(f)})" for f in foils]
            if len(outcomes) == 2:
                outcome_str = f"either {outcomes[0]} or {outcomes[1]}"
            else:
                outcome_str = "one of " + ", ".join(outcomes[:-1]) + f", or {outcomes[-1]}"

        explanation += f" If {interventions_str}, then {outcome_str}"
        if self.satisfaction_rate < 1.0:
            explanation += f" in {self.satisfaction_rate * 100:.3g}% of cases"
        return explanation + "."