#!/usr/bin/env python3
"""
Experiment 9: Score the Reviewer Against Past Incidents
========================================================

Builds a synthetic PR corpus (known-good and known-bad diffs) and scores
a simulated reviewer on catch rate and false-alarm rate.

SIMULATED — the corpus uses the sample codebase's buggy/fixed diffs.
Harness ready for real LLM reviewer evaluation.
"""
import json
import os
import random
import argparse
import difflib
from pathlib import Path

SAMPLE_DIR = Path(__file__).parent.parent / "sample_codebase"


def load_diffs():
    """Generate diffs between buggy and fixed versions of each function."""
    buggy = (SAMPLE_DIR / "mathlib.py").read_text().splitlines()
    fixed = (SAMPLE_DIR / "mathlib_fixed.py").read_text().splitlines()
    full_diff = list(difflib.unified_diff(buggy, fixed, lineterm=""))
    return full_diff, buggy, fixed


def build_corpus():
    """Build a corpus of known-bad (buggy) and known-good (fixed) PRs."""
    _, buggy_lines, fixed_lines = load_diffs()
    corpus = []

    bug_ranges = [
        ("factorial",     12, 15),
        ("fibonacci",     22, 24),
        ("is_prime",      33, 34),
        ("binary_search", 44, 44),
        ("mean",          48, 48),
        ("flatten",       54, 54),
        ("merge_sorted",  62, 62),
        ("caesar_cipher", 73, 74),
        ("unique",        79, 79),
        ("clamp",         84, 86),
    ]

    for name, start, end in bug_ranges:
        corpus.append({
            "id": f"PR-bad-{name}",
            "is_bad": True,
            "function": name,
            "description": f"Contains known bug in {name}",
        })
        corpus.append({
            "id": f"PR-good-{name}",
            "is_bad": False,
            "function": name,
            "description": f"Correctly fixed {name}",
        })

    return corpus


def simulate_reviewer(pr: dict, p_catch: float, p_false_alarm: float) -> bool:
    """Returns True if the reviewer flags the PR. Ideal: flag bad, pass good."""
    if pr["is_bad"]:
        return random.random() < p_catch
    else:
        return random.random() < p_false_alarm


def main():
    parser = argparse.ArgumentParser(description="Experiment 9: Reviewer Scoring")
    parser.add_argument("--p-catch", type=float, default=0.75)
    parser.add_argument("--p-false-alarm", type=float, default=0.15)
    parser.add_argument("--trials", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    random.seed(args.seed)
    corpus = build_corpus()

    true_pos = 0
    false_neg = 0
    true_neg = 0
    false_pos = 0

    for _ in range(args.trials):
        for pr in corpus:
            flagged = simulate_reviewer(pr, args.p_catch, args.p_false_alarm)
            if pr["is_bad"] and flagged:
                true_pos += 1
            elif pr["is_bad"] and not flagged:
                false_neg += 1
            elif not pr["is_bad"] and flagged:
                false_pos += 1
            else:
                true_neg += 1

    total_bad = true_pos + false_neg
    total_good = true_neg + false_pos
    catch_rate = true_pos / total_bad if total_bad > 0 else 0
    false_alarm_rate = false_pos / total_good if total_good > 0 else 0
    precision = true_pos / (true_pos + false_pos) if (true_pos + false_pos) > 0 else 0
    f1 = 2 * precision * catch_rate / (precision + catch_rate) if (precision + catch_rate) > 0 else 0

    print("=" * 65)
    print("EXPERIMENT 9: Reviewer Scoring Against Past Incidents")
    print("=" * 65)
    print(f"Corpus: {len(corpus)} PRs ({sum(1 for p in corpus if p['is_bad'])} bad, "
          f"{sum(1 for p in corpus if not p['is_bad'])} good)")
    print(f"Trials: {args.trials}")
    print(f"Parameters: P(catch)={args.p_catch}, P(false_alarm)={args.p_false_alarm}")
    print()
    print("--- ALL NUMBERS ARE SIMULATED ---")
    print()
    print(f"{'Metric':<30} {'Value':>12}")
    print("-" * 44)
    print(f"{'True positives (caught bad)':<30} {true_pos:>12}")
    print(f"{'False negatives (missed bad)':<30} {false_neg:>12}")
    print(f"{'True negatives (passed good)':<30} {true_neg:>12}")
    print(f"{'False positives (flagged good)':<30} {false_pos:>12}")
    print(f"{'Catch rate (recall)':<30} {catch_rate:>11.1%}")
    print(f"{'False-alarm rate':<30} {false_alarm_rate:>11.1%}")
    print(f"{'Precision':<30} {precision:>11.1%}")
    print(f"{'F1 score':<30} {f1:>12.3f}")
    print()
    print("Conclusion (SIMULATED): The scoring framework produces actionable")
    print("metrics. With real LLM reviewers, use this corpus to compare models")
    print("and calibrate confidence thresholds.")

    summary = {
        "experiment": "09_reviewer_scoring",
        "simulated": True,
        "corpus_size": len(corpus),
        "trials": args.trials,
        "results": {
            "catch_rate": round(catch_rate, 4),
            "false_alarm_rate": round(false_alarm_rate, 4),
            "precision": round(precision, 4),
            "f1_score": round(f1, 4),
            "true_pos": true_pos, "false_neg": false_neg,
            "true_neg": true_neg, "false_pos": false_pos,
        },
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
