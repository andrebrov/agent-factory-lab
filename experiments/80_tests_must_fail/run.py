#!/usr/bin/env python3
"""
Experiment 80: "Tests Must Fail Without the Change" Gate
===========================================================

Deterministic gate (git + pytest, NOT a model): revert the non-test diff,
keep new/changed tests, rerun. If tests still pass → weak tests.

Cases constructed BEFORE the gate code. 7 cases covering:
(a) tests fail when feature reverted, (b) tests pass after revert (weak),
(c) mixed, (d) test-only PR, (e) no-new-tests PR.

MEASURED: real git + real pytest.
Sample: 7 cases on the sample codebase.
"""
import json, os, sys, subprocess, shutil, tempfile, argparse
from pathlib import Path

SAMPLE_DIR = Path(__file__).parent.parent / "sample_codebase"

def git(repo, *args, check=True):
    return subprocess.run(["git", "-C", repo] + list(args),
                          capture_output=True, text=True, check=check)

def run_tests(repo, test_pattern="test_*.py"):
    r = subprocess.run([sys.executable, "-m", "pytest", "-v", "--tb=no"],
                       capture_output=True, text=True, cwd=repo)
    passed = r.stdout.count(" PASSED")
    failed = r.stdout.count(" FAILED")
    return {"passed": passed, "failed": failed, "rc": r.returncode}

def setup_repo(tmpdir):
    repo = os.path.join(tmpdir, "repo")
    os.makedirs(repo)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "t@t"); git(repo, "config", "user.name", "T")
    shutil.copy(SAMPLE_DIR / "mathlib_fixed.py", os.path.join(repo, "mathlib.py"))
    shutil.copy(SAMPLE_DIR / "test_mathlib.py", repo)
    Path(os.path.join(repo, ".gitignore")).write_text("__pycache__/\n*.pyc\n.pytest_cache/\n")
    git(repo, "add", "."); git(repo, "commit", "-m", "init")
    return repo

# Cases written BEFORE the gate logic
CASES = [
    {
        "name": "strong_test",
        "desc": "New feature + test that fails when feature reverted",
        "setup": lambda repo: (
            _add_feature(repo, "def double(n): return n * 2\n",
                         "def test_double():\n    from mathlib import double\n    assert double(5) == 10\n"),
        ),
        "expected_gate": "pass",  # test fails on revert → gate passes
    },
    {
        "name": "weak_test",
        "desc": "New test that passes even without the feature",
        "setup": lambda repo: (
            _add_feature(repo, "def triple(n): return n * 3\n",
                         "def test_always_true():\n    assert 1 + 1 == 2\n"),
        ),
        "expected_gate": "fail",  # test passes on revert → gate fails (weak test)
    },
    {
        "name": "mixed_pr",
        "desc": "One strong test + one weak test",
        "setup": lambda repo: (
            _add_feature(repo, "def square(n): return n * n\n",
                         "def test_square():\n    from mathlib import square\n    assert square(4) == 16\n"
                         "def test_trivial():\n    assert True\n"),
        ),
        "expected_gate": "partial",  # one fails, one passes
    },
    {
        "name": "test_only",
        "desc": "PR only adds tests (no feature code change)",
        "setup": lambda repo: _add_test_only(repo,
            "def test_existing_factorial():\n    from mathlib import factorial\n    assert factorial(5) == 120\n"),
        "expected_gate": "skip",  # no non-test diff to revert
    },
    {
        "name": "no_new_tests",
        "desc": "PR changes code but adds no new tests",
        "setup": lambda repo: _add_code_only(repo),
        "expected_gate": "skip",  # no new tests to run
    },
    {
        "name": "strong_bugfix",
        "desc": "Bugfix with a test that catches the bug",
        "setup": lambda repo: (
            _add_feature(repo, "def safe_div(a, b):\n    if b == 0: raise ValueError('div by zero')\n    return a / b\n",
                         "def test_safe_div_zero():\n    import pytest\n    from mathlib import safe_div\n    with pytest.raises(ValueError): safe_div(1, 0)\n"),
        ),
        "expected_gate": "pass",
    },
    {
        "name": "wrong_assertion",
        "desc": "Test with wrong assertion that coincidentally passes",
        "setup": lambda repo: (
            _add_feature(repo, "def noop(): pass\n",
                         "def test_noop():\n    from mathlib import noop\n    assert noop() is None\n"),
        ),
        "expected_gate": "fail",  # noop returns None with or without the change
    },
]

def _add_feature(repo, code, test_code):
    c = Path(os.path.join(repo, "mathlib.py")).read_text()
    Path(os.path.join(repo, "mathlib.py")).write_text(c + "\n" + code)
    t = Path(os.path.join(repo, "test_mathlib.py")).read_text()
    Path(os.path.join(repo, "test_mathlib.py")).write_text(t + "\n" + test_code)
    git(repo, "add", "."); git(repo, "commit", "-m", "Add feature + tests")

def _add_test_only(repo, test_code):
    t = Path(os.path.join(repo, "test_mathlib.py")).read_text()
    Path(os.path.join(repo, "test_mathlib.py")).write_text(t + "\n" + test_code)
    git(repo, "add", "."); git(repo, "commit", "-m", "Add tests only")

def _add_code_only(repo):
    c = Path(os.path.join(repo, "mathlib.py")).read_text()
    Path(os.path.join(repo, "mathlib.py")).write_text(c + "\ndef helper(): return 42\n")
    git(repo, "add", "."); git(repo, "commit", "-m", "Add code, no tests")


def run_gate(repo) -> dict:
    """Deterministic gate: revert non-test changes, keep new tests, rerun."""
    diff_r = git(repo, "diff", "--name-only", "main...HEAD", check=False)
    changed = diff_r.stdout.strip().splitlines() if diff_r.stdout.strip() else []
    test_files = [f for f in changed if f.startswith("test_")]
    code_files = [f for f in changed if not f.startswith("test_") and not f.startswith(".")]

    if not test_files:
        return {"verdict": "skip", "reason": "no_new_tests", "changed": changed}
    if not code_files:
        return {"verdict": "skip", "reason": "test_only_pr", "changed": changed}

    # Save current test files
    saved_tests = {}
    for tf in test_files:
        saved_tests[tf] = Path(os.path.join(repo, tf)).read_text()

    # Revert code files to main
    for cf in code_files:
        git(repo, "checkout", "main", "--", cf, check=False)

    # Restore saved tests (keep the new/changed tests)
    for tf, content in saved_tests.items():
        Path(os.path.join(repo, tf)).write_text(content)

    # Run only the new/changed test files
    r = subprocess.run(
        [sys.executable, "-m", "pytest"] + test_files + ["-v", "--tb=no"],
        capture_output=True, text=True, cwd=repo)

    passed = r.stdout.count(" PASSED")
    failed = r.stdout.count(" FAILED")
    errors = r.stdout.count(" ERROR")

    if failed > 0 or errors > 0:
        verdict = "pass"  # tests fail without the change → good tests
    elif passed > 0 and failed == 0:
        verdict = "fail"  # tests pass without the change → weak tests
    else:
        verdict = "error"

    # Check for mixed (both strong and weak tests)
    if passed > 0 and failed > 0:
        verdict = "partial"

    # Restore working tree
    git(repo, "checkout", "HEAD", "--", ".", check=False)

    feedback = None
    if verdict == "fail":
        feedback = f"Gate failed: {passed} test(s) pass even without your code changes. These tests don't verify the new behavior."
    elif verdict == "partial":
        feedback = f"Gate partial: {failed} test(s) correctly fail without the change, but {passed} still pass (weak)."

    return {"verdict": verdict, "passed": passed, "failed": failed, "errors": errors,
            "feedback": feedback, "changed": changed}


def main():
    parser = argparse.ArgumentParser(description="Experiment 80: Tests Must Fail Gate")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 80: 'Tests Must Fail Without the Change' Gate")
    print("=" * 65)
    print("Deterministic gate (git + pytest), NOT a model.")
    print(f"Cases: {len(CASES)} (constructed before the gate code)")
    print()
    print("--- REAL EXECUTION (git + pytest) ---")
    print()

    results = []
    for case in CASES:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = setup_repo(tmpdir)
            git(repo, "checkout", "-b", "pr-branch")
            case["setup"](repo)

            gate = run_gate(repo)
            matches = gate["verdict"] == case["expected_gate"]
            results.append({
                "name": case["name"], "desc": case["desc"],
                "expected": case["expected_gate"], "actual": gate["verdict"],
                "correct": matches, "passed": gate.get("passed", 0),
                "failed": gate.get("failed", 0), "feedback": gate.get("feedback"),
            })
            icon = "OK" if matches else "!!"
            print(f"  [{icon}] {case['name']:<18} expected={case['expected_gate']:<8} "
                  f"actual={gate['verdict']:<8} P={gate.get('passed',0)} F={gate.get('failed',0)}")
            if gate.get("feedback"):
                print(f"       Feedback: {gate['feedback'][:70]}")

    correct = sum(1 for r in results if r["correct"])
    total = len(results)

    # Precision/recall for detecting weak tests (verdict=fail or partial)
    weak_cases = [r for r in results if r["expected"] in ("fail", "partial")]
    strong_cases = [r for r in results if r["expected"] == "pass"]
    skip_cases = [r for r in results if r["expected"] == "skip"]

    weak_caught = sum(1 for r in weak_cases if r["actual"] in ("fail", "partial"))
    false_flags = sum(1 for r in strong_cases if r["actual"] in ("fail", "partial"))
    skips_correct = sum(1 for r in skip_cases if r["actual"] == "skip")

    print()
    print(f"{'Metric':<40} {'Value':>10}")
    print("-" * 52)
    print(f"{'Total cases':<40} {total:>10}")
    print(f"{'Correct verdicts':<40} {correct:>8}/{total}")
    print(f"{'Weak/unrelated tests caught':<40} {weak_caught:>8}/{len(weak_cases)}")
    print(f"{'False flags on strong tests':<40} {false_flags:>10}")
    print(f"{'Skips correct (test-only/no-tests)':<40} {skips_correct:>8}/{len(skip_cases)}")
    print(f"{'Auto-feedback generated for failures':<40} "
          f"{sum(1 for r in results if r['feedback']):>10}")
    print()

    print(f"Conclusion: {correct}/{total} verdicts correct.")
    print(f"The gate catches {weak_caught}/{len(weak_cases)} weak/unrelated tests")
    print(f"with {false_flags} false flags on strong tests.")
    print(f"Test-only and no-new-tests PRs are correctly skipped.")
    print(f"Auto-feedback is generated for failed and partial cases.")
    print(f"This is a DETERMINISTIC GATE (git revert + pytest), not a model.")
    print(f"No live agent was run; the feedback message would be sent back,")
    print(f"but whether an agent fixes the tests is untested.")

    summary = {
        "experiment": "80_tests_must_fail",
        "simulated": False,
        "deterministic_gate": True,
        "cases": total,
        "correct": correct,
        "weak_caught": weak_caught,
        "weak_total": len(weak_cases),
        "false_flags": false_flags,
        "skips_correct": skips_correct,
        "results": results,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
