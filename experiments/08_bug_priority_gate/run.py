#!/usr/bin/env python3
"""
Experiment 8: Bug Priority Gate (freq × severity ≥ 5)
=======================================================

Simulates a bug backlog with priority scores and compares gated (fix only
if score ≥ 5) vs ungated (fix everything) strategies.

SIMULATED — harness ready for integration with real bug trackers.
"""
import json
import os
import random
import argparse

THRESHOLD = 5

BUG_BACKLOG = [
    {"id": "BUG-1",  "desc": "Crash on empty input",        "frequency": 5, "severity": 4},
    {"id": "BUG-2",  "desc": "Typo in error message",       "frequency": 2, "severity": 1},
    {"id": "BUG-3",  "desc": "Race condition in cache",     "frequency": 3, "severity": 5},
    {"id": "BUG-4",  "desc": "Wrong date format in export", "frequency": 4, "severity": 2},
    {"id": "BUG-5",  "desc": "SQL injection in search",     "frequency": 1, "severity": 5},
    {"id": "BUG-6",  "desc": "CSS overflow on mobile",      "frequency": 3, "severity": 1},
    {"id": "BUG-7",  "desc": "Auth bypass via cookie",      "frequency": 2, "severity": 5},
    {"id": "BUG-8",  "desc": "Slow query on dashboard",     "frequency": 4, "severity": 3},
    {"id": "BUG-9",  "desc": "Missing CORS header",         "frequency": 3, "severity": 4},
    {"id": "BUG-10", "desc": "Memory leak in WebSocket",    "frequency": 5, "severity": 3},
    {"id": "BUG-11", "desc": "Tooltip text truncated",      "frequency": 2, "severity": 1},
    {"id": "BUG-12", "desc": "Email validation too strict",  "frequency": 3, "severity": 2},
    {"id": "BUG-13", "desc": "Data loss on concurrent save", "frequency": 2, "severity": 5},
    {"id": "BUG-14", "desc": "Incorrect pagination count",  "frequency": 4, "severity": 2},
    {"id": "BUG-15", "desc": "XSS in comment field",        "frequency": 1, "severity": 5},
]

FIX_COST_TOKENS = 4500
FILE_COST_TOKENS = 500


def main():
    parser = argparse.ArgumentParser(description="Experiment 8: Bug Priority Gate")
    parser.add_argument("--threshold", type=int, default=THRESHOLD)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    random.seed(args.seed)

    for bug in BUG_BACKLOG:
        bug["score"] = bug["frequency"] * bug["severity"]

    ungated_fixed = BUG_BACKLOG[:]
    gated_fixed = [b for b in BUG_BACKLOG if b["score"] >= args.threshold]
    gated_filed = [b for b in BUG_BACKLOG if b["score"] < args.threshold]

    ungated_tokens = len(ungated_fixed) * FIX_COST_TOKENS
    gated_tokens = len(gated_fixed) * FIX_COST_TOKENS + len(gated_filed) * FILE_COST_TOKENS

    high_severity_total = [b for b in BUG_BACKLOG if b["severity"] >= 4]
    ungated_high_fixed = len(high_severity_total)
    gated_high_fixed = len([b for b in gated_fixed if b["severity"] >= 4])
    gated_high_filed = len([b for b in gated_filed if b["severity"] >= 4])

    token_savings = (ungated_tokens - gated_tokens) / ungated_tokens * 100
    bug_reduction = (len(ungated_fixed) - len(gated_fixed)) / len(ungated_fixed) * 100

    print("=" * 65)
    print("EXPERIMENT 8: Bug Priority Gate (freq × severity ≥ threshold)")
    print("=" * 65)
    print(f"Backlog: {len(BUG_BACKLOG)} bugs, threshold: {args.threshold}")
    print()
    print("--- ALL NUMBERS ARE SIMULATED ---")
    print()

    print(f"{'Metric':<35} {'Ungated':>12} {'Gated':>12}")
    print("-" * 61)
    print(f"{'Bugs fixed now':<35} {len(ungated_fixed):>12} {len(gated_fixed):>12}")
    print(f"{'Bugs filed (deferred)':<35} {0:>12} {len(gated_filed):>12}")
    print(f"{'Total tokens spent':<35} {ungated_tokens:>12,} {gated_tokens:>12,}")
    print(f"{'Token savings':<35} {'baseline':>12} {token_savings:>11.1f}%")
    print(f"{'High-severity (≥4) fixed':<35} {ungated_high_fixed:>12} {gated_high_fixed:>12}")
    print(f"{'High-severity filed':<35} {0:>12} {gated_high_filed:>12}")
    print()

    print("Per-bug breakdown:")
    print(f"  {'ID':<8} {'Score':>5} {'Action':<8} {'Description'}")
    print("  " + "-" * 55)
    for b in sorted(BUG_BACKLOG, key=lambda x: -x["score"]):
        action = "FIX" if b["score"] >= args.threshold else "FILE"
        print(f"  {b['id']:<8} {b['score']:>5} {action:<8} {b['desc']}")

    print()
    print(f"Conclusion (SIMULATED): Gating at threshold {args.threshold} defers "
          f"{len(gated_filed)} low-priority bugs,")
    print(f"saving {token_savings:.0f}% of fix tokens while still addressing all "
          f"high-severity issues.")
    if gated_high_filed > 0:
        print(f"WARNING: {gated_high_filed} high-severity bug(s) were deferred — "
              f"consider adjusting the threshold.")

    summary = {
        "experiment": "08_bug_priority_gate",
        "simulated": True,
        "threshold": args.threshold,
        "total_bugs": len(BUG_BACKLOG),
        "bugs_fixed_ungated": len(ungated_fixed),
        "bugs_fixed_gated": len(gated_fixed),
        "bugs_filed": len(gated_filed),
        "token_savings_pct": round(token_savings, 2),
        "high_severity_fixed_gated": gated_high_fixed,
        "high_severity_filed_gated": gated_high_filed,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
