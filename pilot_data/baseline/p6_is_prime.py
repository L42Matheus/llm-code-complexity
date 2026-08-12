def is_prime(n):
    """Check if a number is prime.

    Args:
        n: The number to check.

    Returns:
        bool: True if n is prime, False otherwise.
    """
    if n is None:
        raise TypeError("Input cannot be None")
    if not isinstance(n, int):
        raise TypeError("Input must be an integer")
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True
