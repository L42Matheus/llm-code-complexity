def fizzbuzz_single(n):
    """Return Fizz, Buzz, FizzBuzz or the number as string.

    Args:
        n: The number to evaluate.

    Returns:
        str: The FizzBuzz result.
    """
    if n is None:
        raise TypeError("Input cannot be None")
    if not isinstance(n, int):
        raise TypeError("Input must be an integer")
    if n <= 0:
        raise ValueError("Input must be positive")
    if n % 3 == 0 and n % 5 == 0:
        return "FizzBuzz"
    elif n % 3 == 0:
        return "Fizz"
    elif n % 5 == 0:
        return "Buzz"
    else:
        return str(n)
