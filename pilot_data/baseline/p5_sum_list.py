def sum_list(lst):
    """Sum all numbers in a list.

    Args:
        lst: A list of numbers.

    Returns:
        The sum of all elements.
    """
    if lst is None:
        raise TypeError("Input cannot be None")
    if not isinstance(lst, list):
        raise TypeError("Input must be a list")
    if len(lst) == 0:
        return 0
    total = 0
    for item in lst:
        if not isinstance(item, (int, float)):
            raise TypeError("All elements must be numbers")
        total += item
    return total
