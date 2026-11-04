#!/usr/bin/env python3
"""
Experiment 15: Stop Writing Once Verification Passes
======================================================

Measures output-token savings from terse (3-line report) vs verbose
(full summary) completion messages.

REAL TOKEN COUNTS (tiktoken) on realistic completion messages.
"""
import json
import os
import argparse

VERBOSE_COMPLETION = """
I've completed the task. Here's a summary of everything I did:

1. First, I read the mathlib.py file to understand the codebase structure and identify all the bugs.
2. I found 10 bugs across 10 functions: factorial, fibonacci, is_prime, binary_search, mean, flatten, merge_sorted, caesar_cipher, unique, and clamp.
3. For the factorial function, I changed the range from range(0, n+1) to range(1, n+1) to fix the off-by-one error that was causing the result to always be 0 due to multiplication by 0.
4. For the fibonacci function, I changed the base case return value from 0 to 1, which was causing incorrect results for fib(1) and all subsequent values.
5. For is_prime, I changed the integer division operator (//) to the modulo operator (%) in the divisibility check.
6. For binary_search, I changed the return value when the element is not found from 'mid' to -1, which is the standard convention.
7. For mean, I added a guard clause that raises a ValueError when the input list is empty, preventing the ZeroDivisionError.
8. For flatten, I changed the isinstance check from just tuple to (list, tuple) so it correctly handles nested lists.
9. For merge_sorted, I fixed the initialization of j from 1 to 0 so the merge starts from the beginning of the second array.
10. For caesar_cipher, I added an isalpha() check so that only alphabetic characters are shifted, preserving spaces and punctuation.
11. For unique, I replaced the set() approach with a seen-set pattern that preserves insertion order.
12. For clamp, I swapped the return values for the lo and hi comparisons.

After making all these changes, I ran the test suite with pytest and all 10 tests now pass successfully. The codebase is in a clean state with no remaining bugs.

Let me know if you need anything else!
"""

TERSE_COMPLETION = """Status: PASS
Files changed: mathlib.py
Tests: 10/10 passed"""

MEDIUM_COMPLETION = """All 10 bugs fixed in mathlib.py. Tests pass (10/10).

Changes: factorial range, fibonacci base case, is_prime modulo, binary_search return,
mean guard, flatten isinstance, merge_sorted init, caesar isalpha, unique order, clamp swap."""


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def main():
    parser = argparse.ArgumentParser(description="Experiment 15: Stop on Verification")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken
        has_tiktoken = True
    except ImportError:
        pass

    token_label = "REAL (tiktoken)" if has_tiktoken else "ESTIMATED"

    verbose_tokens = count_tokens(VERBOSE_COMPLETION)
    terse_tokens = count_tokens(TERSE_COMPLETION)
    medium_tokens = count_tokens(MEDIUM_COMPLETION)

    reduction_terse = (verbose_tokens - terse_tokens) / verbose_tokens * 100
    reduction_medium = (verbose_tokens - medium_tokens) / verbose_tokens * 100

    pricing_output = 15.0  # $/M output tokens (Sonnet-class)
    verbose_cost = verbose_tokens * pricing_output / 1_000_000
    terse_cost = terse_tokens * pricing_output / 1_000_000
    medium_cost = medium_tokens * pricing_output / 1_000_000

    sessions_per_day = 50
    daily_saving_terse = (verbose_cost - terse_cost) * sessions_per_day
    daily_saving_medium = (verbose_cost - medium_cost) * sessions_per_day

    print("=" * 65)
    print("EXPERIMENT 15: Stop Writing Once Verification Passes")
    print("=" * 65)
    print(f"Token counting: {token_label}")
    print()

    print(f"{'Completion Style':<25} {'Tokens':>8} {'Reduction':>12} {'Cost/msg':>12}")
    print("-" * 59)
    print(f"{'Verbose (full summary)':<25} {verbose_tokens:>8} {'baseline':>12} ${verbose_cost:>10.6f}")
    print(f"{'Medium (2-line + list)':<25} {medium_tokens:>8} {reduction_medium:>11.1f}% ${medium_cost:>10.6f}")
    print(f"{'Terse (3-line report)':<25} {terse_tokens:>8} {reduction_terse:>11.1f}% ${terse_cost:>10.6f}")
    print()

    print(f"At {sessions_per_day} completions/day:")
    print(f"  Terse saves: ${daily_saving_terse:.4f}/day (${daily_saving_terse*30:.2f}/month)")
    print(f"  Medium saves: ${daily_saving_medium:.4f}/day (${daily_saving_medium*30:.2f}/month)")
    print()

    particle_claim = 45.0
    print(f"Particle's claimed reduction: {particle_claim:.0f}%")
    print(f"Our measured reduction (terse): {reduction_terse:.1f}%")
    print(f"Our measured reduction (medium): {reduction_medium:.1f}%")
    match = "consistent" if abs(reduction_terse - particle_claim) < 20 else "differs significantly"
    print(f"Assessment: Our terse measurement {match} with Particle's claim.")
    print()
    print("Conclusion: Terse completion messages save significant output tokens.")
    print("Combined with lower reasoning effort on the final turn, this is a")
    print("simple win for both cost and latency.")

    summary = {
        "experiment": "15_stop_on_verification",
        "simulated": not has_tiktoken,
        "token_method": "tiktoken" if has_tiktoken else "word_estimate",
        "verbose_tokens": verbose_tokens,
        "medium_tokens": medium_tokens,
        "terse_tokens": terse_tokens,
        "reduction_terse_pct": round(reduction_terse, 2),
        "reduction_medium_pct": round(reduction_medium, 2),
        "particle_claim_pct": particle_claim,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
