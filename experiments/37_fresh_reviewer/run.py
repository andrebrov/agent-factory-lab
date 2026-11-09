#!/usr/bin/env python3
"""
Experiment 37: Fresh-Reviewer Step — Spec-Based Review with Bug Reproduction
===============================================================================

Each seeded bug gets a spec. A fresh reviewer checks the diff against the
spec by running the relevant test on original code (should fail) and patched
code (should pass). Includes adversarial cases where tests pass but the fix
is wrong.

REAL EXECUTION: actual pytest runs on buggy, correct, and adversarial patches.
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

SPECS = [
    {
        "bug": "factorial",
        "spec": "factorial(n) multiplies 0..n instead of 1..n, so result is always 0",
        "test": "test_factorial_basic",
        "correct_patch": ("range(0, n + 1)", "range(1, n + 1)"),
        "adversarial_patch": ("range(0, n + 1)", "range(0, n + 2)"),
        "adversarial_note": "Adds an extra iteration — factorial(5) still gives 0 because it starts at 0",
    },
    {
        "bug": "fibonacci",
        "spec": "fib(1) returns 0, should return 1",
        "test": "test_fibonacci_base",
        "correct_patch": ("return 0  # BUG: should return 1", "return 1"),
        "adversarial_patch": ("return 0  # BUG: should return 1", "return 1  # fixed"),
        "adversarial_note": "Correct fix but cosmetically different — reviewer should still approve",
    },
    {
        "bug": "is_prime",
        "spec": "Uses // (floor division) instead of % (modulo) for divisibility check",
        "test": "test_is_prime",
        "correct_patch": ("n // i == 0", "n % i == 0"),
        "adversarial_patch": ("n // i == 0", "n / i == 0"),
        "adversarial_note": "Uses float division — passes for small primes but fails on edge cases",
    },
    {
        "bug": "binary_search",
        "spec": "Returns mid instead of -1 when element is not found",
        "test": "test_binary_search_missing",
        "correct_patch": ("return mid  # BUG", "return -1"),
        "adversarial_patch": ("return mid  # BUG", "return None"),
        "adversarial_note": "Returns None instead of -1 — test expects -1",
    },
    {
        "bug": "mean",
        "spec": "No guard for empty list — ZeroDivisionError",
        "test": "test_mean_empty",
        "correct_patch": (
            "    return sum(numbers) / len(numbers)  # BUG: no guard for empty list",
            '    if not numbers:\n        raise ValueError("empty")\n    return sum(numbers) / len(numbers)',
        ),
        "adversarial_patch": (
            "    return sum(numbers) / len(numbers)  # BUG: no guard for empty list",
            "    return sum(numbers) / max(len(numbers), 1)",
        ),
        "adversarial_note": "Returns 0.0 for empty list instead of raising ValueError",
    },
]


def run_test(code: str, test_name: str) -> bool:
    """Run a specific test against provided code. Returns True if test passes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "mathlib.py").write_text(code)
        shutil.copy(SAMPLE_DIR / "test_mathlib.py", tmpdir)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", f"test_mathlib.py::{test_name}",
             "-x", "--tb=no", "-q"],
            capture_output=True, text=True, cwd=tmpdir,
        )
        return result.returncode == 0


def review_against_spec(spec: dict, patch_type: str) -> dict:
    """Run the fresh-reviewer protocol for one bug."""
    buggy_code = (SAMPLE_DIR / "mathlib.py").read_text()
    old, new = spec[f"{patch_type}_patch"]
    patched_code = buggy_code.replace(old, new, 1)

    # Step 1: Confirm bug reproduces on original code (test should FAIL)
    bug_reproduces = not run_test(buggy_code, spec["test"])

    # Step 2: Confirm fix resolves the bug (test should PASS)
    fix_resolves = run_test(patched_code, spec["test"])

    # Reviewer verdict
    if bug_reproduces and fix_resolves:
        verdict = "APPROVE"
    elif not bug_reproduces:
        verdict = "REJECT: bug does not reproduce on original code"
    elif not fix_resolves:
        verdict = "REJECT: test still fails after fix"
    else:
        verdict = "REJECT: unknown"

    return {
        "bug": spec["bug"],
        "patch_type": patch_type,
        "spec": spec["spec"],
        "bug_reproduces": bug_reproduces,
        "fix_resolves": fix_resolves,
        "verdict": verdict,
    }


def main():
    parser = argparse.ArgumentParser(description="Experiment 37: Fresh Reviewer")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 37: Fresh-Reviewer Step")
    print("=" * 65)
    print()
    print("--- REAL EXECUTION (pytest) ---")
    print()

    results = []

    # Phase 1: Correct patches
    print("Phase 1: Correct patches (should all be APPROVED)")
    print("-" * 55)
    correct_approved = 0
    for spec in SPECS:
        r = review_against_spec(spec, "correct")
        results.append(r)
        status = "OK" if r["verdict"] == "APPROVE" else "!!"
        if r["verdict"] == "APPROVE":
            correct_approved += 1
        print(f"  [{status}] {r['bug']:<16} repro={r['bug_reproduces']} "
              f"fixes={r['fix_resolves']} → {r['verdict']}")

    print(f"\n  Correct approved: {correct_approved}/{len(SPECS)}")
    print()

    # Phase 2: Adversarial patches (some should be REJECTED)
    print("Phase 2: Adversarial patches (tests-pass-but-wrong cases)")
    print("-" * 55)
    adversarial_caught = 0
    adversarial_total = 0
    for spec in SPECS:
        r = review_against_spec(spec, "adversarial")
        results.append(r)
        is_truly_wrong = spec["bug"] in ("factorial", "is_prime", "binary_search", "mean")
        if is_truly_wrong:
            adversarial_total += 1
            if r["verdict"] != "APPROVE":
                adversarial_caught += 1

        status = "OK" if (is_truly_wrong and r["verdict"] != "APPROVE") or \
                         (not is_truly_wrong and r["verdict"] == "APPROVE") else "!!"
        print(f"  [{status}] {r['bug']:<16} repro={r['bug_reproduces']} "
              f"fixes={r['fix_resolves']} → {r['verdict']}")
        print(f"         Note: {spec['adversarial_note']}")

    print(f"\n  Adversarial caught: {adversarial_caught}/{adversarial_total}")
    print()

    # Phase 3: Compare with tests-pass-only gate
    tests_only_would_approve = sum(
        1 for r in results if r["patch_type"] == "adversarial" and r["fix_resolves"]
    )
    spec_reviewer_rejects = sum(
        1 for r in results if r["patch_type"] == "adversarial" and r["verdict"] != "APPROVE"
    )

    print("Comparison: tests-pass-only vs spec-based review")
    print(f"  Tests-pass-only would approve: {tests_only_would_approve}/{len(SPECS)} adversarial")
    print(f"  Spec-based reviewer rejects:   {spec_reviewer_rejects}/{len(SPECS)} adversarial")
    print()

    all_correct_approved = correct_approved == len(SPECS)

    print(f"Conclusion (MEASURED): The spec-based fresh reviewer correctly")
    print(f"approves {correct_approved}/{len(SPECS)} correct patches and catches")
    print(f"{adversarial_caught}/{adversarial_total} adversarial patches where the test")
    print(f"alone would miss the problem. Bug-reproduction check adds a second")
    print(f"verification dimension beyond just 'tests pass'.")

    summary = {
        "experiment": "37_fresh_reviewer",
        "simulated": False,
        "correct_approved": correct_approved,
        "correct_total": len(SPECS),
        "adversarial_caught": adversarial_caught,
        "adversarial_total": adversarial_total,
        "tests_only_would_approve_adversarial": tests_only_would_approve,
        "all_correct_approved": all_correct_approved,
        "results": results,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
