#!/usr/bin/env python3
"""
Experiment 18: Firecracker microVM per Task — Cost Model
==========================================================

Models the cost of one-VM-per-task vs reusable-VM vs bare-metal for
typical coding-agent task durations. Firecracker cannot run on this VM
(no KVM), so this is a cost/protocol exercise.

ESTIMATED — cost model only. Protocol provided for real benchmarking.
"""
import json
import os
import argparse

TASK_DURATIONS_SEC = [5, 10, 30, 60, 120, 300, 600]

PROVIDERS = {
    "firecracker_cloud": {
        "boot_sec": 0.125,
        "destroy_sec": 0.05,
        "cost_per_sec": 0.0001,    # ~$0.36/hr for a small instance
        "setup_overhead_sec": 2.0,  # image pull, network setup
    },
    "lizard_microvm": {
        "boot_sec": 0.238,
        "destroy_sec": 0.05,
        "cost_per_sec": 0.00008,   # per-second billing, vendor claim
        "setup_overhead_sec": 0.5,
    },
    "docker_container": {
        "boot_sec": 1.0,
        "destroy_sec": 0.3,
        "cost_per_sec": 0.00005,   # lighter than VM
        "setup_overhead_sec": 0.5,
    },
    "bubblewrap_sandbox": {
        "boot_sec": 0.01,
        "destroy_sec": 0.005,
        "cost_per_sec": 0.0,       # OS-level, no extra cost
        "setup_overhead_sec": 0.0,
    },
}


def main():
    parser = argparse.ArgumentParser(description="Experiment 18: Firecracker Cost Model")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 70)
    print("EXPERIMENT 18: Firecracker microVM per Task — Cost Model")
    print("=" * 70)
    print()
    print("--- ALL NUMBERS ARE ESTIMATED (vendor claims + public pricing) ---")
    print()

    header = f"{'Duration':>8}  "
    for p in PROVIDERS:
        header += f"{'Total(s)':>9} {'Cost($)':>9}  "
    print(header)
    print("-" * len(header))

    results = []
    for dur in TASK_DURATIONS_SEC:
        row = f"{dur:>7}s  "
        row_data = {"task_duration_sec": dur}
        for name, p in PROVIDERS.items():
            total_time = p["setup_overhead_sec"] + p["boot_sec"] + dur + p["destroy_sec"]
            cost = (p["boot_sec"] + dur + p["destroy_sec"]) * p["cost_per_sec"]
            row += f"{total_time:>9.2f} ${cost:>8.5f}  "
            row_data[name] = {"total_sec": round(total_time, 3), "cost": round(cost, 6)}
        print(row)
        results.append(row_data)

    print()
    print("Overhead comparison for a 30s task:")
    for name, p in PROVIDERS.items():
        overhead = p["setup_overhead_sec"] + p["boot_sec"] + p["destroy_sec"]
        pct = overhead / 30 * 100
        print(f"  {name:<25} overhead: {overhead:.3f}s ({pct:.1f}% of task)")

    print()
    print("Protocol for real benchmarking (requires KVM host):")
    print("  1. Boot Firecracker with a minimal rootfs + kernel")
    print("  2. Measure: time from API call to first shell command in VM")
    print("  3. Run a sample task (clone repo, run pytest)")
    print("  4. Measure: time from shutdown signal to VM destroyed")
    print("  5. Repeat 100x, report p50/p95/p99")
    print()
    print("Conclusion (ESTIMATED): Bubblewrap adds near-zero overhead.")
    print("Firecracker/Lizard add 0.1-2.5s, acceptable for tasks >10s.")
    print("The isolation-vs-overhead tradeoff favors tiered routing.")

    summary = {
        "experiment": "18_firecracker_microvm",
        "simulated": True,
        "providers": {k: v for k, v in PROVIDERS.items()},
        "task_results": results,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
