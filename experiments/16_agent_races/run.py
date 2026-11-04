#!/usr/bin/env python3
"""
Experiment 16: Agent Races — Run 2–3 Models, Pick the Winner
==============================================================

Simulates racing multiple agents on the same task and measures how
often racing finds at least one correct solution compared to single-agent.

SIMULATED — Monte Carlo with configurable per-agent success probabilities.
"""
import json
import os
import random
import argparse

NUM_TASKS = 100
NUM_TRIALS = 500


def simulate_single_agent(p_success: float) -> bool:
    return random.random() < p_success


def simulate_race(agent_probs: list) -> dict:
    results = [random.random() < p for p in agent_probs]
    any_success = any(results)
    majority = sum(results) > len(results) / 2
    return {
        "any_success": any_success,
        "majority_agree": majority,
        "individual_results": results,
    }


def main():
    parser = argparse.ArgumentParser(description="Experiment 16: Agent Races")
    parser.add_argument("--trials", type=int, default=NUM_TRIALS)
    parser.add_argument("--tasks", type=int, default=NUM_TASKS)
    parser.add_argument("--p1", type=float, default=0.60, help="Agent 1 success probability")
    parser.add_argument("--p2", type=float, default=0.55, help="Agent 2 success probability")
    parser.add_argument("--p3", type=float, default=0.50, help="Agent 3 success probability")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    random.seed(args.seed)
    agent_probs = [args.p1, args.p2, args.p3]

    single_successes = 0
    race2_successes = 0
    race3_successes = 0
    race3_majority = 0
    total = args.trials * args.tasks

    single_tokens_per_task = 5000
    race2_tokens_per_task = single_tokens_per_task * 2
    race3_tokens_per_task = single_tokens_per_task * 3

    for _ in range(args.trials):
        for _ in range(args.tasks):
            s1 = simulate_single_agent(agent_probs[0])
            r2 = simulate_race(agent_probs[:2])
            r3 = simulate_race(agent_probs[:3])
            if s1:
                single_successes += 1
            if r2["any_success"]:
                race2_successes += 1
            if r3["any_success"]:
                race3_successes += 1
            if r3["majority_agree"]:
                race3_majority += 1

    single_rate = single_successes / total
    race2_rate = race2_successes / total
    race3_rate = race3_successes / total
    majority_rate = race3_majority / total

    p_none_2 = (1 - agent_probs[0]) * (1 - agent_probs[1])
    p_none_3 = p_none_2 * (1 - agent_probs[2])
    theoretical_race2 = 1 - p_none_2
    theoretical_race3 = 1 - p_none_3

    single_total_tokens = total * single_tokens_per_task
    race2_total_tokens = total * race2_tokens_per_task
    race3_total_tokens = total * race3_tokens_per_task

    print("=" * 65)
    print("EXPERIMENT 16: Agent Races — Run 2–3 Models, Pick Winner")
    print("=" * 65)
    print(f"Tasks: {args.tasks}, Trials: {args.trials}, Total: {total:,}")
    print(f"Agent success probs: {agent_probs}")
    print()
    print("--- ALL NUMBERS ARE SIMULATED ---")
    print()
    print(f"{'Mode':<25} {'Success Rate':>12} {'Theoretical':>12} {'Tokens':>14}")
    print("-" * 65)
    print(f"{'Single agent (p1)'::<25} {single_rate:>11.1%} {agent_probs[0]:>11.1%} {single_total_tokens:>14,}")
    print(f"{'Race 2 (best-of-2)'::<25} {race2_rate:>11.1%} {theoretical_race2:>11.1%} {race2_total_tokens:>14,}")
    print(f"{'Race 3 (best-of-3)'::<25} {race3_rate:>11.1%} {theoretical_race3:>11.1%} {race3_total_tokens:>14,}")
    print(f"{'Race 3 majority vote'::<25} {majority_rate:>11.1%} {'n/a':>12} {race3_total_tokens:>14,}")
    print()

    cost_per_token = 3.0 / 1_000_000  # $3/M input tokens
    single_cost = single_total_tokens * cost_per_token
    race3_cost = race3_total_tokens * cost_per_token
    cost_per_success_single = single_cost / single_successes if single_successes > 0 else float("inf")
    cost_per_success_race3 = race3_cost / race3_successes if race3_successes > 0 else float("inf")

    print(f"Cost per successful task (Sonnet-class $3/M):")
    print(f"  Single: ${cost_per_success_single:.4f}")
    print(f"  Race-3: ${cost_per_success_race3:.4f}")
    print(f"  Overhead: {(race3_cost / single_cost - 1) * 100:.0f}% more total cost")
    print(f"  Value:    {(race3_rate / single_rate - 1) * 100:+.1f}% higher success rate")
    print()
    print("Conclusion (SIMULATED): Racing 3 agents raises success rate from")
    print(f"{single_rate:.0%} to {race3_rate:.0%} at 3x token cost. Majority voting")
    print(f"({majority_rate:.0%}) adds a safety layer for risky actions.")
    print("Best used selectively on hard tasks where single-agent failure is likely.")

    summary = {
        "experiment": "16_agent_races",
        "simulated": True,
        "agent_probs": agent_probs,
        "total_attempts": total,
        "results": {
            "single_success_rate": round(single_rate, 4),
            "race2_success_rate": round(race2_rate, 4),
            "race3_success_rate": round(race3_rate, 4),
            "majority_vote_rate": round(majority_rate, 4),
            "theoretical_race2": round(theoretical_race2, 4),
            "theoretical_race3": round(theoretical_race3, 4),
        },
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
