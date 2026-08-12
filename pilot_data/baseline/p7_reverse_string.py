def reverse_string(s):
    """Reverse a string.

    Args:
        s: The string to reverse.

    Returns:
        str: The reversed string.
    """
    if s is None:
        raise TypeError("Input cannot be None")
    if not isinstance(s, str):
        raise TypeError("Input must be a string")
    if len(s) == 0:
        return s
    return s[::-1]
