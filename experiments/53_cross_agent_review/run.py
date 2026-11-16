#!/usr/bin/env python3
"""
Experiment 53: Cross-Agent Review Gate (herdr-style)
======================================================

Writer produces a patch. A second-model reviewer checks it by running the
targeted test on original code (bug must reproduce) and patched code (fix
must work). No real LLM calls — the reviewer is a deterministic test gate.

MIXED: pytest execution is MEASURED; agent decision-making is SIMULATED
(deterministic gate standing in for a real reviewer model).
Sample: 5 bugs × 2 fix types (correct + adversarial) = 10 scenarios.
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

BUGS = [
    {"name": "factorial", "correct": ("range(0, n + 1)", "range(1, n + 1)"),
     "adversarial": ("range(0, n + 1)", "range(0, n + 2)"), "test": "test_factorial_basic"},
    {"name": "fibonacci", "correct": ("return 0  # BUG: should return 1", "return 1"),
     "adversarial": ("return 0  # BUG: should return 1", "return 2"), "test": "test_fibonacci_base"},
    {"name": "is_prime", "correct": ("n // i == 0", "n % i == 0"),
     "adversarial": ("n // i == 0", "n / i == 0"), "test": "test_is_prime"},
    {"name": "binary_search", "correct": ("return mid  # BUG", "return -1"),
     "adversarial": ("return mid  # BUG", "return None"), "test": "test_binary_search_missing"},
    {"name": "mean",
     "correct": ("    return sum(numbers) / len(numbers)  # BUG: no guard for empty list",
                 '    if not numbers:\n        raise ValueError("empty")\n    return sum(numbers) / len(numbers)'),
     "adversarial": ("    return sum(numbers) / len(numbers)  # BUG: no guard for empty list",
                     "    return sum(numbers) / max(len(numbers), 1)"),
     "test": "test_mean_empty"},
]

WRITER_TOKENS = 2500
REVIEWER_TOKENS = 1500


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def run_test(code: str, test_name: str) -> bool:
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "mathlib.py").write_text(code)
        shutil.copy(SAMPLE_DIR / "test_mathlib.py", d)
        r = subprocess.run(
            [sys.executable, "-m", "pytest", f"test_mathlib.py::{test_name}",
             "-x", "--tb=no", "-q"],
            capture_output=True, text=True, cwd=d)
        return r.returncode == 0


def review_patch(bug: dict, fix_type: str) -> dict:
    buggy = (SAMPLE_DIR / "mathlib.py").read_text()
    old, new = bug[fix_type]
    patched = buggy.replace(old, new, 1)

    bug_reproduces = not run_test(buggy, bug["test"])
    fix_works = run_test(patched, bug["test"])

    findings = []
    if not bug_reproduces:
        findings.append("Bug does not reproduce on original code")
    if not fix_works:
        findings.append("Test still fails after fix")

    approved = bug_reproduces and fix_works
    return {
        "bug": bug["name"], "fix_type": fix_type,
        "bug_reproduces": bug_reproduces, "fix_works": fix_works,
        "approved": approved, "findings": findings,
    }


def main():
    parser = argparse.ArgumentParser(description="Experiment 53: Cross-Agent Review")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken; has_tiktoken = True
    except ImportError: pass
    token_label = "MEASURED (tiktoken)" if has_tiktoken else "ESTIMATED"

    print("=" * 65)
    print("EXPERIMENT 53: Cross-Agent Review Gate (herdr-style)")
    print("=" * 65)
    print(f"Sample: {len(BUGS)} bugs × 2 fix types = {len(BUGS)*2} scenarios")
    print(f"Reviewer: deterministic test gate (no real LLM calls)")
    print()

    results = []

    # Writer-alone baseline (trusts its own work)
    print("Mode A: Writer alone (no review)")
    print("-" * 45)
    writer_correct_shipped = 0
    writer_bad_shipped = 0
    for bug in BUGS:
        for fix_type in ["correct", "adversarial"]:
            buggy = (SAMPLE_DIR / "mathlib.py").read_text()
            old, new = bug[fix_type]
            patched = buggy.replace(old, new, 1)
            test_passes = run_test(patched, bug["test"])
            if fix_type == "correct":
                if test_passes: writer_correct_shipped += 1
            else:
                if test_passes: writer_bad_shipped += 1
            status = "ship" if test_passes else "fail"
            print(f"  {bug['name']:<16} {fix_type:<12} → {status}")

    print(f"\n  Correct shipped: {writer_correct_shipped}/{len(BUGS)}")
    print(f"  Adversarial shipped: {writer_bad_shipped}/{len(BUGS)}")
    print()

    # Writer + Reviewer
    print("Mode B: Writer + Reviewer (cross-agent gate)")
    print("-" * 45)
    review_correct_approved = 0
    review_adv_caught = 0
    review_false_findings = 0
    review_results = []

    for bug in BUGS:
        for fix_type in ["correct", "adversarial"]:
            r = review_patch(bug, fix_type)
            review_results.append(r)
            if fix_type == "correct":
                if r["approved"]:
                    review_correct_approved += 1
                elif r["bug_reproduces"]:
                    review_false_findings += 1
            else:
                if not r["approved"]:
                    review_adv_caught += 1
            status = "APPROVE" if r["approved"] else "REJECT"
            print(f"  {bug['name']:<16} {fix_type:<12} → {status}"
                  + (f" ({'; '.join(r['findings'])})" if r["findings"] else ""))

    review_adv_total = len(BUGS)
    print(f"\n  Correct approved: {review_correct_approved}/{len(BUGS)}")
    print(f"  Adversarial caught: {review_adv_caught}/{review_adv_total}")
    print(f"  False findings on correct: {review_false_findings}")
    print()

    # Token cost comparison
    writer_only_tokens = WRITER_TOKENS * len(BUGS)
    writer_reviewer_tokens = (WRITER_TOKENS + REVIEWER_TOKENS) * len(BUGS)
    extra_tokens = writer_reviewer_tokens - writer_only_tokens
    extra_pct = extra_tokens / writer_only_tokens * 100

    print(f"Token cost (MODELED — {WRITER_TOKENS}/writer + {REVIEWER_TOKENS}/reviewer):")
    print(f"  Writer alone: {writer_only_tokens:,} tokens")
    print(f"  Writer+Reviewer: {writer_reviewer_tokens:,} tokens (+{extra_pct:.0f}%)")
    print()

    print(f"{'Metric':<35} {'Writer Only':>12} {'W+Reviewer':>12}")
    print("-" * 61)
    print(f"{'Correct fixes shipped/approved':<35} {writer_correct_shipped:>10}/{len(BUGS)} "
          f"{review_correct_approved:>10}/{len(BUGS)}")
    print(f"{'Adversarial fixes caught':<35} {'n/a':>12} "
          f"{review_adv_caught:>10}/{review_adv_total}")
    print(f"{'False findings':<35} {0:>12} {review_false_findings:>12}")
    print(f"{'Token overhead':<35} {'baseline':>12} {f'+{extra_pct:.0f}%':>12}")
    print()

    print(f"Conclusion: The cross-agent reviewer catches {review_adv_caught}/{review_adv_total}")
    print(f"adversarial patches at +{extra_pct:.0f}% token cost. {review_false_findings} false")
    print(f"finding(s) on correct patches. The reviewer is a deterministic test")
    print(f"gate, not a real LLM — actual reviewer quality depends on the model.")

    summary = {
        "experiment": "53_cross_agent_review",
        "simulated": True,
        "reviewer_is_deterministic_gate": True,
        "no_real_llm_calls": True,
        "bugs_tested": len(BUGS),
        "writer_correct_shipped": writer_correct_shipped,
        "writer_bad_shipped": writer_bad_shipped,
        "review_correct_approved": review_correct_approved,
        "review_adv_caught": review_adv_caught,
        "review_false_findings": review_false_findings,
        "token_overhead_pct": round(extra_pct, 1),
        "writer_tokens_modeled": WRITER_TOKENS,
        "reviewer_tokens_modeled": REVIEWER_TOKENS,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
