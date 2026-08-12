def is_prime(n):
    if n < 2:
        return False
    return all(n % i for i in range(2, int(n**0.5) + 1))
