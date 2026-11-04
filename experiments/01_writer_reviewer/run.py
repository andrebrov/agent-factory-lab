#!/usr/bin/env python3
"""
Experiment 1: Writer/Reviewer Pipeline vs Single-Agent
=======================================================

Simulates a single-agent and a writer+reviewer pipeline attempting to fix
the 10 seeded bugs in sample_codebase/mathlib.py.

Since we don't have real LLM API keys, we simulate agent behavior:
- The "writer" produces a fix that is correct with probability P_correct.
- The "reviewer" approves correct fixes with probability P_approve_good
  and catches bad fixes with probability P_catch_bad.
- We run many Monte Carlo trials and compare success rates.

All numbers are labeled as SIMULATED. The harness is designed so that
Gwaihir/Landroval can later plug in real LLM calls by replacing the
simulate_* functions.
"""
import json
import random
import sys
import os
import argparse
from dataclasses import dataclass, asdict
from pathlib import Path

NUM_BUGS = 10
NUM_TRIALS = 1000
MAX_REVIEW_ROUNDS = 2

BUGS = [
    "factorial: range starts at 0 instead of 1",
    "fibonacci: fib(1) returns 0 instead of 1",
    "is_prime: uses // instead of %",
    "binary_search: returns mid instead of -1 on miss",
    "mean: no empty-list guard",
    "flatten: checks tuple instead of (list, tuple)",
    "merge_sorted: j starts at 1 instead of 0",
    "caesar_cipher: shifts all chars, not just letters",
    "unique: set() loses order",
    "clamp: lo/hi swapped",
]


@dataclass
class TrialResult:
    bug_id: int
    bug_desc: str
    mode: str
    fixed: bool
    rounds: int
    simulated_tokens: int


def simulate_writer_fix(p_correct: float) -> bool:
    return random.random() < p_correct


def simulate_reviewer(fix_is_correct: bool, p_approve_good: float, p_catch_bad: float) -> bool:
    if fix_is_correct:
        return random.random() < p_approve_good
    else:
        return random.random() > p_catch_bad


def estimate_tokens(mode: str, rounds: int) -> int:
    """Rough token estimates based on typical agent sessions."""
    if mode == "single":
        return 3000 + random.randint(-500, 500)
    else:
        base_writer = 2500
        base_reviewer = 1500
        return (base_writer + base_reviewer) * rounds + random.randint(-300, 300)


def run_single_agent_trial(bug_id: int, p_correct: float) -> TrialResult:
    fixed = simulate_writer_fix(p_correct)
    return TrialResult(
        bug_id=bug_id,
        bug_desc=BUGS[bug_id],
        mode="single",
        fixed=fixed,
        rounds=1,
        simulated_tokens=estimate_tokens("single", 1),
    )


def run_pipeline_trial(
    bug_id: int,
    p_correct: float,
    p_approve_good: float,
    p_catch_bad: float,
) -> TrialResult:
    for round_num in range(1, MAX_REVIEW_ROUNDS + 1):
        fix_correct = simulate_writer_fix(p_correct)
        approved = simulate_reviewer(fix_correct, p_approve_good, p_catch_bad)
        if approved:
            return TrialResult(
                bug_id=bug_id,
                bug_desc=BUGS[bug_id],
                mode="pipeline",
                fixed=fix_correct,
                rounds=round_num,
                simulated_tokens=estimate_tokens("pipeline", round_num),
            )
    return TrialResult(
        bug_id=bug_id,
        bug_desc=BUGS[bug_id],
        mode="pipeline",
        fixed=False,
        rounds=MAX_REVIEW_ROUNDS,
        simulated_tokens=estimate_tokens("pipeline", MAX_REVIEW_ROUNDS),
    )


def main():
    parser = argparse.ArgumentParser(description="Experiment 1: Writer/Reviewer Pipeline")
    parser.add_argument("--trials", type=int, default=NUM_TRIALS)
    parser.add_argument("--p-correct", type=float, default=0.65,
                        help="Probability writer produces a correct fix")
    parser.add_argument("--p-approve-good", type=float, default=0.95,
                        help="Probability reviewer approves a correct fix")
    parser.add_argument("--p-catch-bad", type=float, default=0.70,
                        help="Probability reviewer catches an incorrect fix")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default=None,
                        help="Path to write JSON results")
    args = parser.parse_args()

    random.seed(args.seed)

    single_results = []
    pipeline_results = []

    for _ in range(args.trials):
        for bug_id in range(NUM_BUGS):
            single_results.append(run_single_agent_trial(bug_id, args.p_correct))
            pipeline_results.append(run_pipeline_trial(
                bug_id, args.p_correct, args.p_approve_good, args.p_catch_bad,
            ))

    single_fixes = sum(r.fixed for r in single_results)
    pipeline_fixes = sum(r.fixed for r in pipeline_results)
    total = len(single_results)

    single_tokens = sum(r.simulated_tokens for r in single_results)
    pipeline_tokens = sum(r.simulated_tokens for r in pipeline_results)

    pipeline_false_pos = sum(
        1 for r in pipeline_results if r.fixed is False and r.mode == "pipeline"
    )
    avg_rounds = sum(r.rounds for r in pipeline_results) / len(pipeline_results)

    print("=" * 60)
    print("EXPERIMENT 1: Writer/Reviewer Pipeline vs Single-Agent")
    print("=" * 60)
    print(f"Trials per bug: {args.trials}")
    print(f"Bugs: {NUM_BUGS}")
    print(f"Total attempts: {total}")
    print(f"Parameters: P(correct)={args.p_correct}, "
          f"P(approve_good)={args.p_approve_good}, "
          f"P(catch_bad)={args.p_catch_bad}")
    print()
    print("--- ALL NUMBERS BELOW ARE SIMULATED ---")
    print()
    print(f"{'Metric':<35} {'Single':>10} {'Pipeline':>10}")
    print("-" * 57)
    print(f"{'Fix success rate':<35} {single_fixes/total:>9.1%} {pipeline_fixes/total:>9.1%}")
    print(f"{'Total fixes':<35} {single_fixes:>10} {pipeline_fixes:>10}")
    print(f"{'Failed fixes shipped':<35} {total - single_fixes:>10} {pipeline_false_pos:>10}")
    print(f"{'Avg simulated tokens/attempt':<35} {single_tokens/total:>10.0f} {pipeline_tokens/total:>10.0f}")
    print(f"{'Total simulated tokens':<35} {single_tokens:>10} {pipeline_tokens:>10}")
    print(f"{'Avg review rounds (pipeline)':<35} {'n/a':>10} {avg_rounds:>10.2f}")
    print()

    per_bug = []
    for bug_id in range(NUM_BUGS):
        s = [r for r in single_results if r.bug_id == bug_id]
        p = [r for r in pipeline_results if r.bug_id == bug_id]
        s_rate = sum(r.fixed for r in s) / len(s)
        p_rate = sum(r.fixed for r in p) / len(p)
        per_bug.append({
            "bug_id": bug_id,
            "bug_desc": BUGS[bug_id],
            "single_fix_rate": round(s_rate, 3),
            "pipeline_fix_rate": round(p_rate, 3),
            "delta": round(p_rate - s_rate, 3),
        })
        print(f"  Bug {bug_id}: single={s_rate:.1%}  pipeline={p_rate:.1%}  "
              f"delta={p_rate - s_rate:+.1%}  ({BUGS[bug_id]})")

    print()
    print("Conclusion (SIMULATED): The reviewer pipeline reduces false-positive")
    print("shipped bugs at the cost of higher token usage. The net fix rate may")
    print("increase or decrease depending on whether the reviewer's catch rate")
    print("outweighs its false-rejection rate.")
    print()
    print("To run with real models: replace simulate_writer_fix() and")
    print("simulate_reviewer() with actual LLM API calls against")
    print("sample_codebase/mathlib.py.")

    summary = {
        "experiment": "01_writer_reviewer",
        "simulated": True,
        "parameters": {
            "trials": args.trials,
            "num_bugs": NUM_BUGS,
            "p_correct": args.p_correct,
            "p_approve_good": args.p_approve_good,
            "p_catch_bad": args.p_catch_bad,
        },
        "results": {
            "single_fix_rate": round(single_fixes / total, 4),
            "pipeline_fix_rate": round(pipeline_fixes / total, 4),
            "single_total_tokens": single_tokens,
            "pipeline_total_tokens": pipeline_tokens,
            "avg_review_rounds": round(avg_rounds, 3),
        },
        "per_bug": per_bug,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
