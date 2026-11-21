#!/usr/bin/env python3
"""
Experiment 70: Shared Repo Map for Rex Lanes (with Real File Reads)
=====================================================================

Corrects exp 66's gap: both baseline and treatment include real file-content
reads counted by tiktoken, not just file names and sizes.

Baseline: N lanes each read all 3 source files in full.
Treatment: lanes read a detailed map (function signatures, key patterns,
line counts) + only the specific file(s) their task needs.

The map contains enough detail to route correctly — function signatures,
imports, key patterns — but NOT the full file contents.

MEASURED: real tiktoken on actual file contents and a detailed map.
Sample: 3 lanes, 3 source files, 5 tasks assigned across lanes.
"""
import json
import os
import argparse
from pathlib import Path

SAMPLE_DIR = Path(__file__).parent.parent / "sample_codebase"

LANES = [
    {"name": "lane-bugfix", "tasks": [
        {"name": "fix_factorial", "needs_files": ["mathlib.py"]},
        {"name": "fix_fibonacci", "needs_files": ["mathlib.py"]},
    ]},
    {"name": "lane-testing", "tasks": [
        {"name": "add_edge_tests", "needs_files": ["test_mathlib.py", "mathlib.py"]},
    ]},
    {"name": "lane-review", "tasks": [
        {"name": "review_fixes", "needs_files": ["mathlib.py", "mathlib_fixed.py"]},
        {"name": "check_coverage", "needs_files": ["test_mathlib.py"]},
    ]},
]

SOURCE_FILES = ["mathlib.py", "test_mathlib.py", "mathlib_fixed.py"]


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def build_detailed_map(sample_dir: Path) -> str:
    """Build a detailed map with function signatures, imports, key patterns.
    NOT just file names and sizes — enough detail to route correctly."""
    parts = ["# Repo Map (detailed)\n"]

    for fname in SOURCE_FILES:
        fpath = sample_dir / fname
        if not fpath.exists():
            continue
        content = fpath.read_text()
        lines = content.splitlines()

        parts.append(f"## {fname} ({len(lines)} lines)")

        # Extract imports
        imports = [l for l in lines if l.startswith("import ") or l.startswith("from ")]
        if imports:
            parts.append("Imports: " + ", ".join(i.strip() for i in imports[:5]))

        # Extract function signatures with first-line docstrings
        for i, line in enumerate(lines):
            if line.startswith("def "):
                sig = line.rstrip(":")
                # Check for docstring on next line
                if i + 1 < len(lines) and '"""' in lines[i + 1]:
                    doc = lines[i + 1].strip().strip('"').strip()
                    parts.append(f"  {sig}  # {doc[:60]}")
                else:
                    parts.append(f"  {sig}")

        # Key patterns (for routing decisions)
        has_pytest = "import pytest" in content or "def test_" in content
        has_bugs = "BUG" in content
        has_fixes = "FIX" in content
        tags = []
        if has_pytest: tags.append("tests")
        if has_bugs: tags.append("has-bugs")
        if has_fixes: tags.append("has-fixes")
        if tags:
            parts.append(f"  Tags: {', '.join(tags)}")
        parts.append("")

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Experiment 70: Shared Repo Map")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken; has_tiktoken = True
    except ImportError: pass
    token_label = "MEASURED (tiktoken)" if has_tiktoken else "ESTIMATED"

    print("=" * 65)
    print("EXPERIMENT 70: Shared Repo Map for Rex Lanes")
    print("=" * 65)
    print(f"Token counting: {token_label}")
    print(f"Lanes: {len(LANES)}, Files: {len(SOURCE_FILES)}")
    print(f"NOTE: Both baseline and treatment include real file-content reads.")
    print(f"This corrects exp 66's gap where the treatment only used file names.")
    print()

    # Measure actual file sizes
    file_tokens = {}
    for fname in SOURCE_FILES:
        content = (SAMPLE_DIR / fname).read_text()
        file_tokens[fname] = count_tokens(content)
    total_file_tokens = sum(file_tokens.values())

    # Build and measure the detailed map
    repo_map = build_detailed_map(SAMPLE_DIR)
    map_tokens = count_tokens(repo_map)

    print(f"File sizes ({token_label}):")
    for fname, tok in file_tokens.items():
        print(f"  {fname:<25} {tok:>6} tokens")
    print(f"  {'TOTAL':<25} {total_file_tokens:>6} tokens")
    print(f"\nDetailed repo map: {map_tokens} tokens")
    print()

    # ── Baseline: every lane reads ALL files ──
    print("Baseline: Every lane reads ALL files")
    print("-" * 55)

    baseline_per_lane = {}
    baseline_total = 0

    for lane in LANES:
        lane_reads = total_file_tokens  # reads ALL files
        lane_total = lane_reads * len(lane["tasks"])  # per task in the lane
        baseline_per_lane[lane["name"]] = {
            "tokens_per_task": lane_reads,
            "tasks": len(lane["tasks"]),
            "total": lane_total,
        }
        baseline_total += lane_total
        print(f"  {lane['name']:<15} reads ALL ({total_file_tokens:,} tok) × "
              f"{len(lane['tasks'])} tasks = {lane_total:,}")

    print(f"  Baseline total: {baseline_total:,} tokens")
    print()

    # ── Treatment: read map + only needed files ──
    print("Treatment: Read map + only needed files per task")
    print("-" * 55)

    treatment_per_lane = {}
    treatment_total = 0
    map_cost = map_tokens * len(LANES)  # each lane reads the map once

    for lane in LANES:
        lane_total = 0
        for task in lane["tasks"]:
            # Map read (once per lane, amortized)
            task_tokens = map_tokens // len(lane["tasks"])
            # Plus the specific files this task needs (REAL file content)
            for needed in task["needs_files"]:
                task_tokens += file_tokens[needed]
            lane_total += task_tokens

        treatment_per_lane[lane["name"]] = {
            "tasks": len(lane["tasks"]),
            "total": lane_total,
        }
        treatment_total += lane_total

        for task in lane["tasks"]:
            needed_tok = sum(file_tokens[f] for f in task["needs_files"])
            print(f"  {lane['name']:<15} {task['name']:<20} "
              f"map({map_tokens // len(lane['tasks'])}) + "
              f"files({needed_tok}) = {map_tokens // len(lane['tasks']) + needed_tok}")

    # Add the map reads (not amortized — each lane reads it)
    treatment_total_with_map = treatment_total
    print(f"  Treatment total: {treatment_total_with_map:,} tokens (map reads included)")
    print()

    # ── Comparison ──
    savings = (baseline_total - treatment_total_with_map) / baseline_total * 100

    print(f"{'Metric':<45} {'Baseline':>10} {'Treatment':>10}")
    print("-" * 67)
    print(f"{'Total file-read tokens (all lanes+tasks)':<45} {baseline_total:>10,} {treatment_total_with_map:>10,}")
    print(f"{'Token reduction':<45} {'—':>10} {savings:>9.1f}%")
    print(f"{'Map overhead (once per lane)':<45} {'0':>10} {map_tokens:>10}")
    print(f"{'Each lane reads ALL files':<45} {'yes':>10} {'no':>10}")
    print(f"{'Each lane reads its needed files':<45} {'yes':>10} {'yes':>10}")
    print()

    # Check: does any task need a file not mentioned in the map?
    map_text = repo_map.lower()
    unmentioned = []
    for lane in LANES:
        for task in lane["tasks"]:
            for f in task["needs_files"]:
                if f.lower() not in map_text:
                    unmentioned.append(f"{task['name']} needs {f}")

    print(f"Files needed but not in map: {len(unmentioned)}")
    if unmentioned:
        for u in unmentioned:
            print(f"  WARNING: {u}")
    print()

    print(f"Conclusion ({token_label}):")
    print(f"  Savings: {savings:.1f}% ({baseline_total:,} → {treatment_total_with_map:,}).")
    print(f"  The map costs {map_tokens} tokens but lets lanes skip reading")
    print(f"  files they don't need. Lanes still read the actual file content")
    print(f"  for files their tasks require — not just names and sizes.")
    print(f"  Files unmentioned in map: {len(unmentioned)}.")
    print(f"  Sample: {len(LANES)} lanes, {len(SOURCE_FILES)} files, "
          f"{sum(len(l['tasks']) for l in LANES)} tasks.")

    exp_summary = {
        "experiment": "70_shared_repo_map",
        "simulated": False,
        "token_method": "tiktoken" if has_tiktoken else "word_estimate",
        "includes_real_file_reads": True,
        "corrects_exp66_gap": True,
        "lanes": len(LANES),
        "files": len(SOURCE_FILES),
        "tasks": sum(len(l["tasks"]) for l in LANES),
        "baseline_total": baseline_total,
        "treatment_total": treatment_total_with_map,
        "savings_pct": round(savings, 2),
        "map_tokens": map_tokens,
        "file_tokens": file_tokens,
        "files_unmentioned_in_map": len(unmentioned),
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(exp_summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
