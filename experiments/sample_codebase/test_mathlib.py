"""
Tests for mathlib.py — each test targets one seeded bug.
All 10 tests FAIL against the buggy version.
"""
import pytest
from mathlib import (
    factorial,
    fibonacci,
    is_prime,
    binary_search,
    mean,
    flatten,
    merge_sorted,
    caesar_cipher,
    unique,
    clamp,
)


def test_factorial_basic():
    """Bug 1: factorial(5) should be 120."""
    assert factorial(0) == 1
    assert factorial(1) == 1
    assert factorial(5) == 120


def test_fibonacci_base():
    """Bug 2: fibonacci(1) should be 1."""
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    assert fibonacci(10) == 55


def test_is_prime():
    """Bug 3: 7 is prime, 4 is not."""
    assert is_prime(7) is True
    assert is_prime(4) is False
    assert is_prime(1) is False


def test_binary_search_missing():
    """Bug 4: searching for absent element should return -1."""
    assert binary_search([1, 3, 5, 7], 4) == -1


def test_mean_empty():
    """Bug 5: mean of empty list should raise ValueError."""
    with pytest.raises(ValueError):
        mean([])


def test_flatten_nested_lists():
    """Bug 6: flatten should handle nested lists, not just tuples."""
    assert flatten([1, [2, 3], [4, [5]]]) == [1, 2, 3, 4, 5]


def test_merge_sorted():
    """Bug 7: merge_sorted([1,3,5], [2,4,6]) should give [1,2,3,4,5,6]."""
    assert merge_sorted([1, 3, 5], [2, 4, 6]) == [1, 2, 3, 4, 5, 6]


def test_caesar_cipher_preserves_non_alpha():
    """Bug 8: spaces and punctuation should be unchanged."""
    assert caesar_cipher("Hi!", 3) == "Kl!"


def test_unique_preserves_order():
    """Bug 9: unique should preserve insertion order."""
    assert unique([3, 1, 2, 1, 3]) == [3, 1, 2]


def test_clamp():
    """Bug 10: clamp should return lo when value < lo."""
    assert clamp(-5, 0, 10) == 0
    assert clamp(15, 0, 10) == 10
    assert clamp(5, 0, 10) == 5
