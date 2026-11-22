#!/usr/bin/env python3
"""
Experiment 73: Repo Map + "Who's Working Here" Pane
======================================================

Builds on exp 70: shared repo map + a status pane listing active agents
and their files. Both baseline and treatment include REAL file-content
reads measured in tokens.

MEASURED: real tiktoken on actual file contents, map, and status pane.
Status pane logic tested on labeled agent states.
Sample: 4 agents, 3 files, 6 tasks, 3 overlap scenarios.
"""
import json
import os
import argparse
from pathlib import Path

SAMPLE_DIR = Path(__file__).parent.parent / "sample_codebase"
SOURCE_FILES = ["mathlib.py", "test_mathlib.py", "mathlib_fixed.py"]


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


# ── Repo Map (detailed, from exp 70) ─────────────────────────────────

def build_map(sample_dir: Path) -> str:
    parts = ["# Repo Map\n"]
    for fname in SOURCE_FILES:
        fpath = sample_dir / fname
        if not fpath.exists():
            continue
        content = fpath.read_text()
        lines = content.splitlines()
        parts.append(f"## {fname} ({len(lines)} lines)")
        imports = [l for l in lines if l.startswith("import ") or l.startswith("from ")]
        if imports:
            parts.append("Imports: " + ", ".join(i.strip() for i in imports[:5]))
        for line in lines:
            if line.startswith("def "):
                parts.append(f"  {line.rstrip(':')}")
        parts.append("")
    return "\n".join(parts)


# ── Who's Working Here Pane ───────────────────────────────────────────

AGENTS = [
    {"id": "agent-A", "name": "bugfix-factorial", "editing": ["mathlib.py"],
     "status": "running", "task": "Fix factorial bug"},
    {"id": "agent-B", "name": "bugfix-fibonacci", "editing": ["mathlib.py"],
     "status": "running", "task": "Fix fibonacci bug"},
    {"id": "agent-C", "name": "test-writer", "editing": ["test_mathlib.py"],
     "status": "running", "task": "Add edge-case tests"},
    {"id": "agent-D", "name": "reviewer", "editing": [],
     "status": "idle", "task": "Review when ready"},
]

OVERLAP_SCENARIOS = [
    {"agent1": "agent-A", "agent2": "agent-B", "file": "mathlib.py",
     "expected": True, "desc": "Both edit mathlib.py"},
    {"agent1": "agent-A", "agent2": "agent-C", "file": "test_mathlib.py",
     "expected": False, "desc": "A edits mathlib, C edits tests — no overlap"},
    {"agent1": "agent-C", "agent2": "agent-D", "file": "test_mathlib.py",
     "expected": False, "desc": "D is idle, not editing"},
]

LANES = [
    {"agent": "agent-A", "tasks": [
        {"name": "fix_factorial", "needs": ["mathlib.py"]},
    ]},
    {"agent": "agent-B", "tasks": [
        {"name": "fix_fibonacci", "needs": ["mathlib.py"]},
    ]},
    {"agent": "agent-C", "tasks": [
        {"name": "add_tests", "needs": ["test_mathlib.py", "mathlib.py"]},
    ]},
    {"agent": "agent-D", "tasks": [
        {"name": "review_all", "needs": ["mathlib.py", "mathlib_fixed.py", "test_mathlib.py"]},
    ]},
]


def build_status_pane(agents: list) -> str:
    lines = ["# Who's Working Here"]
    for a in agents:
        files = ", ".join(a["editing"]) if a["editing"] else "(none)"
        lines.append(f"  {a['id']:<10} {a['status']:<8} editing: {files:<25} task: {a['task']}")
    return "\n".join(lines)


def detect_overlap(agents: list) -> list:
    """Detect agents editing the same file."""
    file_to_agents = {}
    for a in agents:
        for f in a["editing"]:
            file_to_agents.setdefault(f, []).append(a["id"])
    conflicts = []
    for f, editors in file_to_agents.items():
        if len(editors) > 1:
            conflicts.append({"file": f, "agents": editors})
    return conflicts


def main():
    parser = argparse.ArgumentParser(description="Experiment 73: Map + Who's Working")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken; has_tiktoken = True
    except ImportError: pass
    token_label = "MEASURED (tiktoken)" if has_tiktoken else "ESTIMATED"

    print("=" * 65)
    print("EXPERIMENT 73: Repo Map + Who's Working Here")
    print("=" * 65)
    print(f"Token counting: {token_label}")
    print(f"Agents: {len(AGENTS)}, Files: {len(SOURCE_FILES)}, Lanes: {len(LANES)}")
    print(f"Both baseline and treatment include REAL file-content reads.")
    print()

    # Measure real file tokens
    file_tokens = {}
    for fname in SOURCE_FILES:
        content = (SAMPLE_DIR / fname).read_text()
        file_tokens[fname] = count_tokens(content)
    total_file_tokens = sum(file_tokens.values())

    repo_map = build_map(SAMPLE_DIR)
    map_tokens = count_tokens(repo_map)
    status_pane = build_status_pane(AGENTS)
    status_tokens = count_tokens(status_pane)

    print(f"File tokens ({token_label}):")
    for fname, tok in file_tokens.items():
        print(f"  {fname:<25} {tok:>6}")
    print(f"  {'TOTAL':<25} {total_file_tokens:>6}")
    print(f"  Repo map: {map_tokens} tokens")
    print(f"  Status pane: {status_tokens} tokens")
    print()

    # ── Part A: Token comparison ──
    print("Part A: Token Comparison (baseline includes real file reads)")
    print("-" * 55)

    baseline_total = 0
    treatment_total = 0

    for lane in LANES:
        for task in lane["tasks"]:
            # Baseline: lane reads ALL files
            b_tokens = total_file_tokens
            baseline_total += b_tokens

            # Treatment: lane reads map + status pane + only needed files
            t_tokens = map_tokens + status_tokens
            for needed in task["needs"]:
                t_tokens += file_tokens[needed]  # REAL file content read
            treatment_total += t_tokens

            needed_tok = sum(file_tokens[f] for f in task["needs"])
            print(f"  {lane['agent']:<10} {task['name']:<20} "
                  f"baseline={b_tokens:>5} treatment={t_tokens:>5} "
                  f"(map+status+{'+'.join(task['needs'])})")

    savings = (baseline_total - treatment_total) / baseline_total * 100

    print(f"\n  Baseline total: {baseline_total:,}")
    print(f"  Treatment total: {treatment_total:,}")
    print(f"  Savings: {savings:.1f}%")
    print()

    # ── Part B: Status pane + overlap detection ──
    print("Part B: Who's Working Here — Overlap Detection")
    print("-" * 55)

    detected_conflicts = detect_overlap(AGENTS)
    print(f"  Active agents: {sum(1 for a in AGENTS if a['status'] == 'running')}")
    print(f"  Conflicts detected: {len(detected_conflicts)}")
    for c in detected_conflicts:
        print(f"    {c['file']}: {', '.join(c['agents'])}")
    print()

    # Test overlap scenarios
    print("  Overlap scenario tests:")
    correct = 0
    for scenario in OVERLAP_SCENARIOS:
        a1_files = set(next(a["editing"] for a in AGENTS if a["id"] == scenario["agent1"]))
        a2_files = set(next(a["editing"] for a in AGENTS if a["id"] == scenario["agent2"]))
        overlap = bool(a1_files & a2_files)
        is_correct = overlap == scenario["expected"]
        if is_correct: correct += 1
        icon = "OK" if is_correct else "!!"
        print(f"    [{icon}] {scenario['desc']}: overlap={overlap}, expected={scenario['expected']}")

    overlap_accuracy = correct / len(OVERLAP_SCENARIOS) * 100
    print(f"\n  Overlap detection: {correct}/{len(OVERLAP_SCENARIOS)} ({overlap_accuracy:.0f}%)")
    print()

    # Note: the agent-B editing mathlib.py while agent-A also edits it IS
    # a real conflict that the status pane would surface
    would_prevent = len(detected_conflicts)

    print(f"{'Metric':<40} {'Baseline':>10} {'Treatment':>10}")
    print("-" * 62)
    print(f"{'Total tokens (all lanes, real reads)':<40} {baseline_total:>10,} {treatment_total:>10,}")
    print(f"{'Token savings':<40} {'—':>10} {savings:>9.1f}%")
    print(f"{'Map overhead':<40} {'0':>10} {map_tokens:>10}")
    print(f"{'Status pane overhead':<40} {'0':>10} {status_tokens:>10}")
    print(f"{'Overlapping edits caught':<40} {'0':>10} {would_prevent:>10}")
    print(f"{'Overlap detection accuracy':<40} {'n/a':>10} {overlap_accuracy:>9.0f}%")
    print()

    print(f"Conclusion ({token_label}):")
    print(f"  Savings: {savings:.1f}% with real file reads included.")
    print(f"  Status pane catches {would_prevent} overlapping edit(s).")
    print(f"  Overlap detection: {correct}/{len(OVERLAP_SCENARIOS)} scenarios correct.")
    print(f"  CAVEAT: 3 files is tiny; lanes needing most files save little.")
    print(f"  The reviewer lane (needs all 3 files) gets zero file savings.")
    print(f"  Savings come from lanes needing 1-2 files skipping the rest.")
    print(f"  Sample: {len(AGENTS)} agents, {len(SOURCE_FILES)} files, "
          f"{sum(len(l['tasks']) for l in LANES)} tasks, {len(OVERLAP_SCENARIOS)} overlap tests.")

    summary = {
        "experiment": "73_map_whos_working",
        "simulated": False,
        "includes_real_file_reads": True,
        "token_method": "tiktoken" if has_tiktoken else "word_estimate",
        "agents": len(AGENTS),
        "files": len(SOURCE_FILES),
        "tasks": sum(len(l["tasks"]) for l in LANES),
        "baseline_total": baseline_total,
        "treatment_total": treatment_total,
        "savings_pct": round(savings, 2),
        "map_tokens": map_tokens,
        "status_tokens": status_tokens,
        "overlaps_detected": len(detected_conflicts),
        "overlap_accuracy_pct": round(overlap_accuracy, 2),
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
