#!/usr/bin/env python3
"""
Experiment 91: Instruction Checklist in Every "Done" Report
=============================================================

A checker parses a task file (list of instructions) and a done report,
verifying every instruction is listed as done/skipped/blocked with a reason.

Cases constructed BEFORE the checker. Cannot test against a live agent.

MEASURED: checker logic on 10 (task, report) pairs.
Sample: 3 task files, 10 done reports (5 complete, 3 missing items, 2 vague).
"""
import json, os, re, argparse

TASK_FILES = [
    {"id": "task-A", "instructions": [
        "Fix the factorial bug (range starts at 0)",
        "Add a test for factorial(0) == 1",
        "Run the full test suite",
        "Update the docstring",
    ]},
    {"id": "task-B", "instructions": [
        "Add rate limiting to the API",
        "Write integration tests for rate limiting",
        "Update the README with the new endpoint",
    ]},
    {"id": "task-C", "instructions": [
        "Migrate the database schema",
        "Add email_verified field to User model",
        "Update the admin panel",
        "Run migration in staging",
        "Verify no data loss",
    ]},
]

# Reports written BEFORE the checker code
DONE_REPORTS = [
    # Complete (5) — every instruction listed
    {"id": "r1", "task_id": "task-A", "expected": "accept",
     "text": "Done:\n- Fix factorial bug: done (changed range to 1,n+1)\n"
             "- Test for factorial(0): done (added test_factorial_zero)\n"
             "- Full test suite: done (10/10 pass)\n- Docstring: done (updated)"},
    {"id": "r2", "task_id": "task-B", "expected": "accept",
     "text": "Completed:\n- Rate limiting: done, added TokenBucket middleware\n"
             "- Integration tests: done, 5 new tests\n- README: done, added /api/rate section"},
    {"id": "r3", "task_id": "task-C", "expected": "accept",
     "text": "Report:\n- Schema migration: done\n- email_verified field: done\n"
             "- Admin panel: done\n- Staging migration: done\n- Data loss check: done, verified"},
    {"id": "r4", "task_id": "task-A", "expected": "accept",
     "text": "- factorial bug: done\n- factorial(0) test: done\n"
             "- test suite: done (10/10)\n- docstring: skipped (already correct)"},
    {"id": "r5", "task_id": "task-B", "expected": "accept",
     "text": "1. Rate limiting: done\n2. Integration tests: done\n"
             "3. README: blocked (no write access to docs repo)"},
    # Missing items (3)
    {"id": "r6", "task_id": "task-A", "expected": "reject",
     "text": "Fixed the factorial bug. Tests pass.",
     "reason": "missing test, suite, docstring items"},
    {"id": "r7", "task_id": "task-C", "expected": "reject",
     "text": "- Schema migration: done\n- email_verified: done\n- Admin: done",
     "reason": "missing staging migration and data loss verification"},
    {"id": "r8", "task_id": "task-B", "expected": "reject",
     "text": "Rate limiting added. README updated.",
     "reason": "missing integration tests item"},
    # Vague mentions (2) — instruction mentioned but no status
    {"id": "r9", "task_id": "task-A", "expected": "reject",
     "text": "I looked at the factorial bug and the tests. The docstring is fine.",
     "reason": "mentions items but gives no done/skipped/blocked status"},
    {"id": "r10", "task_id": "task-C", "expected": "reject",
     "text": "Migration is in progress. Working on the admin panel. Will check data soon.",
     "reason": "in-progress, not a done report"},
]

STATUS_KEYWORDS = {"done", "completed", "skipped", "blocked", "finished", "added", "fixed",
                   "updated", "verified", "passed"}


def check_report(task: dict, report_text: str) -> dict:
    """Check that every instruction is listed with a status."""
    report_lower = report_text.lower()
    missing = []
    found = []

    for instruction in task["instructions"]:
        # Extract key noun phrases from the instruction
        keywords = [w for w in re.findall(r'\b\w{4,}\b', instruction.lower())
                    if w not in {"from", "with", "that", "this", "they", "have", "been", "should"}]

        # Check if at least one keyword appears near a status word
        instruction_found = False
        for kw in keywords:
            if kw in report_lower:
                # Check if a status word is within ~50 chars
                for match in re.finditer(re.escape(kw), report_lower):
                    context = report_lower[max(0, match.start()-30):match.end()+50]
                    if any(sw in context for sw in STATUS_KEYWORDS):
                        instruction_found = True
                        break
            if instruction_found:
                break

        if instruction_found:
            found.append(instruction)
        else:
            missing.append(instruction)

    accepted = len(missing) == 0
    return {"accepted": accepted, "found": len(found), "total": len(task["instructions"]),
            "missing": missing}


def main():
    parser = argparse.ArgumentParser(description="Experiment 91: Instruction Checklist")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    task_map = {t["id"]: t for t in TASK_FILES}

    print("=" * 65)
    print("EXPERIMENT 91: Instruction Checklist in Done Reports")
    print("=" * 65)
    print("Deterministic checker, NOT a live agent test.")
    print(f"Tasks: {len(TASK_FILES)}, Reports: {len(DONE_REPORTS)}")
    print(f"Reports written before the checker code.")
    print()

    correct = 0
    false_rejects = 0
    false_accepts = 0
    catches = 0

    for report in DONE_REPORTS:
        task = task_map[report["task_id"]]
        result = check_report(task, report["text"])
        actual = "accept" if result["accepted"] else "reject"
        is_correct = actual == report["expected"]
        if is_correct: correct += 1
        if actual == "reject" and report["expected"] == "accept": false_rejects += 1
        if actual == "accept" and report["expected"] == "reject": false_accepts += 1
        if actual == "reject" and report["expected"] == "reject": catches += 1

        icon = "OK" if is_correct else "!!"
        print(f"  [{icon}] {report['id']:<4} task={report['task_id']:<7} "
              f"expected={report['expected']:<7} actual={actual:<7} "
              f"found={result['found']}/{result['total']}")
        if result["missing"] and not is_correct:
            print(f"       missing: {result['missing'][:2]}")

    total = len(DONE_REPORTS)
    complete = sum(1 for r in DONE_REPORTS if r["expected"] == "accept")
    incomplete = total - complete

    print()
    print(f"{'Metric':<40} {'Value':>10}")
    print("-" * 52)
    print(f"{'Correct':<40} {correct:>8}/{total}")
    print(f"{'Incomplete/vague reports caught':<40} {catches:>8}/{incomplete}")
    print(f"{'False rejects (complete rejected)':<40} {false_rejects:>10}")
    print(f"{'False accepts (incomplete accepted)':<40} {false_accepts:>10}")
    print()
    print(f"Conclusion: {correct}/{total} correct. The checker catches {catches}/{incomplete}")
    print(f"incomplete reports with {false_rejects} false rejects.")
    print(f"This is a KEYWORD + PROXIMITY checker, not a model.")
    print(f"Cannot test against a live agent — only the checker logic.")

    summary = {
        "experiment": "91_instruction_checklist",
        "simulated": False,
        "checker_deterministic": True,
        "no_live_agent": True,
        "reports": total,
        "correct": correct,
        "catches": catches,
        "incomplete_total": incomplete,
        "false_rejects": false_rejects,
        "false_accepts": false_accepts,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
