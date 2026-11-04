"""
Corrected version of mathlib.py — all 10 bugs fixed.
Used as the ground-truth reference for experiments.
"""


def factorial(n):
    if n < 0:
        raise ValueError("n must be non-negative")
    result = 1
    for i in range(1, n + 1):  # FIX: start at 1
        result *= i
    return result


def fibonacci(n):
    if n <= 0:
        return 0
    if n == 1:
        return 1  # FIX: return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:  # FIX: use modulo
            return False
    return True


def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] < target:
            lo = mid + 1
        elif arr[mid] > target:
            hi = mid - 1
        else:
            return mid
    return -1  # FIX: return -1


def mean(numbers):
    if not numbers:  # FIX: guard empty list
        raise ValueError("cannot compute mean of empty list")
    return sum(numbers) / len(numbers)


def flatten(nested):
    result = []
    for item in nested:
        if isinstance(item, (list, tuple)):  # FIX: check list and tuple
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def merge_sorted(a, b):
    result = []
    i, j = 0, 0  # FIX: j starts at 0
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
    result = []
    for ch in text:
        if ch.isalpha():  # FIX: only shift letters
            base = ord("A") if ch.isupper() else ord("a")
            result.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            result.append(ch)
    return "".join(result)


def unique(items):
    seen = set()
    result = []
    for item in items:  # FIX: preserve order
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def clamp(value, lo, hi):
    if value < lo:
        return lo  # FIX: return lo
    if value > hi:
        return hi  # FIX: return hi
    return value
