#!/usr/bin/env python3
"""
Experiment 32: Cross-Session Handoff Accept + Context Health
==============================================================

Simulates task handoffs between sessions with and without an explicit
accept gate. Measures discard/respawn rate and context utilization.

SIMULATED — Monte Carlo with configurable parameters.
Context health metrics use realistic token budgets.
"""
import json
import os
import random
import argparse

CONTEXT_BUDGET = 200_000  # tokens
CACHE_TTL_SEC = 300       # 5 minutes
HANDOFF_SIZE = 500        # tokens for HANDOFF.md
NUM_TASKS = 100
NUM_TRIALS = 500


def simulate_handoff_without_accept(
    context_used_pct: float, idle_sec: float, p_discard: float
) -> dict:
    """Without accept gate: receiver may silently discard and respawn."""
    discarded = random.random() < p_discard
    cache_expired = idle_sec > CACHE_TTL_SEC
    return {
        "accepted": not discarded,
        "discarded": discarded,
        "respawned": discarded,
        "cache_expired": cache_expired,
        "wasted_tokens": int(context_used_pct * CONTEXT_BUDGET) if discarded else 0,
    }


def simulate_handoff_with_accept(
    context_used_pct: float, idle_sec: float, p_discard: float
) -> dict:
    """With accept gate: receiver checks context health before accepting."""
    cache_expired = idle_sec > CACHE_TTL_SEC
    context_healthy = context_used_pct < 0.80
    budget_ok = (1.0 - context_used_pct) * CONTEXT_BUDGET > HANDOFF_SIZE * 2

    should_accept = context_healthy and budget_ok and not cache_expired
    accepted = should_accept

    if not accepted:
        return {
            "accepted": False,
            "discarded": False,
            "respawned": True,
            "reason": ("cache_expired" if cache_expired
                       else "context_full" if not context_healthy
                       else "budget_low"),
            "cache_expired": cache_expired,
            "wasted_tokens": 0,
        }

    return {
        "accepted": True,
        "discarded": False,
        "respawned": False,
        "cache_expired": False,
        "wasted_tokens": 0,
    }


def main():
    parser = argparse.ArgumentParser(description="Experiment 32: Handoff Accept")
    parser.add_argument("--trials", type=int, default=NUM_TRIALS)
    parser.add_argument("--tasks", type=int, default=NUM_TASKS)
    parser.add_argument("--p-discard", type=float, default=0.30,
                        help="Probability of silent discard without accept gate")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    random.seed(args.seed)
    total = args.trials * args.tasks

    without_discards = 0
    without_wasted = 0
    with_respawns = 0
    with_respawn_reasons = {"cache_expired": 0, "context_full": 0, "budget_low": 0}
    with_wasted = 0

    for _ in range(args.trials):
        for _ in range(args.tasks):
            context_pct = random.uniform(0.2, 0.95)
            idle = random.uniform(0, 600)

            wo = simulate_handoff_without_accept(context_pct, idle, args.p_discard)
            wi = simulate_handoff_with_accept(context_pct, idle, args.p_discard)

            if wo["discarded"]:
                without_discards += 1
                without_wasted += wo["wasted_tokens"]

            if wi["respawned"]:
                with_respawns += 1
                reason = wi.get("reason", "unknown")
                if reason in with_respawn_reasons:
                    with_respawn_reasons[reason] += 1
            with_wasted += wi["wasted_tokens"]

    without_discard_rate = without_discards / total
    with_respawn_rate = with_respawns / total
    wasted_reduction = (
        (without_wasted - with_wasted) / without_wasted * 100
        if without_wasted > 0 else 0
    )

    print("=" * 65)
    print("EXPERIMENT 32: Cross-Session Handoff Accept + Context Health")
    print("=" * 65)
    print(f"Trials: {args.trials} × {args.tasks} tasks = {total:,}")
    print(f"P(silent discard without gate): {args.p_discard}")
    print(f"Context budget: {CONTEXT_BUDGET:,} tokens, cache TTL: {CACHE_TTL_SEC}s")
    print()
    print("--- ALL NUMBERS ARE SIMULATED ---")
    print()

    print(f"{'Metric':<35} {'No Gate':>12} {'With Gate':>12}")
    print("-" * 61)
    print(f"{'Discard/respawn rate':<35} {without_discard_rate:>11.1%} {with_respawn_rate:>11.1%}")
    print(f"{'Total discards/respawns':<35} {without_discards:>12,} {with_respawns:>12,}")
    print(f"{'Wasted tokens (from discards)':<35} {without_wasted:>12,} {with_wasted:>12,}")
    print(f"{'Wasted token reduction':<35} {'baseline':>12} {wasted_reduction:>11.1f}%")
    print()

    print("With-gate respawn reasons:")
    for reason, count in sorted(with_respawn_reasons.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        print(f"  {reason:<25} {count:>8} ({pct:.1f}%)")
    print()

    print("Context health metrics (per handoff):")
    print(f"  Context budget:     {CONTEXT_BUDGET:>10,} tokens")
    print(f"  Handoff overhead:   {HANDOFF_SIZE:>10} tokens")
    print(f"  Cache TTL:          {CACHE_TTL_SEC:>10}s")
    print(f"  Accept threshold:   <80% context used, budget > {HANDOFF_SIZE * 2} tokens")
    print()

    print("Conclusion (SIMULATED): The accept gate eliminates silent discards")
    print(f"({without_discard_rate:.0%} → 0%) by making respawns explicit and justified.")
    print(f"Informed respawns still occur ({with_respawn_rate:.0%}) but waste no tokens")
    print("because the gate rejects before work begins.")

    summary = {
        "experiment": "32_handoff_accept",
        "simulated": True,
        "parameters": {
            "trials": args.trials, "tasks": args.tasks,
            "p_discard": args.p_discard,
            "context_budget": CONTEXT_BUDGET, "cache_ttl": CACHE_TTL_SEC,
        },
        "without_gate": {
            "discard_rate": round(without_discard_rate, 4),
            "total_discards": without_discards,
            "wasted_tokens": without_wasted,
        },
        "with_gate": {
            "respawn_rate": round(with_respawn_rate, 4),
            "total_respawns": with_respawns,
            "wasted_tokens": with_wasted,
            "respawn_reasons": with_respawn_reasons,
        },
        "wasted_token_reduction_pct": round(wasted_reduction, 2),
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
