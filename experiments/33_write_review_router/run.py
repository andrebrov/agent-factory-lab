#!/usr/bin/env python3
"""
Experiment 33: Write/Review Router — Strong for Judgment, Cheap for Checks
===========================================================================

Extends experiment 2's pricing model to the review phase specifically:
frontier model for judgment (security, correctness, design) vs cheap model
for mechanical checks (lint, types, tests, formatting).

ESTIMATED — real pricing data, synthetic review trace.
"""
import json
import os
import argparse

PRICING = {
    "claude-opus": {"input": 15.00, "output": 75.00},
    "claude-sonnet": {"input": 3.00, "output": 15.00},
    "claude-haiku": {"input": 0.25, "output": 1.25},
}

REVIEW_STEPS = [
    {"step": "lint_check", "type": "mechanical", "input_tokens": 800, "output_tokens": 200},
    {"step": "type_check", "type": "mechanical", "input_tokens": 600, "output_tokens": 150},
    {"step": "format_check", "type": "mechanical", "input_tokens": 400, "output_tokens": 100},
    {"step": "test_execution", "type": "mechanical", "input_tokens": 1200, "output_tokens": 500},
    {"step": "test_coverage", "type": "mechanical", "input_tokens": 500, "output_tokens": 200},
    {"step": "security_review", "type": "judgment", "input_tokens": 3000, "output_tokens": 1500},
    {"step": "correctness_review", "type": "judgment", "input_tokens": 4000, "output_tokens": 2000},
    {"step": "design_review", "type": "judgment", "input_tokens": 2500, "output_tokens": 1200},
    {"step": "api_compatibility", "type": "judgment", "input_tokens": 1500, "output_tokens": 800},
    {"step": "commit_message", "type": "mechanical", "input_tokens": 300, "output_tokens": 100},
]


def compute_cost(step: dict, model: str) -> float:
    p = PRICING[model]
    return step["input_tokens"] * p["input"] / 1e6 + step["output_tokens"] * p["output"] / 1e6


def main():
    parser = argparse.ArgumentParser(description="Experiment 33: Write/Review Router")
    parser.add_argument("--frontier", default="claude-opus", choices=list(PRICING.keys()))
    parser.add_argument("--cheap", default="claude-haiku", choices=list(PRICING.keys()))
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    mechanical = [s for s in REVIEW_STEPS if s["type"] == "mechanical"]
    judgment = [s for s in REVIEW_STEPS if s["type"] == "judgment"]

    mech_input = sum(s["input_tokens"] for s in mechanical)
    mech_output = sum(s["output_tokens"] for s in mechanical)
    judg_input = sum(s["input_tokens"] for s in judgment)
    judg_output = sum(s["output_tokens"] for s in judgment)
    total_input = mech_input + judg_input
    total_output = mech_output + judg_output

    all_frontier = sum(compute_cost(s, args.frontier) for s in REVIEW_STEPS)
    routed = (sum(compute_cost(s, args.cheap) for s in mechanical) +
              sum(compute_cost(s, args.frontier) for s in judgment))

    savings = all_frontier - routed
    savings_pct = savings / all_frontier * 100 if all_frontier > 0 else 0

    # Early-exit scenario: if mechanical checks fail, skip judgment
    mech_fail_rate = 0.25
    early_exit_savings = mech_fail_rate * sum(compute_cost(s, args.frontier) for s in judgment)
    total_savings_with_exit = savings + early_exit_savings
    total_savings_pct = total_savings_with_exit / all_frontier * 100

    print("=" * 65)
    print("EXPERIMENT 33: Write/Review Router")
    print("=" * 65)
    print(f"Frontier: {args.frontier}, Cheap: {args.cheap}")
    print()
    print("--- ALL COSTS ARE ESTIMATED FROM PUBLIC PRICING ---")
    print()

    print(f"Review breakdown ({len(REVIEW_STEPS)} steps):")
    print(f"  Mechanical: {len(mechanical)} steps, {mech_input:,} in + {mech_output:,} out "
          f"({mech_input / total_input:.0%} of input)")
    print(f"  Judgment:   {len(judgment)} steps, {judg_input:,} in + {judg_output:,} out "
          f"({judg_input / total_input:.0%} of input)")
    print()

    print(f"{'Mode':<35} {'Cost':>10}")
    print("-" * 47)
    print(f"{'All-frontier review':<35} ${all_frontier:>9.5f}")
    print(f"{'Routed (cheap mech + frontier judg)':<35} ${routed:>9.5f}")
    print(f"{'Savings (routing only)':<35} ${savings:>9.5f} ({savings_pct:.1f}%)")
    print(f"{'+ Early exit (mech fail {:.0%})'.format(mech_fail_rate):<35} "
          f"${total_savings_with_exit:>9.5f} ({total_savings_pct:.1f}%)")
    print()

    print("Per-step breakdown:")
    print(f"  {'Step':<22} {'Type':<12} {'Frontier':>10} {'Routed':>10} {'Model':>14}")
    print("  " + "-" * 70)
    for s in REVIEW_STEPS:
        fc = compute_cost(s, args.frontier)
        model = args.cheap if s["type"] == "mechanical" else args.frontier
        rc = compute_cost(s, model)
        print(f"  {s['step']:<22} {s['type']:<12} ${fc:>9.5f} ${rc:>9.5f} {model:>14}")

    print()
    print(f"Conclusion (ESTIMATED): Routing mechanical review checks to")
    print(f"{args.cheap} saves {savings_pct:.0f}% on review cost alone.")
    print(f"With early exit on mechanical failure (~{mech_fail_rate:.0%} of PRs),")
    print(f"total savings reach {total_savings_pct:.0f}%.")

    summary = {
        "experiment": "33_write_review_router",
        "simulated": True,
        "frontier_model": args.frontier,
        "cheap_model": args.cheap,
        "review_steps": len(REVIEW_STEPS),
        "mechanical_steps": len(mechanical),
        "judgment_steps": len(judgment),
        "all_frontier_cost": round(all_frontier, 6),
        "routed_cost": round(routed, 6),
        "routing_savings_pct": round(savings_pct, 2),
        "early_exit_savings_pct": round(total_savings_pct, 2),
        "mechanical_fail_rate": mech_fail_rate,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
