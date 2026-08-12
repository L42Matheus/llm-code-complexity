def count_vowels(s):
    """Count the number of vowels in a string.

    Args:
        s: The input string.

    Returns:
        int: Number of vowels found.
    """
    if s is None:
        raise TypeError("Input cannot be None")
    if not isinstance(s, str):
        raise TypeError("Input must be a string")
    if len(s) == 0:
        return 0
    vowels = "aeiouAEIOU"
    count = 0
    for ch in s:
        if ch in vowels:
            count += 1
    return count
