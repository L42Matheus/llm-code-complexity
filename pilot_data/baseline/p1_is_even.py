def is_even(n):
    """Check if a number is even.

    Args:
        n: The number to check.

    Returns:
        bool: True if n is even, False otherwise.

    Raises:
        TypeError: If n is not an integer.
    """
    if n is None:
        raise TypeError("Input cannot be None")
    if not isinstance(n, int):
        raise TypeError("Input must be an integer")
    if n < 0:
        n = abs(n)
    return n % 2 == 0
