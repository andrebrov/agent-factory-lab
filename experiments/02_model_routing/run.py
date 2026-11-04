#!/usr/bin/env python3
"""
Experiment 2: Cheap vs Frontier Model Routing Cost Model
=========================================================

Models the cost difference between:
  (a) All-frontier: every agent step uses a frontier model.
  (b) Two-tier: orchestration/control-plane uses a cheap model,
      code generation/data-plane uses a frontier model.

Uses real pricing data (as of mid-2025, publicly available).
The session trace is synthesized but representative of a real
multi-file coding task.

All cost numbers are ESTIMATED from public pricing — no actual
API calls are made.
"""
import json
import os
import argparse
from dataclasses import dataclass, asdict

PRICING = {
    "claude-opus": {"input": 15.00, "output": 75.00, "cached_input": 1.50},
    "claude-sonnet": {"input": 3.00, "output": 15.00, "cached_input": 0.30},
    "claude-haiku": {"input": 0.25, "output": 1.25, "cached_input": 0.03},
    "gpt-4o": {"input": 2.50, "output": 10.00, "cached_input": 1.25},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60, "cached_input": 0.075},
}

SYNTHETIC_SESSION = [
    {"step": "parse_issue", "type": "control", "input_tokens": 800, "output_tokens": 200},
    {"step": "list_files", "type": "control", "input_tokens": 500, "output_tokens": 150},
    {"step": "read_file_1", "type": "control", "input_tokens": 600, "output_tokens": 100},
    {"step": "read_file_2", "type": "control", "input_tokens": 600, "output_tokens": 100},
    {"step": "plan_changes", "type": "data", "input_tokens": 3000, "output_tokens": 1500},
    {"step": "write_code_1", "type": "data", "input_tokens": 4000, "output_tokens": 2000},
    {"step": "check_status_1", "type": "control", "input_tokens": 500, "output_tokens": 100},
    {"step": "write_code_2", "type": "data", "input_tokens": 4500, "output_tokens": 2500},
    {"step": "run_tests", "type": "control", "input_tokens": 700, "output_tokens": 300},
    {"step": "read_test_output", "type": "control", "input_tokens": 800, "output_tokens": 200},
    {"step": "fix_test_failure", "type": "data", "input_tokens": 3500, "output_tokens": 1500},
    {"step": "run_tests_2", "type": "control", "input_tokens": 700, "output_tokens": 300},
    {"step": "check_status_2", "type": "control", "input_tokens": 500, "output_tokens": 100},
    {"step": "write_code_3", "type": "data", "input_tokens": 5000, "output_tokens": 3000},
    {"step": "run_lint", "type": "control", "input_tokens": 600, "output_tokens": 200},
    {"step": "format_pr", "type": "control", "input_tokens": 1000, "output_tokens": 500},
    {"step": "final_check", "type": "control", "input_tokens": 500, "output_tokens": 100},
]


def cost_per_mtok(model: str, direction: str) -> float:
    return PRICING[model][direction]


def compute_step_cost(step: dict, model: str) -> float:
    input_cost = step["input_tokens"] * cost_per_mtok(model, "input") / 1_000_000
    output_cost = step["output_tokens"] * cost_per_mtok(model, "output") / 1_000_000
    return input_cost + output_cost


def main():
    parser = argparse.ArgumentParser(description="Experiment 2: Model Routing Cost Model")
    parser.add_argument("--frontier", default="claude-opus", choices=list(PRICING.keys()))
    parser.add_argument("--cheap", default="claude-haiku", choices=list(PRICING.keys()))
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    total_input = sum(s["input_tokens"] for s in SYNTHETIC_SESSION)
    total_output = sum(s["output_tokens"] for s in SYNTHETIC_SESSION)
    control_input = sum(s["input_tokens"] for s in SYNTHETIC_SESSION if s["type"] == "control")
    control_output = sum(s["output_tokens"] for s in SYNTHETIC_SESSION if s["type"] == "control")
    data_input = sum(s["input_tokens"] for s in SYNTHETIC_SESSION if s["type"] == "data")
    data_output = sum(s["output_tokens"] for s in SYNTHETIC_SESSION if s["type"] == "data")

    all_frontier_cost = sum(compute_step_cost(s, args.frontier) for s in SYNTHETIC_SESSION)
    two_tier_cost = sum(
        compute_step_cost(s, args.cheap if s["type"] == "control" else args.frontier)
        for s in SYNTHETIC_SESSION
    )

    savings = all_frontier_cost - two_tier_cost
    savings_pct = savings / all_frontier_cost * 100 if all_frontier_cost > 0 else 0

    print("=" * 65)
    print("EXPERIMENT 2: Cheap vs Frontier Model Routing Cost Model")
    print("=" * 65)
    print(f"Frontier model: {args.frontier} "
          f"(${PRICING[args.frontier]['input']}/M in, "
          f"${PRICING[args.frontier]['output']}/M out)")
    print(f"Cheap model:    {args.cheap} "
          f"(${PRICING[args.cheap]['input']}/M in, "
          f"${PRICING[args.cheap]['output']}/M out)")
    print()
    print("--- ALL COSTS ARE ESTIMATED FROM PUBLIC PRICING ---")
    print()
    print(f"Session: {len(SYNTHETIC_SESSION)} steps")
    print(f"  Total tokens:   {total_input:,} input + {total_output:,} output")
    ctrl_steps = sum(1 for s in SYNTHETIC_SESSION if s["type"] == "control")
    data_steps = sum(1 for s in SYNTHETIC_SESSION if s["type"] == "data")
    print(f"  Control-plane:  {ctrl_steps} steps, "
          f"{control_input:,} in + {control_output:,} out "
          f"({control_input / total_input:.0%} of input)")
    print(f"  Data-plane:     {data_steps} steps, "
          f"{data_input:,} in + {data_output:,} out "
          f"({data_input / total_input:.0%} of input)")
    print()

    print(f"{'Mode':<25} {'Cost':>12}")
    print("-" * 39)
    print(f"{'All-frontier'::<25} ${all_frontier_cost:>10.4f}")
    print(f"{'Two-tier (cheap+frontier)'::<25} ${two_tier_cost:>10.4f}")
    print(f"{'Savings'::<25} ${savings:>10.4f} ({savings_pct:.1f}%)")
    print()

    print("Per-step breakdown:")
    print(f"  {'Step':<22} {'Type':<8} {'In':>6} {'Out':>6} "
          f"{'Frontier':>10} {'Two-tier':>10} {'Saved':>8}")
    print("  " + "-" * 74)
    step_details = []
    for s in SYNTHETIC_SESSION:
        fc = compute_step_cost(s, args.frontier)
        model = args.cheap if s["type"] == "control" else args.frontier
        tc = compute_step_cost(s, model)
        step_details.append({
            "step": s["step"],
            "type": s["type"],
            "input_tokens": s["input_tokens"],
            "output_tokens": s["output_tokens"],
            "frontier_cost": round(fc, 6),
            "two_tier_cost": round(tc, 6),
            "model_used": model,
        })
        print(f"  {s['step']:<22} {s['type']:<8} {s['input_tokens']:>6} "
              f"{s['output_tokens']:>6} ${fc:>9.5f} ${tc:>9.5f} "
              f"${fc - tc:>7.5f}")

    print()
    print("Conclusion (ESTIMATED): Routing control-plane steps to the cheap")
    print(f"model saves ~{savings_pct:.0f}% of session cost. Quality risk is low for")
    print("routing/status tasks but should be validated with A/B testing on")
    print("real coding tasks in Gwaihir.")

    summary = {
        "experiment": "02_model_routing",
        "simulated": True,
        "frontier_model": args.frontier,
        "cheap_model": args.cheap,
        "session_steps": len(SYNTHETIC_SESSION),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "control_plane_pct": round(control_input / total_input, 3),
        "all_frontier_cost": round(all_frontier_cost, 6),
        "two_tier_cost": round(two_tier_cost, 6),
        "savings_usd": round(savings, 6),
        "savings_pct": round(savings_pct, 2),
        "step_details": step_details,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
