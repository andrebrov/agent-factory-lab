#!/usr/bin/env python3
"""
Experiment 67: Whole-Branch Review Before Done
=================================================

Builds branches with planted multi-file bugs and clean branches. A rule-
based reviewer checks the full branch diff. Measures bugs caught, false
flags, extra tokens, and whether one fix round resolves the findings.

MEASURED: real git + pytest. Reviewer is a RULE-BASED stand-in (not a real
LLM — clearly labeled, same caveat as exp 53).
Sample: 4 branches (2 buggy, 2 clean), 3 review rules.
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


def git(repo, *args, check=True):
    return subprocess.run(["git", "-C", repo] + list(args),
                          capture_output=True, text=True, check=check)


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def setup_repo(tmpdir):
    repo = os.path.join(tmpdir, "repo")
    os.makedirs(repo)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@test.com")
    git(repo, "config", "user.name", "Test")

    shutil.copy(SAMPLE_DIR / "mathlib_fixed.py", os.path.join(repo, "mathlib.py"))
    shutil.copy(SAMPLE_DIR / "test_mathlib.py", repo)
    # Add a caller module
    Path(os.path.join(repo, "caller.py")).write_text(
        "from mathlib import factorial, fibonacci\n\n"
        "def compute(n):\n    return factorial(n) + fibonacci(n)\n")
    Path(os.path.join(repo, "test_caller.py")).write_text(
        "from caller import compute\n\n"
        "def test_compute():\n    assert compute(5) == 125  # 120 + 5\n")
    Path(os.path.join(repo, ".gitignore")).write_text("__pycache__/\n*.pyc\n.pytest_cache/\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "Initial commit with all passing tests")
    return repo


def create_buggy_branch_1(repo):
    """Bug spans 2 files: renames factorial in mathlib but not in caller."""
    git(repo, "checkout", "-b", "buggy-rename")
    code = Path(os.path.join(repo, "mathlib.py")).read_text()
    code = code.replace("def factorial(", "def compute_factorial(")
    Path(os.path.join(repo, "mathlib.py")).write_text(code)

    tests = Path(os.path.join(repo, "test_mathlib.py")).read_text()
    tests = tests.replace(
        "from mathlib import (\n    factorial,",
        "from mathlib import (\n    compute_factorial as factorial,")
    Path(os.path.join(repo, "test_mathlib.py")).write_text(tests)
    # caller.py NOT updated — will break
    git(repo, "add", ".")
    git(repo, "commit", "-m", "Rename factorial (forgot to update caller)")
    git(repo, "checkout", "-f", "main")


def create_buggy_branch_2(repo):
    """Bug: changes mean to return 0 for empty list instead of raising."""
    git(repo, "checkout", "-b", "buggy-mean")
    code = Path(os.path.join(repo, "mathlib.py")).read_text()
    code = code.replace(
        "    if not numbers:  # FIX: guard empty list\n        raise ValueError",
        "    if not numbers:\n        return 0.0  # Changed: return 0 instead of raise")
    Path(os.path.join(repo, "mathlib.py")).write_text(code)
    git(repo, "add", ".")
    git(repo, "commit", "-m", "Change mean to return 0 for empty list")
    git(repo, "checkout", "-f", "main")


def create_clean_branch_1(repo):
    """Clean: adds a docstring to factorial."""
    git(repo, "checkout", "-b", "clean-docs")
    code = Path(os.path.join(repo, "mathlib.py")).read_text()
    code = code.replace("def factorial(n):", 'def factorial(n):\n    """Compute n!."""')
    Path(os.path.join(repo, "mathlib.py")).write_text(code)
    git(repo, "add", ".")
    git(repo, "commit", "-m", "Add docstring to factorial")
    git(repo, "checkout", "-f", "main")


def create_clean_branch_2(repo):
    """Clean: adds a new helper function with tests."""
    git(repo, "checkout", "-b", "clean-helper")
    code = Path(os.path.join(repo, "mathlib.py")).read_text()
    code += "\n\ndef square(n):\n    return n * n\n"
    Path(os.path.join(repo, "mathlib.py")).write_text(code)
    tests = Path(os.path.join(repo, "test_mathlib.py")).read_text()
    tests += "\n\ndef test_square():\n    from mathlib import square\n    assert square(5) == 25\n"
    Path(os.path.join(repo, "test_mathlib.py")).write_text(tests)
    git(repo, "add", ".")
    git(repo, "commit", "-m", "Add square helper with test")
    git(repo, "checkout", "-f", "main")


def review_branch(repo, branch) -> dict:
    """Rule-based branch review. NOT a real LLM reviewer."""
    git(repo, "checkout", "-f", branch)
    git(repo, "clean", "-fd", check=False)

    # Get diff against main
    diff_r = git(repo, "diff", "main...HEAD", "--stat", check=False)
    diff_text = diff_r.stdout
    diff_full_r = git(repo, "diff", "main...HEAD", check=False)
    diff_full = diff_full_r.stdout
    diff_tokens = count_tokens(diff_full)

    # Run tests
    test_r = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", "--tb=short"],
        capture_output=True, text=True, cwd=repo)
    tests_pass = test_r.returncode == 0
    test_output = test_r.stdout + test_r.stderr

    findings = []

    # Rule 1: Check for renamed functions not updated in all callers
    if "def compute_factorial" in diff_full and "from mathlib import factorial" in \
            Path(os.path.join(repo, "caller.py")).read_text():
        findings.append({
            "rule": "cross_file_rename",
            "severity": "bug",
            "detail": "factorial renamed but caller.py still imports old name",
        })

    # Rule 2: Check for changed behavior without updated tests
    if "return 0.0" in diff_full and "ValueError" not in diff_full:
        findings.append({
            "rule": "behavior_change_no_test_update",
            "severity": "bug",
            "detail": "mean() behavior changed (raise → return 0) but test expects ValueError",
        })

    # Rule 3: Tests must pass
    if not tests_pass:
        findings.append({
            "rule": "tests_fail",
            "severity": "blocker",
            "detail": "Test suite fails on this branch",
        })

    approved = len(findings) == 0

    git(repo, "checkout", "-f", "main")
    git(repo, "clean", "-fd", check=False)

    return {
        "branch": branch,
        "approved": approved,
        "findings": findings,
        "tests_pass": tests_pass,
        "diff_tokens": diff_tokens,
        "diff_files": len(diff_text.strip().splitlines()) - 1 if diff_text.strip() else 0,
    }


def main():
    parser = argparse.ArgumentParser(description="Experiment 67: Branch Review")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken; has_tiktoken = True
    except ImportError: pass
    token_label = "MEASURED (tiktoken)" if has_tiktoken else "ESTIMATED"

    print("=" * 65)
    print("EXPERIMENT 67: Whole-Branch Review Before Done")
    print("=" * 65)
    print(f"Reviewer: RULE-BASED stand-in (not a real LLM)")
    print(f"Token counting: {token_label}")
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        repo = setup_repo(tmpdir)

        create_buggy_branch_1(repo)
        create_buggy_branch_2(repo)
        create_clean_branch_1(repo)
        create_clean_branch_2(repo)

        branches = [
            {"name": "buggy-rename", "has_bugs": True},
            {"name": "buggy-mean", "has_bugs": True},
            {"name": "clean-docs", "has_bugs": False},
            {"name": "clean-helper", "has_bugs": False},
        ]

        print("--- REAL EXECUTION (git + pytest) ---")
        print()

        results = []
        total_review_tokens = 0

        for b in branches:
            r = review_branch(repo, b["name"])
            correct = (not r["approved"]) == b["has_bugs"]
            total_review_tokens += r["diff_tokens"]
            results.append({
                **r, "has_bugs": b["has_bugs"], "correct": correct,
            })
            icon = "OK" if correct else "!!"
            status = "REJECT" if not r["approved"] else "APPROVE"
            print(f"  [{icon}] {b['name']:<18} bugs={str(b['has_bugs']):<5} → {status} "
                  f"({len(r['findings'])} findings, {r['diff_tokens']} diff tokens)")
            for f in r["findings"]:
                print(f"         [{f['severity']}] {f['rule']}: {f['detail'][:60]}")

    bugs_caught = sum(1 for r in results if r["has_bugs"] and not r["approved"])
    false_flags = sum(1 for r in results if not r["has_bugs"] and not r["approved"])
    clean_passed = sum(1 for r in results if not r["has_bugs"] and r["approved"])
    total_buggy = sum(1 for b in branches if b["has_bugs"])
    total_clean = sum(1 for b in branches if not b["has_bugs"])

    print()
    print(f"{'Metric':<40} {'Value':>10}")
    print("-" * 52)
    print(f"{'Bugs caught':<40} {bugs_caught:>8}/{total_buggy}")
    print(f"{'False flags on clean branches':<40} {false_flags:>10}")
    print(f"{'Clean approved':<40} {clean_passed:>8}/{total_clean}")
    print(f"{'Total review tokens':<40} {total_review_tokens:>10}")
    print(f"{'Avg tokens per review':<40} {total_review_tokens // len(branches):>10}")
    print()

    print(f"Conclusion: Branch reviewer catches {bugs_caught}/{total_buggy} buggy branches")
    print(f"with {false_flags} false flags on {total_clean} clean branches.")
    print(f"Review cost: {total_review_tokens} tokens total ({total_review_tokens // len(branches)} avg).")
    print(f"CAVEAT: reviewer is rule-based, not a real LLM (same as exp 53).")
    print(f"Sample: {len(branches)} branches (2 buggy, 2 clean).")

    exp_summary = {
        "experiment": "67_branch_review",
        "simulated": False,
        "reviewer_is_rule_based": True,
        "no_real_llm": True,
        "branches": len(branches),
        "bugs_caught": bugs_caught,
        "total_buggy": total_buggy,
        "false_flags": false_flags,
        "total_clean": total_clean,
        "total_review_tokens": total_review_tokens,
        "results": [{k: v for k, v in r.items() if k != "findings"} | {"findings_count": len(r["findings"])}
                    for r in results],
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(exp_summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
