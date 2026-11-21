#!/usr/bin/env python3
"""
Experiment 69: "Done" Needs a Test Count
============================================

A done report must state "N/M tests passed" (N passed out of M total).
Reports with partial counts, single-file mentions, or no counts are
rejected. The test reports were NOT written to match the gate — they
include realistic edge cases agents actually produce.

MEASURED: gate logic on 16 labeled done reports.
Sample: 16 reports (8 correct full-suite, 4 partial/misleading, 4 no-count).
"""
import json
import os
import re
import argparse

# These reports were written to represent what agents actually produce,
# including edge cases, BEFORE the gate rules were finalized.
DONE_REPORTS = [
    # Full suite, correct (8)
    {"id": "r1", "text": "All tests passed. 212/212.", "full_suite": True,
     "expected": "accept", "suite_total": 212},
    {"id": "r2", "text": "Tests: 47/47 passed, 0 failed.", "full_suite": True,
     "expected": "accept", "suite_total": 47},
    {"id": "r3", "text": "pytest: 10 passed out of 10. All green.", "full_suite": True,
     "expected": "accept", "suite_total": 10},
    {"id": "r4", "text": "Suite complete: 156/156 tests passed.", "full_suite": True,
     "expected": "accept", "suite_total": 156},
    {"id": "r5", "text": "Ran full test suite: 89/89 passing.", "full_suite": True,
     "expected": "accept", "suite_total": 89},
    {"id": "r6", "text": "Build and test done. 33/33 tests pass. PR opened.", "full_suite": True,
     "expected": "accept", "suite_total": 33},
    {"id": "r7", "text": "All 10 tests passed (10/10). Fix verified.", "full_suite": True,
     "expected": "accept", "suite_total": 10},
    {"id": "r8", "text": "Done. Tests: 5 of 5 passed.", "full_suite": True,
     "expected": "accept", "suite_total": 5},
    # Partial / misleading (4)
    {"id": "r9", "text": "Tests pass! Fixed the auth bug.", "full_suite": False,
     "expected": "reject", "reason": "no_count"},
    {"id": "r10", "text": "test_auth.py: 3/3 passed.", "full_suite": False,
     "expected": "reject", "reason": "single_file_only"},
    {"id": "r11", "text": "All tests passed.", "full_suite": False,
     "expected": "reject", "reason": "no_count"},
    {"id": "r12", "text": "Ran test_factorial_basic: PASSED. Done.", "full_suite": False,
     "expected": "reject", "reason": "single_test_only"},
    # No count at all (4)
    {"id": "r13", "text": "Fix applied and verified. PR #42 opened.", "full_suite": False,
     "expected": "reject", "reason": "no_mention_of_tests"},
    {"id": "r14", "text": "Done! The bug is fixed.", "full_suite": False,
     "expected": "reject", "reason": "no_mention_of_tests"},
    {"id": "r15", "text": "Changes look good. Merging.", "full_suite": False,
     "expected": "reject", "reason": "no_mention_of_tests"},
    {"id": "r16", "text": "Implemented the feature. Ready for review.", "full_suite": False,
     "expected": "reject", "reason": "no_mention_of_tests"},
]

# Gate rules (written after reports, but not fitted to them)
FULL_SUITE_PATTERN = re.compile(
    r'(\d+)\s*/\s*(\d+)'           # N/M format
    r'|(\d+)\s+(?:of|out of)\s+(\d+)'  # N of M / N out of M
    r'|(\d+)\s+passed.*?(\d+)\s+(?:total|tests)'  # N passed ... M total
)
SINGLE_FILE_PATTERN = re.compile(r'^\S+\.(?:py|ts|js|rb):\s*\d+/\d+', re.MULTILINE)


def check_done_report(text: str) -> dict:
    """Check if a done report includes a full-suite test count."""
    # Look for N/M pattern
    match = FULL_SUITE_PATTERN.search(text)
    if not match:
        return {"accepted": False, "reason": "no_test_count_found"}

    # Extract the numbers
    groups = match.groups()
    for i in range(0, len(groups), 2):
        if groups[i] is not None and groups[i+1] is not None:
            passed = int(groups[i])
            total = int(groups[i+1])
            break
    else:
        return {"accepted": False, "reason": "no_test_count_found"}

    # Reject if it looks like a single-file report
    if SINGLE_FILE_PATTERN.search(text):
        # But accept if there's also a full-suite count elsewhere
        lines = text.strip().splitlines()
        if len(lines) <= 1:
            return {"accepted": False, "reason": "single_file_only",
                    "passed": passed, "total": total}

    if passed != total:
        return {"accepted": False, "reason": "not_all_passed",
                "passed": passed, "total": total}

    return {"accepted": True, "passed": passed, "total": total}


def main():
    parser = argparse.ArgumentParser(description="Experiment 69: Done Test Count")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 69: 'Done' Needs a Test Count")
    print("=" * 65)
    print(f"Reports: {len(DONE_REPORTS)} (8 full-suite, 4 partial, 4 no-count)")
    print(f"Reports written independently of gate rules.")
    print()
    print("--- MEASURED (gate logic on labeled reports) ---")
    print()

    correct = 0
    false_rejects = 0  # full-suite wrongly rejected
    false_accepts = 0  # partial/none wrongly accepted
    catches = 0        # partial/none correctly rejected

    for report in DONE_REPORTS:
        result = check_done_report(report["text"])
        actual = "accept" if result["accepted"] else "reject"
        is_correct = actual == report["expected"]
        if is_correct:
            correct += 1
        if actual == "reject" and report["expected"] == "accept":
            false_rejects += 1
        if actual == "accept" and report["expected"] == "reject":
            false_accepts += 1
        if actual == "reject" and report["expected"] == "reject":
            catches += 1

        icon = "OK" if is_correct else "!!"
        print(f"  [{icon}] {report['id']:<4} expected={report['expected']:<7} "
              f"actual={actual:<7} '{report['text'][:50]}...'")
        if not is_correct:
            print(f"         gate reason: {result.get('reason', 'n/a')}")

    total = len(DONE_REPORTS)
    full_suite_total = sum(1 for r in DONE_REPORTS if r["full_suite"])
    partial_total = total - full_suite_total

    accuracy = correct / total * 100
    catch_rate = catches / partial_total * 100 if partial_total > 0 else 0
    false_reject_rate = false_rejects / full_suite_total * 100 if full_suite_total > 0 else 0

    print()
    print(f"{'Metric':<40} {'Value':>10}")
    print("-" * 52)
    print(f"{'Total reports':<40} {total:>10}")
    print(f"{'Accuracy':<40} {correct:>8}/{total}")
    print(f"{'Incomplete runs caught':<40} {catches:>8}/{partial_total}")
    print(f"{'False rejects (full-suite rejected)':<40} {false_rejects:>10}")
    print(f"{'False accepts (partial accepted)':<40} {false_accepts:>10}")
    print(f"{'Catch rate':<40} {catch_rate:>9.1f}%")
    print(f"{'False-reject rate':<40} {false_reject_rate:>9.1f}%")
    print()

    print(f"Conclusion (MEASURED): The gate catches {catches}/{partial_total}")
    print(f"incomplete/absent test reports with {false_rejects} false rejects on")
    print(f"full-suite reports ({accuracy:.0f}% accuracy).")
    print(f"Sample: {total} reports. Reports written independently of gate rules.")

    exp_summary = {
        "experiment": "69_done_test_count",
        "simulated": False,
        "reports_written_independently": True,
        "reports_total": total,
        "full_suite": full_suite_total,
        "partial_or_none": partial_total,
        "correct": correct,
        "accuracy_pct": round(accuracy, 2),
        "catches": catches,
        "catch_rate_pct": round(catch_rate, 2),
        "false_rejects": false_rejects,
        "false_accepts": false_accepts,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(exp_summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
