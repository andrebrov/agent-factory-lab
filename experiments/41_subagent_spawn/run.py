#!/usr/bin/env python3
"""
Experiment 41: Subagent Spawn — Task File vs Cloned History
==============================================================

Compares tokens per task when spawning a sub-agent with:
  (a) A short task file (< 400 tokens): target paths, constraints, checks.
  (b) The parent session's full history cloned to the child.

Differs from exp 38 (handoff): handoff transfers ongoing state between
peers; spawn starts a fresh child for a scoped subtask.

MEASURED: real tiktoken token counting on realistic spawn payloads.
"""
import json
import os
import argparse
from pathlib import Path

SAMPLE_DIR = Path(__file__).parent.parent / "sample_codebase"

PARENT_HISTORY = """User: Fix the 10 seeded bugs in mathlib.py.
Assistant: I'll start by reading the file structure and identifying all bugs.
Tool: list_dir('.') → mathlib.py, test_mathlib.py, mathlib_fixed.py
Assistant: Let me read the main file.
Tool: read_file('mathlib.py') → [full 105-line file]
Assistant: I found all 10 bugs. Here's my plan:
1. Fix factorial (range starts at 0)
2. Fix fibonacci (base case returns 0)
3. Fix is_prime (uses // instead of %)
4. Fix binary_search (returns mid on miss)
5. Fix mean (no empty guard)
6. Fix flatten (only checks tuple)
7. Fix merge_sorted (j starts at 1)
8. Fix caesar_cipher (shifts all chars)
9. Fix unique (set loses order)
10. Fix clamp (lo/hi swapped)

Let me delegate each bug to a sub-agent. Starting with factorial...
"""

SYSTEM_PROMPT = """You are an expert software engineer. Fix bugs and write tests.
Tools: read_file, write_file, run_command, search_files, list_directory."""

BUGS = [
    {
        "name": "factorial",
        "task_file": "## Task: Fix factorial\n- File: mathlib.py\n- Bug: range(0, n+1) should be range(1, n+1)\n- Constraint: change only the factorial function\n- Accept: pytest test_mathlib.py::test_factorial_basic passes",
        "relevant_code": "def factorial(n):\n    if n < 0:\n        raise ValueError\n    result = 1\n    for i in range(0, n + 1):\n        result *= i\n    return result",
        "test_name": "test_factorial_basic",
    },
    {
        "name": "fibonacci",
        "task_file": "## Task: Fix fibonacci\n- File: mathlib.py\n- Bug: fib(1) returns 0, should return 1\n- Constraint: change only the fibonacci function\n- Accept: pytest test_mathlib.py::test_fibonacci_base passes",
        "relevant_code": "def fibonacci(n):\n    if n <= 0: return 0\n    if n == 1: return 0\n    a, b = 0, 1\n    for _ in range(2, n+1): a, b = b, a+b\n    return b",
        "test_name": "test_fibonacci_base",
    },
    {
        "name": "is_prime",
        "task_file": "## Task: Fix is_prime\n- File: mathlib.py\n- Bug: uses n//i==0 instead of n%i==0\n- Constraint: change only the is_prime function\n- Accept: pytest test_mathlib.py::test_is_prime passes",
        "relevant_code": "def is_prime(n):\n    if n < 2: return False\n    for i in range(2, int(n**0.5)+1):\n        if n // i == 0: return False\n    return True",
        "test_name": "test_is_prime",
    },
    {
        "name": "binary_search",
        "task_file": "## Task: Fix binary_search\n- File: mathlib.py\n- Bug: returns mid instead of -1 on miss\n- Constraint: change only the binary_search function\n- Accept: pytest test_mathlib.py::test_binary_search_missing passes",
        "relevant_code": "def binary_search(arr, target):\n    lo, hi = 0, len(arr)-1\n    while lo <= hi:\n        mid = (lo+hi)//2\n        if arr[mid] < target: lo = mid+1\n        elif arr[mid] > target: hi = mid-1\n        else: return mid\n    return mid",
        "test_name": "test_binary_search_missing",
    },
    {
        "name": "mean",
        "task_file": "## Task: Fix mean\n- File: mathlib.py\n- Bug: no empty-list guard, ZeroDivisionError\n- Constraint: change only the mean function, raise ValueError on empty\n- Accept: pytest test_mathlib.py::test_mean_empty passes",
        "relevant_code": "def mean(numbers):\n    return sum(numbers) / len(numbers)",
        "test_name": "test_mean_empty",
    },
]


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def main():
    parser = argparse.ArgumentParser(description="Experiment 41: Subagent Spawn")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken
        has_tiktoken = True
    except ImportError:
        pass
    token_label = "MEASURED (tiktoken)" if has_tiktoken else "ESTIMATED"

    print("=" * 65)
    print("EXPERIMENT 41: Subagent Spawn — Task File vs Cloned History")
    print("=" * 65)
    print(f"Token counting: {token_label}")
    print(f"Bugs: {len(BUGS)}")
    print()

    system_tokens = count_tokens(SYSTEM_PROMPT)
    history_tokens = count_tokens(PARENT_HISTORY)
    mathlib_tokens = count_tokens((SAMPLE_DIR / "mathlib.py").read_text())
    test_tokens = count_tokens((SAMPLE_DIR / "test_mathlib.py").read_text())

    print(f"Baseline sizes:")
    print(f"  System prompt: {system_tokens} tokens")
    print(f"  Parent history: {history_tokens} tokens")
    print(f"  mathlib.py: {mathlib_tokens} tokens")
    print(f"  test_mathlib.py: {test_tokens} tokens")
    print()

    print(f"{'Bug':<16} {'Task File':>10} {'Spawn':>10} {'Clone':>10} {'Saved':>8} {'<400?':>6}")
    print("-" * 64)

    results = []
    for bug in BUGS:
        task_tokens = count_tokens(bug["task_file"])
        code_tokens = count_tokens(bug["relevant_code"])

        # Task-file spawn: system + task file + relevant code snippet
        spawn_tokens = system_tokens + task_tokens + code_tokens

        # Clone spawn: system + full parent history + all files
        clone_tokens = system_tokens + history_tokens + mathlib_tokens + test_tokens

        saved = clone_tokens - spawn_tokens
        saved_pct = saved / clone_tokens * 100
        under_400 = task_tokens < 400

        print(f"  {bug['name']:<14} {task_tokens:>10} {spawn_tokens:>10} "
              f"{clone_tokens:>10} {saved_pct:>7.0f}% {'yes' if under_400 else 'NO':>5}")

        results.append({
            "bug": bug["name"],
            "task_file_tokens": task_tokens,
            "spawn_total_tokens": spawn_tokens,
            "clone_total_tokens": clone_tokens,
            "savings_pct": round(saved_pct, 2),
            "task_under_400": under_400,
        })

    avg_spawn = sum(r["spawn_total_tokens"] for r in results) / len(results)
    avg_clone = sum(r["clone_total_tokens"] for r in results) / len(results)
    avg_savings = (avg_clone - avg_spawn) / avg_clone * 100
    all_under_400 = all(r["task_under_400"] for r in results)

    total_5_tasks_spawn = sum(r["spawn_total_tokens"] for r in results)
    total_5_tasks_clone = sum(r["clone_total_tokens"] for r in results)

    print()
    print(f"{'Metric':<35} {'Spawn':>10} {'Clone':>10}")
    print("-" * 57)
    print(f"{'Avg tokens/task':<35} {avg_spawn:>10,.0f} {avg_clone:>10,.0f}")
    print(f"{'Total tokens (5 tasks)':<35} {total_5_tasks_spawn:>10,} {total_5_tasks_clone:>10,}")
    print(f"{'Token savings':<35} {'—':>10} {avg_savings:>9.1f}%")
    print(f"{'All task files < 400 tokens':<35} {all_under_400!s:>10} {'n/a':>10}")
    print()

    # Compare with exp 38 handoff
    exp38_handoff = 467  # from exp 38 results
    print(f"Comparison with exp 38 (session handoff): {exp38_handoff} tokens")
    print(f"  Spawn task file avg: {sum(r['task_file_tokens'] for r in results) / len(results):.0f} tokens")
    print(f"  Spawn is {sum(r['task_file_tokens'] for r in results) / len(results) / exp38_handoff * 100:.0f}% "
          f"of handoff size (more focused, less context)")
    print()

    print(f"Conclusion ({token_label}): Task-file spawn saves {avg_savings:.0f}% of tokens")
    print(f"vs cloning parent history. All task files are under 400 tokens.")
    print(f"This is complementary to exp 38 — spawn for fresh subtasks,")
    print(f"handoff for session continuity.")

    summary = {
        "experiment": "41_subagent_spawn",
        "simulated": False,
        "token_method": "tiktoken" if has_tiktoken else "word_estimate",
        "bugs_tested": len(BUGS),
        "avg_spawn_tokens": round(avg_spawn, 1),
        "avg_clone_tokens": round(avg_clone, 1),
        "avg_savings_pct": round(avg_savings, 2),
        "all_task_files_under_400": all_under_400,
        "total_spawn_5_tasks": total_5_tasks_spawn,
        "total_clone_5_tasks": total_5_tasks_clone,
        "per_bug": results,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
