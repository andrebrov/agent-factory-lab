#!/usr/bin/env python3
"""
Experiment 24: forgerun — Local microVM Architecture
=======================================================

Protocol-only experiment. forgerun requires KVM on the host machine.
Documents the architecture and provides a test protocol.

PROTOCOL ONLY — no KVM available on this VM.
"""
import json
import os
import argparse


ARCHITECTURE = {
    "components": [
        "Host machine with KVM support",
        "forgerun daemon managing VM lifecycle",
        "Minimal rootfs with dev tools (git, python, node)",
        "Host-side mount: project worktree → VM /workspace",
        "Host-side secret injection via env variables",
        "Host-side egress firewall (iptables/nftables)",
    ],
    "lifecycle": [
        "1. Agent requests new task sandbox",
        "2. forgerun boots microVM from cached rootfs (<1s)",
        "3. Worktree mounted read-write into VM",
        "4. Secrets injected as env vars (host-held)",
        "5. Agent executes task inside VM",
        "6. On completion: extract diff, destroy VM",
        "7. Diff applied to host worktree",
    ],
    "requirements": {
        "host": "Linux with KVM (bare metal or nested virt)",
        "memory": "128-512MB per microVM",
        "disk": "Minimal rootfs ~50-200MB",
        "boot_target": "<500ms (Firecracker-class)",
    },
}

TEST_PROTOCOL = [
    "1. Install forgerun on a KVM-capable Linux host",
    "2. Prepare a minimal rootfs with Python 3.10+ and git",
    "3. Boot a VM and measure time to first shell command",
    "4. Mount a sample worktree and run pytest inside the VM",
    "5. Measure: boot time, mount time, test execution time, destroy time",
    "6. Compare with bare-metal execution of the same task",
    "7. Test secret injection: verify env vars are set inside VM",
    "8. Test egress control: verify blocked domains are unreachable",
    "9. Run 10 sequential tasks, measure amortized overhead",
    "10. Run 5 parallel VMs, measure resource contention",
]


def main():
    parser = argparse.ArgumentParser(description="Experiment 24: forgerun Architecture")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 24: forgerun — Local microVM per Task")
    print("=" * 65)
    print()
    print("--- PROTOCOL ONLY (requires KVM host) ---")
    print()
    print("Architecture:")
    for c in ARCHITECTURE["components"]:
        print(f"  - {c}")
    print()
    print("Task lifecycle:")
    for step in ARCHITECTURE["lifecycle"]:
        print(f"  {step}")
    print()
    print("Requirements:")
    for k, v in ARCHITECTURE["requirements"].items():
        print(f"  {k}: {v}")
    print()
    print("Test protocol (run on KVM host):")
    for step in TEST_PROTOCOL:
        print(f"  {step}")
    print()
    print("Conclusion: Architecture and protocol documented.")
    print("Requires a KVM-capable host for real benchmarking.")

    summary = {
        "experiment": "24_forgerun_local",
        "simulated": True,
        "protocol_only": True,
        "architecture": ARCHITECTURE,
        "test_protocol": TEST_PROTOCOL,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
