#!/usr/bin/env python3
"""
Experiment 11: Mutation Check — Deliberate Breaks to Verify Tests
===================================================================

Applies mutations to the fixed sample codebase and checks whether the test
suite catches them. Measures mutation kill rate.

REAL EXECUTION — actually mutates code and runs pytest.
"""
import json
import os
import sys
import subprocess
import shutil
import tempfile
import argparse
from pathlib import Path

SAMPLE_DIR = Path(__file__).parent.parent / "sample_codebase"

MUTATIONS = [
    {
        "function": "factorial",
        "description": "Change range(1, n+1) to range(1, n)",
        "find": "for i in range(1, n + 1):",
        "replace": "for i in range(1, n):",
    },
    {
        "function": "fibonacci",
        "description": "Change return 1 to return 0 for base case",
        "find": "        return 1  # FIX: return 1",
        "replace": "        return 0",
    },
    {
        "function": "is_prime",
        "description": "Change n % i to n // i",
        "find": "if n % i == 0:  # FIX: use modulo",
        "replace": "if n // i == 0:",
    },
    {
        "function": "binary_search",
        "description": "Change return -1 to return 0",
        "find": "return -1  # FIX: return -1",
        "replace": "return 0",
    },
    {
        "function": "mean",
        "description": "Remove empty-list guard",
        "find": "    if not numbers:  # FIX: guard empty list\n        raise ValueError(\"cannot compute mean of empty list\")\n",
        "replace": "",
    },
    {
        "function": "flatten",
        "description": "Check only tuple, not list",
        "find": "if isinstance(item, (list, tuple)):  # FIX: check list and tuple",
        "replace": "if isinstance(item, tuple):",
    },
    {
        "function": "merge_sorted",
        "description": "Start j at 1",
        "find": "i, j = 0, 0  # FIX: j starts at 0",
        "replace": "i, j = 0, 1",
    },
    {
        "function": "caesar_cipher",
        "description": "Remove isalpha check",
        "find": "        if ch.isalpha():  # FIX: only shift letters",
        "replace": "        if True:",
    },
    {
        "function": "clamp",
        "description": "Swap lo and hi returns",
        "find": "        return lo  # FIX: return lo",
        "replace": "        return hi",
    },
    {
        "function": "unique",
        "description": "Use set() directly (lose order)",
        "find": "    seen = set()\n    result = []\n    for item in items:  # FIX: preserve order\n        if item not in seen:\n            seen.add(item)\n            result.append(item)\n    return result",
        "replace": "    return list(set(items))",
    },
]


def apply_mutation_and_test(mutation: dict) -> dict:
    """Apply one mutation to the fixed code and run the test suite."""
    fixed_code = (SAMPLE_DIR / "mathlib_fixed.py").read_text()

    if mutation["find"] not in fixed_code:
        return {
            "function": mutation["function"],
            "description": mutation["description"],
            "applied": False,
            "killed": False,
            "error": "mutation target not found in source",
        }

    mutated = fixed_code.replace(mutation["find"], mutation["replace"], 1)

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "mathlib.py"), "w") as f:
            f.write(mutated)
        shutil.copy(SAMPLE_DIR / "test_mathlib.py", tmpdir)

        result = subprocess.run(
            [sys.executable, "-m", "pytest", "test_mathlib.py", "-v", "--tb=no"],
            capture_output=True, text=True, cwd=tmpdir,
        )
        output = result.stdout + result.stderr
        failed = output.count(" FAILED")
        killed = failed > 0

        return {
            "function": mutation["function"],
            "description": mutation["description"],
            "applied": True,
            "killed": killed,
            "tests_failed": failed,
        }


def main():
    parser = argparse.ArgumentParser(description="Experiment 11: Mutation Check")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 11: Mutation Check — Deliberate Breaks")
    print("=" * 65)
    print(f"Mutations: {len(MUTATIONS)}")
    print()
    print("--- REAL EXECUTION: actual code mutation + pytest ---")
    print()

    results = []
    killed = 0
    survived = 0

    for mut in MUTATIONS:
        r = apply_mutation_and_test(mut)
        results.append(r)
        if r["applied"]:
            status = "KILLED" if r["killed"] else "SURVIVED"
            if r["killed"]:
                killed += 1
            else:
                survived += 1
        else:
            status = "SKIPPED"
        print(f"  [{status:<8}] {r['function']:<16} {r['description']}")

    total = killed + survived
    kill_rate = killed / total if total > 0 else 0

    print()
    print(f"{'Metric':<30} {'Value':>10}")
    print("-" * 42)
    print(f"{'Total mutations':<30} {len(MUTATIONS):>10}")
    print(f"{'Applied':<30} {total:>10}")
    print(f"{'Killed (test caught)':<30} {killed:>10}")
    print(f"{'Survived (test missed)':<30} {survived:>10}")
    print(f"{'Kill rate':<30} {kill_rate:>9.0%}")
    print()

    if survived > 0:
        print("Surviving mutations indicate test blind spots.")
        print("An agent should be sent back to add tests for these cases.")
    else:
        print("All mutations killed — the test suite has good coverage of")
        print("the changed functions.")

    print()
    print("Conclusion: Mutation testing is a practical way to verify test")
    print("quality. The harness runs in seconds and catches weak test suites.")

    summary = {
        "experiment": "11_mutation_check",
        "simulated": False,
        "total_mutations": len(MUTATIONS),
        "applied": total,
        "killed": killed,
        "survived": survived,
        "kill_rate": round(kill_rate, 4),
        "details": results,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
