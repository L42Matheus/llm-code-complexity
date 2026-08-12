def is_palindrome(s):
    """Check if a string is a palindrome.

    Args:
        s: The string to check.

    Returns:
        bool: True if s is a palindrome, False otherwise.
    """
    if s is None:
        raise TypeError("Input cannot be None")
    if not isinstance(s, str):
        raise TypeError("Input must be a string")
    cleaned = ""
    for ch in s:
        if ch.isalnum():
            cleaned += ch.lower()
    if len(cleaned) == 0:
        return True
    left, right = 0, len(cleaned) - 1
    while left < right:
        if cleaned[left] != cleaned[right]:
            return False
        left += 1
        right -= 1
    return True
