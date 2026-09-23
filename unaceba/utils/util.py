from bisect import bisect_left

def take_closest(myList:list, myNumber):
    """
    Assumes myList is sorted. Returns closest value to myNumber.

    If two numbers are equally close, return the smallest number.
    """
    pos = bisect_left(myList, myNumber)
    if pos == 0:
        return myList[0]
    if pos == len(myList):
        return myList[-1]
    before = myList[pos - 1]
    after = myList[pos]
    if after - myNumber < myNumber - before:
        return after
    else:
        return before
    
def diff_dicts(dict1: dict, dict2: dict) -> str:
    """
    Compare two dicts with the same keys and return a human-readable
    string highlighting differences. dict1 is treated as the older
    version, dict2 as the newer version.
    """
    if dict1.keys() != dict2.keys():
        missing = set(dict1) - set(dict2)
        extra = set(dict2) - set(dict1)
        raise ValueError(
            f"Dicts do not have the same keys. "
            f"Missing from dict2: {missing}, extra in dict2: {extra}"
        )

    changes = [
        f"{key}: {dict1[key]!r} -> {dict2[key]!r}"
        for key in dict1
        if dict1[key] != dict2[key]
    ]

    if not changes:
        return "None"

    return "; ".join(changes)

def select_from_distribution(probs, possible_keys, exogenous_variable):
    """
    Deterministically pick a key from a probability distribution using
    inverse-CDF sampling.

    probs: dict mapping key -> probability (keys with 0 probability may be omitted)
    possible_keys: ordered sequence of all possible keys; its order defines the CDF
    exogenous_variable: float in [0, 1]
    """
    if not 0 <= exogenous_variable <= 1:
        raise ValueError("exogenous_variable must be between 0 and 1")

    unknown = set(probs) - set(possible_keys)
    if unknown:
        raise ValueError(f"Keys in probs not found in possible_keys: {unknown}")

    # Missing keys get probability 0
    ordered = [(k, probs.get(k, 0.0)) for k in possible_keys]
    total = sum(p for _, p in ordered)
    if total <= 0:
        raise ValueError("Probabilities must have a positive sum")

    # Scale u by the total so small floating-point errors in the sum don't matter
    threshold = exogenous_variable * total

    cumulative = 0.0
    last_valid = None
    for key, p in ordered:
        if p <= 0:
            continue
        last_valid = key
        cumulative += p
        if threshold < cumulative:
            return key

    # Reached only if threshold == total (e.g. u = 1.0) or due to rounding
    return last_valid