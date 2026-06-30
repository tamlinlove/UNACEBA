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