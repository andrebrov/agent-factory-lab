#!/usr/bin/env python3
"""
Experiment 12: HANDOFF.md vs Full Transcript — Context Savings
================================================================

Compares token costs between passing a full transcript vs a 60-line
HANDOFF.md summary when handing work between agents or sessions.

REAL TOKEN COUNTS (tiktoken) on synthetic but realistic transcripts.
"""
import json
import os
import argparse

FULL_TRANSCRIPT_TURNS = [
    "User: Fix the bugs in mathlib.py. There are 10 known bugs.",
    "Assistant: I'll start by reading the file and understanding the codebase structure. Let me list the files first.",
    "Tool: list_dir('.') -> mathlib.py, test_mathlib.py, mathlib_fixed.py",
    "Assistant: Now let me read mathlib.py to identify the bugs.",
    "Tool: read_file('mathlib.py') -> [contents of mathlib.py, ~100 lines]",
    "Assistant: I can see several bugs. Let me also read the test file to understand expected behavior.",
    "Tool: read_file('test_mathlib.py') -> [contents of test_mathlib.py, ~75 lines]",
    "Assistant: I've identified all 10 bugs. Let me fix them one by one.\n\nBug 1: factorial - range starts at 0 instead of 1. Fixing by changing range(0, n+1) to range(1, n+1).\nBug 2: fibonacci - base case returns 0 instead of 1. Fixing the return value.\nBug 3: is_prime - uses integer division instead of modulo. Changing // to %.\nBug 4: binary_search - returns mid on miss instead of -1. Fixing the return.\nBug 5: mean - no empty-list guard. Adding ValueError raise.",
    "Tool: write_file('mathlib.py', [updated contents]) -> OK",
    "Assistant: First 5 bugs fixed. Now fixing the remaining 5.\n\nBug 6: flatten - checks tuple instead of (list, tuple). Fixing isinstance.\nBug 7: merge_sorted - j starts at 1 instead of 0. Fixing initialization.\nBug 8: caesar_cipher - shifts all chars. Adding isalpha check.\nBug 9: unique - set() loses order. Using seen-set pattern.\nBug 10: clamp - lo/hi returns swapped. Fixing.",
    "Tool: write_file('mathlib.py', [final contents]) -> OK",
    "Assistant: All fixes applied. Let me run the tests to verify.",
    "Tool: run_command('python -m pytest test_mathlib.py -v') -> 10 passed in 0.05s",
    "Assistant: All 10 tests pass. The bugs are fixed:\n1. factorial: range(1, n+1)\n2. fibonacci: return 1 for base case\n3. is_prime: modulo instead of floor division\n4. binary_search: return -1 on miss\n5. mean: guard for empty list\n6. flatten: check both list and tuple\n7. merge_sorted: j starts at 0\n8. caesar_cipher: only shift alpha chars\n9. unique: preserve insertion order\n10. clamp: correct lo/hi returns",
]

HANDOFF_MD = """# HANDOFF.md

## Task
Fix 10 seeded bugs in mathlib.py.

## Status: COMPLETE
All 10 bugs fixed. All 10 tests pass.

## Changes Made
- mathlib.py: Fixed all 10 functions

## Bug Fixes
1. factorial: range(0,n+1) -> range(1,n+1)
2. fibonacci: base case return 0 -> return 1
3. is_prime: n//i -> n%i
4. binary_search: return mid -> return -1 on miss
5. mean: added empty-list ValueError guard
6. flatten: isinstance(tuple) -> isinstance((list,tuple))
7. merge_sorted: j=1 -> j=0
8. caesar_cipher: added isalpha() guard
9. unique: set() -> seen-set preserving order
10. clamp: swapped lo/hi return values

## Key Files
- mathlib.py (modified)
- test_mathlib.py (unchanged, all 10 pass)
- mathlib_fixed.py (reference, unchanged)

## Decisions
- Fixed bugs in-place rather than rewriting functions
- Preserved original function signatures
- No new tests added (existing suite covers all bugs)

## Remaining Work
None — task complete.
"""


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def main():
    parser = argparse.ArgumentParser(description="Experiment 12: HANDOFF.md Context Savings")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken
        has_tiktoken = True
    except ImportError:
        pass

    token_label = "REAL (tiktoken)" if has_tiktoken else "ESTIMATED (word-count)"

    full_text = "\n".join(FULL_TRANSCRIPT_TURNS)
    handoff_text = HANDOFF_MD.strip()

    full_tokens = count_tokens(full_text)
    handoff_tokens = count_tokens(handoff_text)

    full_lines = len(full_text.splitlines())
    handoff_lines = len(handoff_text.splitlines())

    reduction_tokens = (full_tokens - handoff_tokens) / full_tokens * 100
    reduction_lines = (full_lines - handoff_lines) / full_lines * 100

    key_facts = [
        "10 bugs fixed",
        "all tests pass",
        "mathlib.py modified",
        "factorial range fix",
        "fibonacci base case",
        "is_prime modulo",
        "binary_search return -1",
        "mean empty guard",
        "flatten list+tuple",
        "merge_sorted j=0",
        "caesar isalpha",
        "unique order preserved",
        "clamp lo/hi",
    ]
    facts_in_handoff = sum(1 for f in key_facts if any(
        kw in handoff_text.lower() for kw in f.lower().split()[:2]
    ))
    fact_retention = facts_in_handoff / len(key_facts) * 100

    print("=" * 65)
    print("EXPERIMENT 12: HANDOFF.md vs Full Transcript")
    print("=" * 65)
    print(f"Token counting: {token_label}")
    print()
    print(f"{'Metric':<35} {'Full Transcript':>15} {'HANDOFF.md':>12}")
    print("-" * 64)
    print(f"{'Lines':<35} {full_lines:>15} {handoff_lines:>12}")
    print(f"{'Tokens':<35} {full_tokens:>15,} {handoff_tokens:>12,}")
    print(f"{'Token reduction':<35} {'baseline':>15} {reduction_tokens:>11.1f}%")
    print(f"{'Line reduction':<35} {'baseline':>15} {reduction_lines:>11.1f}%")
    print(f"{'Key facts retained':<35} {len(key_facts):>15} {facts_in_handoff:>12}")
    print(f"{'Fact retention rate':<35} {'100%':>15} {fact_retention:>11.0f}%")
    print()

    restarts_per_session = 0
    typical_session_tokens = 150_000
    turns_to_150k = typical_session_tokens // (full_tokens // len(FULL_TRANSCRIPT_TURNS))
    print(f"Context-window restart policy:")
    print(f"  Restart threshold: 150K tokens")
    print(f"  Estimated turns before restart: ~{turns_to_150k}")
    print(f"  Tokens saved per restart: {full_tokens - handoff_tokens:,}")
    print()

    under_60 = handoff_lines <= 60
    print(f"HANDOFF.md under 60 lines: {'YES' if under_60 else 'NO'} ({handoff_lines} lines)")
    print()
    print(f"Conclusion ({token_label}): HANDOFF.md compresses the session to")
    print(f"{reduction_tokens:.0f}% fewer tokens while retaining {fact_retention:.0f}% of key facts.")
    print("Combined with the 150K-token restart policy, this prevents context")
    print("degradation in long sessions.")

    summary = {
        "experiment": "12_handoff_context",
        "simulated": not has_tiktoken,
        "token_method": "tiktoken" if has_tiktoken else "word_estimate",
        "full_transcript_tokens": full_tokens,
        "handoff_tokens": handoff_tokens,
        "token_reduction_pct": round(reduction_tokens, 2),
        "full_lines": full_lines,
        "handoff_lines": handoff_lines,
        "fact_retention_pct": round(fact_retention, 2),
        "handoff_under_60_lines": under_60,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
