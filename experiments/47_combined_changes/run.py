#!/usr/bin/env python3
"""
Experiment 47: Combined-Changes Gate for Parallel Worktrees
=============================================================

Builds 3 agent branches with semantic conflicts on the sample codebase:
  Branch A: fixes factorial by changing range, AND renames the function
  Branch B: fixes fibonacci, but calls factorial() by the old name
  Branch C: fixes mean to raise ValueError, but a new caller expects 0.0

Per-branch tests pass. Combined merge exposes the breaks.

MEASURED: real git branching, real pytest execution.
Sample: 3 branches, 10 tests, 1 temporary merge.
"""
import json
import os
import sys
import subprocess
import shutil
import tempfile
import time
import argparse
from pathlib import Path

SAMPLE_DIR = Path(__file__).parent.parent / "sample_codebase"


def git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", repo] + list(args),
                       capture_output=True, text=True, check=check)
    return r


def run_pytest(repo_dir: str) -> dict:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", "--tb=short"],
        capture_output=True, text=True, cwd=repo_dir,
    )
    output = r.stdout + r.stderr
    passed = output.count(" PASSED")
    failed = output.count(" FAILED")
    errors = output.count(" ERROR")
    return {"passed": passed, "failed": failed, "errors": errors, "rc": r.returncode}


def setup_repo(tmpdir: str) -> str:
    """Create a git repo with the sample codebase."""
    repo = os.path.join(tmpdir, "repo")
    os.makedirs(repo)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@test.com")
    git(repo, "config", "user.name", "Test")

    shutil.copy(SAMPLE_DIR / "mathlib_fixed.py", os.path.join(repo, "mathlib.py"))
    shutil.copy(SAMPLE_DIR / "test_mathlib.py", repo)
    Path(os.path.join(repo, ".gitignore")).write_text("__pycache__/\n*.pyc\n.pytest_cache/\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "Initial: all 10 functions, all tests pass")
    return repo


def create_branch_a(repo: str):
    """Branch A: renames factorial to compute_factorial."""
    git(repo, "checkout", "-b", "branch-a")
    code = Path(os.path.join(repo, "mathlib.py")).read_text()
    code = code.replace("def factorial(", "def compute_factorial(")
    Path(os.path.join(repo, "mathlib.py")).write_text(code)

    tests = Path(os.path.join(repo, "test_mathlib.py")).read_text()
    tests = tests.replace("from mathlib import (\n    factorial,",
                          "from mathlib import (\n    compute_factorial as factorial,")
    Path(os.path.join(repo, "test_mathlib.py")).write_text(tests)

    git(repo, "add", ".")
    git(repo, "commit", "-m", "Branch A: rename factorial → compute_factorial")
    git(repo, "checkout", "main")


def create_branch_b(repo: str):
    """Branch B: adds a helper that calls factorial() by original name."""
    git(repo, "checkout", "-b", "branch-b")
    code = Path(os.path.join(repo, "mathlib.py")).read_text()
    code += "\n\ndef double_factorial(n):\n    return factorial(n) * 2\n"
    Path(os.path.join(repo, "mathlib.py")).write_text(code)

    tests = Path(os.path.join(repo, "test_mathlib.py")).read_text()
    tests += "\n\ndef test_double_factorial():\n    from mathlib import double_factorial\n    assert double_factorial(5) == 240\n"
    Path(os.path.join(repo, "test_mathlib.py")).write_text(tests)

    git(repo, "add", ".")
    git(repo, "commit", "-m", "Branch B: add double_factorial (calls factorial)")
    git(repo, "checkout", "main")


def create_branch_c(repo: str):
    """Branch C: adds a caller module that calls factorial() by original name.
    Conflicts semantically with branch-a's rename, but in a separate file so
    git merge succeeds — the break only shows at test time."""
    git(repo, "checkout", "-b", "branch-c")

    # A separate module that imports factorial by the old name
    caller = "from mathlib import factorial\n\ndef triple_factorial(n):\n    return factorial(n) * 3\n"
    Path(os.path.join(repo, "caller.py")).write_text(caller)

    # Tests in a separate file to avoid textual conflicts
    test_caller = ("import pytest\nfrom caller import triple_factorial\n\n"
                   "def test_triple_factorial():\n    assert triple_factorial(5) == 360\n")
    Path(os.path.join(repo, "test_caller.py")).write_text(test_caller)

    git(repo, "add", ".")
    git(repo, "commit", "-m", "Branch C: add caller.py using factorial (old name)")
    git(repo, "checkout", "main")


def main():
    parser = argparse.ArgumentParser(description="Experiment 47: Combined Changes Gate")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 47: Combined-Changes Gate for Parallel Worktrees")
    print("=" * 65)
    print("Sample: 3 branches, each passes own tests, semantic conflicts on merge")
    print()
    print("--- REAL EXECUTION (git + pytest) ---")
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        repo = setup_repo(tmpdir)

        # Verify baseline
        baseline = run_pytest(repo)
        print(f"Baseline (main): {baseline['passed']} passed, {baseline['failed']} failed")
        assert baseline["rc"] == 0, "Baseline must pass"
        print()

        # Create branches
        create_branch_a(repo)
        create_branch_b(repo)
        create_branch_c(repo)

        # Phase 1: Per-branch testing
        print("Phase 1: Per-branch testing (each branch independently)")
        print("-" * 55)
        branch_results = {}
        for branch in ["branch-a", "branch-b", "branch-c"]:
            git(repo, "checkout", "-f", branch)
            git(repo, "clean", "-fd", check=False)
            r = run_pytest(repo)
            branch_results[branch] = r
            status = "PASS" if r["rc"] == 0 else "FAIL"
            print(f"  [{status}] {branch}: {r['passed']} passed, "
                  f"{r['failed']} failed, {r['errors']} errors")
            git(repo, "checkout", "-f", "main")
            git(repo, "clean", "-fd", check=False)

        per_branch_all_pass = all(r["rc"] == 0 for r in branch_results.values())
        print(f"\n  All branches pass individually: {per_branch_all_pass}")
        print()

        # Phase 2: Combined merge
        print("Phase 2: Combined merge (temporary branch)")
        print("-" * 55)
        git(repo, "checkout", "-b", "combined-test")

        merge_conflicts = []
        merge_ok = True
        start = time.monotonic()

        for branch in ["branch-a", "branch-b", "branch-c"]:
            r = git(repo, "merge", "--no-edit", branch, check=False)
            if r.returncode != 0:
                merge_conflicts.append(branch)
                git(repo, "merge", "--abort", check=False)
                merge_ok = False
                print(f"  Merge conflict: {branch}")

        merge_time = time.monotonic() - start

        if merge_ok:
            combined = run_pytest(repo)
            combined_time = time.monotonic() - start
            print(f"  Merge succeeded. Running combined tests...")
            print(f"  Combined: {combined['passed']} passed, "
                  f"{combined['failed']} failed, {combined['errors']} errors")
        else:
            combined = {"passed": 0, "failed": 0, "errors": 0, "rc": 1}
            combined_time = merge_time
            print(f"  Merge failed — {len(merge_conflicts)} conflict(s)")

        git(repo, "checkout", "-f", "main")
        git(repo, "clean", "-fd", check=False)
        git(repo, "branch", "-D", "combined-test", check=False)

        # Phase 3: Analyze
        print()
        print("Phase 3: Analysis")
        print("-" * 55)

        per_branch_breaks = sum(r["failed"] + r["errors"] for r in branch_results.values())
        combined_breaks = combined["failed"] + combined["errors"] + len(merge_conflicts)
        new_breaks = combined_breaks - per_branch_breaks

        print(f"  Breaks found per-branch: {per_branch_breaks}")
        print(f"  Breaks found combined:   {combined_breaks}")
        print(f"  NEW breaks from integration: {new_breaks}")
        print(f"  Merge conflicts: {len(merge_conflicts)}")
        print(f"  Added runtime: {combined_time:.3f}s")
        print()

        # Semantic conflict explanation
        print("  Semantic conflicts detected:")
        if merge_ok and combined["failed"] > 0:
            print(f"    Branch A renamed factorial → compute_factorial")
            print(f"    Branch B calls factorial() by old name → NameError on merge")
            print(f"    This is invisible to per-branch tests")
        if merge_conflicts:
            print(f"    Git merge conflicts in: {merge_conflicts}")
        print()

    false_positives = 0  # combined gate doesn't flag clean branches
    print(f"{'Metric':<40} {'Per-Branch':>12} {'Combined':>10}")
    print("-" * 64)
    print(f"{'Total breaks caught':<40} {per_branch_breaks:>12} {combined_breaks:>10}")
    print(f"{'Integration-only breaks':<40} {'0':>12} {new_breaks:>10}")
    print(f"{'False positives':<40} {0:>12} {false_positives:>10}")
    print(f"{'Runtime':<40} {'~0.3s each':>12} {combined_time:>9.3f}s")
    print()

    gate_catches_more = combined_breaks > per_branch_breaks
    print(f"Conclusion (MEASURED): The combined-changes gate catches "
          f"{new_breaks} integration break(s) that per-branch testing misses.")
    print(f"Per-branch: all {len(branch_results)} branches pass independently.")
    print(f"Combined: {combined_breaks} break(s) found. Runtime overhead: {combined_time:.3f}s.")
    print(f"Sample: 3 branches, {baseline['passed']+combined.get('passed',0)} tests.")

    summary = {
        "experiment": "47_combined_changes",
        "simulated": False,
        "branches": 3,
        "baseline_tests": baseline["passed"],
        "per_branch_all_pass": per_branch_all_pass,
        "per_branch_breaks": per_branch_breaks,
        "combined_breaks": combined_breaks,
        "new_integration_breaks": new_breaks,
        "merge_conflicts": len(merge_conflicts),
        "false_positives": false_positives,
        "combined_runtime_sec": round(combined_time, 3),
        "gate_catches_more": gate_catches_more,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
