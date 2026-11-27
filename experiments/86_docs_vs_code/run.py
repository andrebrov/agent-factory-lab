#!/usr/bin/env python3
"""
Experiment 86: Docs-vs-Code Rule in AGENTS.md
=================================================

Builds a fixture where docs and code clearly disagree. Tests a
DETERMINISTIC MISMATCH CHECKER (not a real coding agent) that flags
disagreements and verifies they would be listed.

This does NOT test whether a real model follows the AGENTS.md rule.
It tests whether the mismatches are programmatically detectable.

MEASURED: mismatch detection on a constructed fixture.
Sample: 8 doc/code pairs (5 disagreements, 3 agreements).
"""
import json, os, argparse

# Fixture: code conventions and what the docs say
# Written BEFORE the checker code
CODE_CONVENTIONS = {
    "indent": {"code_does": "4 spaces", "source": "all .py files use 4-space indent"},
    "test_runner": {"code_does": "pytest", "source": "test files import pytest"},
    "naming": {"code_does": "snake_case", "source": "all functions use snake_case"},
    "error_handling": {"code_does": "raise ValueError", "source": "functions raise ValueError on bad input"},
    "return_sentinel": {"code_does": "return -1", "source": "binary_search returns -1 on miss"},
    "docstrings": {"code_does": "triple-quote", "source": "functions have triple-quote docstrings"},
    "imports": {"code_does": "stdlib first", "source": "import statements: stdlib before third-party"},
    "line_length": {"code_does": "no hard limit", "source": "lines vary, some >100 chars"},
}

DOC_CLAIMS = [
    # 5 disagreements
    {"id": "d1", "topic": "indent", "doc_says": "2 spaces",
     "agrees": False, "desc": "Docs say 2-space indent, code uses 4"},
    {"id": "d2", "topic": "test_runner", "doc_says": "unittest",
     "agrees": False, "desc": "Docs say unittest, code uses pytest"},
    {"id": "d3", "topic": "return_sentinel", "doc_says": "return None",
     "agrees": False, "desc": "Docs say return None, code returns -1"},
    {"id": "d4", "topic": "line_length", "doc_says": "max 79 characters",
     "agrees": False, "desc": "Docs say max 79, code has no hard limit"},
    {"id": "d5", "topic": "error_handling", "doc_says": "return error code",
     "agrees": False, "desc": "Docs say return error code, code raises ValueError"},
    # 3 agreements
    {"id": "a1", "topic": "naming", "doc_says": "snake_case",
     "agrees": True, "desc": "Docs and code both use snake_case"},
    {"id": "a2", "topic": "docstrings", "doc_says": "triple-quote",
     "agrees": True, "desc": "Docs and code both use triple-quote docstrings"},
    {"id": "a3", "topic": "imports", "doc_says": "stdlib first",
     "agrees": True, "desc": "Docs and code both put stdlib first"},
]


def check_mismatch(doc_claim: dict, code_conventions: dict) -> dict:
    """Deterministic checker: does the doc claim match the code convention?"""
    topic = doc_claim["topic"]
    if topic not in code_conventions:
        return {"match": None, "reason": "topic not in code"}

    code_does = code_conventions[topic]["code_does"]
    doc_says = doc_claim["doc_says"]

    # Simple string comparison — not NLP, not a model
    match = doc_says.lower().strip() == code_does.lower().strip()
    return {
        "match": match,
        "code_does": code_does,
        "doc_says": doc_says,
        "mismatch_detail": None if match else f"Doc says '{doc_says}', code does '{code_does}'",
    }


def verify_listing(mismatches: list, report_text: str) -> dict:
    """Check that every mismatch is listed in the report."""
    listed = 0
    missing = []
    for m in mismatches:
        # Check if the topic appears in the report
        if m["topic"] in report_text.lower() or m["code_does"].lower() in report_text.lower():
            listed += 1
        else:
            missing.append(m["topic"])
    return {"listed": listed, "total": len(mismatches), "missing": missing}


def main():
    parser = argparse.ArgumentParser(description="Experiment 86: Docs vs Code")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 86: Docs-vs-Code Rule in AGENTS.md")
    print("=" * 65)
    print("DETERMINISTIC MISMATCH CHECKER, not a real coding agent.")
    print("Does NOT test whether a model follows the rule.")
    print()

    # Phase 1: Detect mismatches
    print("Phase 1: Mismatch Detection (MEASURED)")
    print("-" * 55)

    detected_mismatches = []
    correct = 0

    for claim in DOC_CLAIMS:
        result = check_mismatch(claim, CODE_CONVENTIONS)
        expected_match = claim["agrees"]
        actual_match = result["match"]
        is_correct = actual_match == expected_match
        if is_correct: correct += 1
        if not actual_match:
            detected_mismatches.append({"topic": claim["topic"], **result})

        icon = "OK" if is_correct else "!!"
        status = "agree" if actual_match else "MISMATCH"
        print(f"  [{icon}] {claim['id']:<4} {claim['desc']:<50} → {status}")

    total = len(DOC_CLAIMS)
    disagree_count = sum(1 for c in DOC_CLAIMS if not c["agrees"])
    detected_count = len(detected_mismatches)

    print(f"\n  Detection accuracy: {correct}/{total}")
    print(f"  Mismatches found: {detected_count}/{disagree_count}")
    print()

    # Phase 2: Verify listing requirement
    print("Phase 2: Listing Verification (RULE CHECK)")
    print("-" * 55)

    # Simulate a report that lists all mismatches
    good_report = "Inconsistencies found:\n"
    for m in detected_mismatches:
        good_report += f"- {m['topic']}: {m['mismatch_detail']}\n"

    good_listing = verify_listing(detected_mismatches, good_report)
    print(f"  Good report (lists all): {good_listing['listed']}/{good_listing['total']} listed")

    # Simulate a report that misses one
    partial_report = "Inconsistencies found:\n"
    for m in detected_mismatches[:-1]:  # skip last
        partial_report += f"- {m['topic']}: {m['mismatch_detail']}\n"

    partial_listing = verify_listing(detected_mismatches, partial_report)
    print(f"  Partial report (misses 1): {partial_listing['listed']}/{partial_listing['total']} listed")
    print(f"    Missing: {partial_listing['missing']}")

    # Empty report
    empty_listing = verify_listing(detected_mismatches, "No issues found.")
    print(f"  Empty report: {empty_listing['listed']}/{empty_listing['total']} listed")
    print()

    listing_correct = (
        good_listing["listed"] == good_listing["total"] and
        partial_listing["listed"] < partial_listing["total"] and
        empty_listing["listed"] == 0
    )

    print(f"{'Metric':<40} {'Value':>10}")
    print("-" * 52)
    print(f"{'Mismatch detection accuracy':<40} {correct:>8}/{total}")
    print(f"{'Mismatches found':<40} {detected_count:>8}/{disagree_count}")
    print(f"{'Listing checker correct':<40} {str(listing_correct):>10}")
    print()

    print(f"Conclusion: The deterministic checker detects {detected_count}/{disagree_count}")
    print(f"doc/code mismatches and verifies they are listed in a report.")
    print(f"This does NOT test whether a real coding agent follows the")
    print(f"AGENTS.md rule — only that the mismatches are programmatically")
    print(f"detectable. A model test would require a real LLM.")
    print(f"Sample: {total} doc/code pairs ({disagree_count} disagreements, "
          f"{total - disagree_count} agreements).")

    summary = {
        "experiment": "86_docs_vs_code",
        "simulated": False,
        "checker_deterministic": True,
        "not_a_model_test": True,
        "pairs": total,
        "mismatches_expected": disagree_count,
        "mismatches_detected": detected_count,
        "detection_accuracy": correct,
        "listing_checker_works": listing_correct,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
