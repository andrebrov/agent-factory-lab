#!/usr/bin/env python3
"""
Experiment 88: Different Model as Reviewer — Process Rule Test
=================================================================

Rex not available. No second real model. No API keys.

Tests the PROCESS RULE only: does the task stay open until a review
step runs and passes? The review itself is a deterministic test gate
(same as exp 74's regression gate), NOT a real model review.

NO CLAIM about whether a second model catches more bugs. That would
require two real models, which we don't have.

MEASURED: process rule enforcement on 5 task scenarios.
Sample: 5 scenarios (3 should block until review, 2 should pass through).
"""
import json, os, sys, subprocess, shutil, tempfile, argparse
from pathlib import Path

SAMPLE_DIR = Path(__file__).parent.parent / "sample_codebase"


def git(repo, *args, check=True):
    return subprocess.run(["git", "-C", repo] + list(args),
                          capture_output=True, text=True, check=check)


def run_test_gate(repo_dir) -> dict:
    """Deterministic test gate (NOT a model review)."""
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", "--tb=no"],
        capture_output=True, text=True, cwd=repo_dir)
    passed = r.stdout.count(" PASSED")
    failed = r.stdout.count(" FAILED")
    return {"passed": passed, "failed": failed, "gate_passes": r.returncode == 0}


SCENARIOS = [
    {"name": "good_fix", "desc": "Fix applied, tests pass",
     "modify": lambda code: code,  # keep fixed code
     "expected_done": True},
    {"name": "broken_fix", "desc": "Fix breaks a test",
     "modify": lambda code: code.replace("range(1, n + 1)", "range(0, n + 1)"),
     "expected_done": False},
    {"name": "incomplete_fix", "desc": "Only partial fix applied",
     "modify": lambda code: code.replace("return 1  # FIX: return 1", "return 0"),
     "expected_done": False},
    {"name": "extra_function", "desc": "New function added, all tests pass",
     "modify": lambda code: code + "\ndef bonus(): return 42\n",
     "expected_done": True},
    {"name": "no_change", "desc": "No code changed, tests pass",
     "modify": lambda code: code,
     "expected_done": True},
]


class SimplifyThenReviewProcess:
    """Process rule: task stays open until review gate passes.
    The 'simplify' step is stubbed (would need a real model).
    The 'review' step is a deterministic test gate."""

    def __init__(self):
        self.state = "writing"

    def submit_for_review(self, repo_dir) -> dict:
        """Transition: writing → review. Run the gate."""
        self.state = "review"
        # Simplify step: STUBBED (would need a real model to simplify code)
        # We skip it and go straight to the test gate
        gate = run_test_gate(repo_dir)

        if gate["gate_passes"]:
            self.state = "done"
            return {"verdict": "done", "gate": gate,
                    "note": "Review gate (deterministic test, not model) passed"}
        else:
            self.state = "writing"  # sent back to writer
            return {"verdict": "sent_back", "gate": gate,
                    "note": f"Review gate failed: {gate['failed']} test(s) fail"}

    def is_done(self):
        return self.state == "done"


def main():
    parser = argparse.ArgumentParser(description="Experiment 88: Different Reviewer")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 88: Different Model as Reviewer — Process Rule")
    print("=" * 65)
    print("Rex not available. No second real model. No API keys.")
    print("Tests the PROCESS RULE only (task stays open until gate passes).")
    print("The review is a DETERMINISTIC TEST GATE, not a real model review.")
    print("NO CLAIM about whether a second model catches more bugs.")
    print()
    print("--- MEASURED (process rule + real pytest) ---")
    print()

    results = []

    for scenario in SCENARIOS:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = os.path.join(tmpdir, "repo")
            os.makedirs(repo)
            shutil.copy(SAMPLE_DIR / "mathlib_fixed.py", os.path.join(repo, "mathlib.py"))
            shutil.copy(SAMPLE_DIR / "test_mathlib.py", repo)

            # Apply scenario modification
            code = Path(os.path.join(repo, "mathlib.py")).read_text()
            modified = scenario["modify"](code)
            Path(os.path.join(repo, "mathlib.py")).write_text(modified)

            # Run the process
            process = SimplifyThenReviewProcess()
            result = process.submit_for_review(repo)

            is_done = process.is_done()
            correct = is_done == scenario["expected_done"]

            results.append({
                "name": scenario["name"],
                "desc": scenario["desc"],
                "expected_done": scenario["expected_done"],
                "actual_done": is_done,
                "correct": correct,
                "verdict": result["verdict"],
                "tests_passed": result["gate"]["passed"],
                "tests_failed": result["gate"]["failed"],
            })

            icon = "OK" if correct else "!!"
            print(f"  [{icon}] {scenario['name']:<18} expected_done={scenario['expected_done']:<5} "
                  f"actual_done={is_done:<5} P={result['gate']['passed']} F={result['gate']['failed']}")

    correct_count = sum(1 for r in results if r["correct"])
    total = len(results)

    blocked_correctly = sum(1 for r in results
                            if not r["expected_done"] and not r["actual_done"])
    passed_correctly = sum(1 for r in results
                           if r["expected_done"] and r["actual_done"])
    false_blocks = sum(1 for r in results
                       if r["expected_done"] and not r["actual_done"])
    false_passes = sum(1 for r in results
                       if not r["expected_done"] and r["actual_done"])

    print()
    print(f"{'Metric':<40} {'Value':>10}")
    print("-" * 52)
    print(f"{'Process rule correct':<40} {correct_count:>8}/{total}")
    print(f"{'Blocked until fix (correctly)':<40} {blocked_correctly:>10}")
    print(f"{'Passed through (correctly)':<40} {passed_correctly:>10}")
    print(f"{'False blocks':<40} {false_blocks:>10}")
    print(f"{'False passes':<40} {false_passes:>10}")
    print(f"{'Simplify step':<40} {'STUBBED':>10}")
    print(f"{'Review step':<40} {'test gate':>10}")
    print()

    print(f"Conclusion: The process rule correctly blocks {blocked_correctly}")
    print(f"incomplete tasks and passes {passed_correctly} complete ones ({correct_count}/{total}).")
    print(f"The review is a DETERMINISTIC TEST GATE, not a real model.")
    print(f"The simplify step is STUBBED (needs a real model).")
    print(f"NO CLAIM about whether a second model catches more bugs.")
    print(f"Sample: {total} scenarios.")

    summary = {
        "experiment": "88_different_reviewer",
        "simulated": False,
        "process_rule_tested": True,
        "review_is_test_gate": True,
        "simplify_stubbed": True,
        "no_real_model_review": True,
        "no_rex": True,
        "correct": correct_count,
        "total": total,
        "blocked_correctly": blocked_correctly,
        "passed_correctly": passed_correctly,
        "false_blocks": false_blocks,
        "false_passes": false_passes,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
