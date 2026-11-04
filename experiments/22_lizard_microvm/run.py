#!/usr/bin/env python3
"""
Experiment 22: Lizard microVM — Cost Model for Per-Second Billing
===================================================================

Models cost savings from per-second billing vs per-minute/per-hour
for typical agent task durations.

ESTIMATED — vendor claims, no actual Lizard access.
"""
import json
import os
import argparse

TASK_DURATIONS_SEC = [3, 5, 10, 30, 60, 120, 300, 600]

BILLING_MODELS = {
    "per_second": {"granularity_sec": 1, "rate_per_sec": 0.00008, "min_charge_sec": 1},
    "per_minute": {"granularity_sec": 60, "rate_per_sec": 0.00007, "min_charge_sec": 60},
    "per_hour":   {"granularity_sec": 3600, "rate_per_sec": 0.00005, "min_charge_sec": 3600},
}


def compute_cost(duration_sec: float, model: dict) -> float:
    billable = max(duration_sec, model["min_charge_sec"])
    granularity = model["granularity_sec"]
    rounded_up = ((int(billable) + granularity - 1) // granularity) * granularity
    return rounded_up * model["rate_per_sec"]


def main():
    parser = argparse.ArgumentParser(description="Experiment 22: Lizard Cost Model")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 22: Lizard microVM — Per-Second Billing Model")
    print("=" * 65)
    print()
    print("--- ALL NUMBERS ARE ESTIMATED (vendor claims) ---")
    print()
    print(f"{'Duration':>8}  {'Per-Second':>12} {'Per-Minute':>12} {'Per-Hour':>12}  {'Savings':>10}")
    print("-" * 62)

    results = []
    for dur in TASK_DURATIONS_SEC:
        costs = {name: compute_cost(dur, model) for name, model in BILLING_MODELS.items()}
        savings = (costs["per_hour"] - costs["per_second"]) / costs["per_hour"] * 100
        print(f"{dur:>7}s  ${costs['per_second']:>11.5f} ${costs['per_minute']:>11.5f} "
              f"${costs['per_hour']:>11.5f}  {savings:>9.1f}%")
        results.append({"duration_sec": dur, "costs": costs, "savings_vs_hourly_pct": round(savings, 2)})

    print()
    avg_savings = sum(r["savings_vs_hourly_pct"] for r in results) / len(results)
    print(f"Average savings vs hourly billing: {avg_savings:.1f}%")
    print()
    print(f"Lizard claimed boot time: 238ms")
    print(f"Lizard claimed parallel capacity: 100 VMs")
    print(f"Lizard claimed paused cost: $0 (free while paused)")
    print()
    print("Protocol for real benchmarking (requires Lizard account):")
    print("  1. Create a VM with a minimal image")
    print("  2. Measure: time from API call to SSH-ready")
    print("  3. Run a sample task, record wall-clock and billed time")
    print("  4. Pause VM, verify $0 billing, resume and measure latency")
    print("  5. Repeat with 10/50/100 parallel VMs")

    summary = {
        "experiment": "22_lizard_microvm",
        "simulated": True,
        "billing_results": results,
        "avg_savings_vs_hourly_pct": round(avg_savings, 2),
        "vendor_claims": {"boot_ms": 238, "parallel_max": 100, "paused_cost": 0},
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
