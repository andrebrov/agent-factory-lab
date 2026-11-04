"""
Small math/utility library with 10 intentionally seeded bugs.
Each bug has a corresponding test in test_mathlib.py that fails.
Used as the target codebase for agent experiments.
"""


def factorial(n):
    """Bug 1: Off-by-one — range should start at 1, not 0. Multiplying by 0."""
    if n < 0:
        raise ValueError("n must be non-negative")
    result = 1
    for i in range(0, n + 1):  # BUG: should be range(1, n + 1)
        result *= i
    return result


def fibonacci(n):
    """Bug 2: Wrong base case — fib(1) should return 1, returns 0."""
    if n <= 0:
        return 0
    if n == 1:
        return 0  # BUG: should return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def is_prime(n):
    """Bug 3: Wrong operator — should be n % i == 0, uses n // i == 0."""
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n // i == 0:  # BUG: should be n % i == 0
            return False
    return True


def binary_search(arr, target):
    """Bug 4: Missing bounds check — returns mid even when element not found."""
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] < target:
            lo = mid + 1
        elif arr[mid] > target:
            hi = mid - 1
        else:
            return mid
    return mid  # BUG: should return -1


def mean(numbers):
    """Bug 5: No empty-list guard — ZeroDivisionError."""
    return sum(numbers) / len(numbers)  # BUG: no guard for empty list


def flatten(nested):
    """Bug 6: Wrong type check — checks for tuple instead of list."""
    result = []
    for item in nested:
        if isinstance(item, tuple):  # BUG: should be isinstance(item, (list, tuple))
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def merge_sorted(a, b):
    """Bug 7: Off-by-one in index — starts j at 1 instead of 0."""
    result = []
    i, j = 0, 1  # BUG: j should start at 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            result.append(a[i])
            i += 1
        else:
            result.append(b[j])
            j += 1
    result.extend(a[i:])
    result.extend(b[j:])
    return result


def caesar_cipher(text, shift):
    """Bug 8: Applies shift to ALL characters, not just letters."""
    result = []
    for ch in text:
        result.append(chr(ord(ch) + shift))  # BUG: should only shift a-z/A-Z
    return "".join(result)


def unique(items):
    """Bug 9: Loses original order — uses set() which doesn't preserve order."""
    return list(set(items))  # BUG: doesn't preserve insertion order reliably


def clamp(value, lo, hi):
    """Bug 10: Swapped lo/hi comparison — returns hi when value < lo."""
    if value < lo:
        return hi  # BUG: should return lo
    if value > hi:
        return lo  # BUG: should return hi
    return value
