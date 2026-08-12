def find_max(lst):
    """Find the maximum value in a list of numbers.

    Args:
        lst: A list of numbers.

    Returns:
        The maximum value.

    Raises:
        ValueError: If the list is empty.
        TypeError: If input is not a list.
    """
    if lst is None:
        raise TypeError("Input cannot be None")
    if not isinstance(lst, list):
        raise TypeError("Input must be a list")
    if len(lst) == 0:
        raise ValueError("List cannot be empty")
    max_val = lst[0]
    for item in lst[1:]:
        if not isinstance(item, (int, float)):
            raise TypeError("All elements must be numbers")
        if item > max_val:
            max_val = item
    return max_val
