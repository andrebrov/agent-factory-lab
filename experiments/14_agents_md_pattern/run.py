#!/usr/bin/env python3
"""
Experiment 14: AGENTS.md Single Source vs Duplicated Configs
==============================================================

Simulates config drift in single-source (AGENTS.md + pointer) vs duplicated
(separate files per agent) setups over a series of edits.

SIMULATED — models real-world config evolution.
"""
import json
import os
import random
import argparse
import hashlib


INITIAL_RULES = [
    "Always run tests before marking done",
    "Use TypeScript strict mode",
    "Max 500 lines per file",
    "Write docstrings for public functions",
    "Use conventional commits",
    "No console.log in production code",
    "Prefer const over let",
    "Handle all error cases explicitly",
    "Use async/await over callbacks",
    "Add types to all function parameters",
]

NUM_AGENTS = 4
NUM_EDITS = 30


def simulate_single_source(rules: list, num_edits: int, seed: int) -> dict:
    random.seed(seed)
    current = list(rules)
    edit_log = []

    for i in range(num_edits):
        action = random.choice(["modify", "add", "remove"])
        if action == "modify" and current:
            idx = random.randint(0, len(current) - 1)
            current[idx] = current[idx] + f" (updated-{i})"
            edit_log.append(f"edit {i}: modified rule {idx}")
        elif action == "add":
            current.append(f"New rule added at edit {i}")
            edit_log.append(f"edit {i}: added rule")
        elif action == "remove" and len(current) > 3:
            idx = random.randint(0, len(current) - 1)
            removed = current.pop(idx)
            edit_log.append(f"edit {i}: removed '{removed[:30]}...'")

    return {
        "final_rules": current,
        "edits": len(edit_log),
        "divergent_copies": 0,
        "max_drift": 0,
    }


def simulate_duplicated(rules: list, num_agents: int, num_edits: int, seed: int) -> dict:
    random.seed(seed + 1000)
    copies = {f"agent_{i}": list(rules) for i in range(num_agents)}
    edit_log = []

    for i in range(num_edits):
        target_agent = f"agent_{random.randint(0, num_agents - 1)}"
        action = random.choice(["modify", "add", "remove"])
        current = copies[target_agent]

        if action == "modify" and current:
            idx = random.randint(0, len(current) - 1)
            current[idx] = current[idx] + f" (v{i})"
            edit_log.append(f"edit {i}: modified {target_agent} rule {idx}")
        elif action == "add":
            current.append(f"Rule added in {target_agent} edit {i}")
            edit_log.append(f"edit {i}: added to {target_agent}")
        elif action == "remove" and len(current) > 3:
            idx = random.randint(0, len(current) - 1)
            current.pop(idx)
            edit_log.append(f"edit {i}: removed from {target_agent}")

        propagate = random.random() < 0.3
        if propagate:
            other = random.choice([a for a in copies if a != target_agent])
            copies[other] = list(current)
            edit_log.append(f"  -> propagated to {other}")

    hashes = {}
    for agent, r in copies.items():
        h = hashlib.md5("\n".join(r).encode()).hexdigest()[:8]
        hashes[agent] = h

    unique_versions = len(set(hashes.values()))
    divergent = unique_versions - 1

    pairs_compared = 0
    total_drift = 0
    for i, a1 in enumerate(list(copies.keys())):
        for a2 in list(copies.keys())[i + 1:]:
            set1 = set(copies[a1])
            set2 = set(copies[a2])
            drift = len(set1.symmetric_difference(set2))
            total_drift += drift
            pairs_compared += 1

    avg_drift = total_drift / pairs_compared if pairs_compared > 0 else 0

    return {
        "final_copies": {k: len(v) for k, v in copies.items()},
        "edits": len(edit_log),
        "unique_versions": unique_versions,
        "divergent_copies": divergent,
        "avg_drift_rules": round(avg_drift, 1),
    }


def main():
    parser = argparse.ArgumentParser(description="Experiment 14: AGENTS.md Pattern")
    parser.add_argument("--edits", type=int, default=NUM_EDITS)
    parser.add_argument("--agents", type=int, default=NUM_AGENTS)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    single = simulate_single_source(INITIAL_RULES, args.edits, args.seed)
    duped = simulate_duplicated(INITIAL_RULES, args.agents, args.edits, args.seed)

    print("=" * 65)
    print("EXPERIMENT 14: AGENTS.md Single Source vs Duplicated Configs")
    print("=" * 65)
    print(f"Initial rules: {len(INITIAL_RULES)}, Edits: {args.edits}, Agents: {args.agents}")
    print()
    print("--- ALL NUMBERS ARE SIMULATED ---")
    print()
    print(f"{'Metric':<35} {'Single Source':>14} {'Duplicated':>12}")
    print("-" * 63)
    print(f"{'Config versions after edits':<35} {1:>14} {duped['unique_versions']:>12}")
    print(f"{'Divergent copies':<35} {single['divergent_copies']:>14} {duped['divergent_copies']:>12}")
    print(f"{'Avg rule drift between agents':<35} {0:>14} {duped['avg_drift_rules']:>12}")
    print(f"{'Risk of conflicting instructions':<35} {'None':>14} {'High':>12}")
    print()

    print("Conclusion (SIMULATED): Single-source AGENTS.md eliminates config")
    print(f"drift entirely. Duplicated configs diverged into {duped['unique_versions']} unique versions")
    print(f"with an average drift of {duped['avg_drift_rules']} rules between agent pairs.")

    summary = {
        "experiment": "14_agents_md_pattern",
        "simulated": True,
        "initial_rules": len(INITIAL_RULES),
        "edits": args.edits,
        "agents": args.agents,
        "single_source": {"divergent_copies": 0, "drift": 0},
        "duplicated": {
            "unique_versions": duped["unique_versions"],
            "divergent_copies": duped["divergent_copies"],
            "avg_drift_rules": duped["avg_drift_rules"],
        },
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
