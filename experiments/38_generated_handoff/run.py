#!/usr/bin/env python3
"""
Experiment 38: Generated Session Handoff from Git Log + Stale-TODO Scanner
============================================================================

Generates a handoff file from git log + open tasks (no model call), measures
tokens before first relevant edit, and scans for stale TODOs.

REAL EXECUTION: git log, token counting (tiktoken), TODO scanning.
"""
import json
import os
import re
import subprocess
import argparse
from pathlib import Path

REPO_DIR = Path(__file__).parent.parent.parent  # workspace root
SAMPLE_DIR = Path(__file__).parent.parent / "sample_codebase"


def generate_handoff(repo_dir: str, task_spec: str) -> str:
    """Generate a handoff from git log + task spec, no model call."""
    # Recent git log
    result = subprocess.run(
        ["git", "-C", repo_dir, "log", "--oneline", "-20"],
        capture_output=True, text=True,
    )
    git_log = result.stdout.strip()

    # Current branch
    result = subprocess.run(
        ["git", "-C", repo_dir, "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True,
    )
    branch = result.stdout.strip()

    # Changed files in last commit
    result = subprocess.run(
        ["git", "-C", repo_dir, "diff", "--name-only", "HEAD~1", "HEAD"],
        capture_output=True, text=True,
    )
    changed = result.stdout.strip()

    handoff = f"""# Generated Handoff (no model call)

## Current State
- Branch: {branch}
- Last 20 commits:
{git_log}

## Recent Changes
{changed}

## Task
{task_spec}

## Notes
- Generated automatically from git log and task spec
- No LLM call required
"""
    return handoff


def scan_stale_todos(directory: str) -> list:
    """Scan for TODO/FIXME/HACK comments and flag potentially stale ones."""
    stale = []
    stale_patterns = [
        r"TODO.*(?:later|eventually|someday|future|v2|phase\s*2)",
        r"FIXME.*(?:workaround|temporary|temp\b|hack)",
        r"HACK",
        r"XXX",
    ]
    for root, _, files in os.walk(directory):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            filepath = Path(root) / fname
            try:
                content = filepath.read_text()
            except (OSError, UnicodeDecodeError):
                continue
            for i, line in enumerate(content.splitlines(), 1):
                for pattern in stale_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        stale.append({
                            "file": str(filepath.relative_to(directory)),
                            "line": i,
                            "text": line.strip()[:100],
                            "pattern": pattern.split(".*")[0],
                        })
                        break
    return stale


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def main():
    parser = argparse.ArgumentParser(description="Experiment 38: Generated Handoff")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken
        has_tiktoken = True
    except ImportError:
        pass
    token_label = "MEASURED (tiktoken)" if has_tiktoken else "ESTIMATED"

    print("=" * 65)
    print("EXPERIMENT 38: Generated Session Handoff + Stale-TODO Scanner")
    print("=" * 65)
    print(f"Token counting: {token_label}")
    print()
    print("--- REAL EXECUTION ---")
    print()

    task_spec = "Fix the 10 seeded bugs in experiments/sample_codebase/mathlib.py"

    # Phase 1: Generate handoff
    print("Phase 1: Generate handoff from git log (no model call)")
    print("-" * 55)
    handoff = generate_handoff(str(REPO_DIR), task_spec)
    handoff_tokens = count_tokens(handoff)
    print(f"  Handoff generated: {handoff_tokens} tokens, "
          f"{len(handoff.splitlines())} lines")
    print()

    # Phase 2: Compare context tokens with and without handoff
    print("Phase 2: Context tokens before first edit")
    print("-" * 55)

    # Without handoff: agent reads all files to understand context
    all_files_content = ""
    for fname in ["mathlib.py", "test_mathlib.py", "mathlib_fixed.py"]:
        fpath = SAMPLE_DIR / fname
        if fpath.exists():
            all_files_content += f"\n# {fname}\n{fpath.read_text()}\n"
    all_files_tokens = count_tokens(all_files_content)

    # With handoff: agent reads handoff + target file only
    target_content = (SAMPLE_DIR / "mathlib.py").read_text()
    with_handoff_tokens = handoff_tokens + count_tokens(target_content)

    savings = all_files_tokens - with_handoff_tokens
    savings_pct = savings / all_files_tokens * 100 if all_files_tokens > 0 else 0

    print(f"  Without handoff (read all files): {all_files_tokens:,} tokens")
    print(f"  With handoff (handoff + target):  {with_handoff_tokens:,} tokens")
    print(f"  Token savings: {savings:,} ({savings_pct:.1f}%)")
    print()

    # Phase 3: Stale-TODO scanner
    print("Phase 3: Stale-TODO scanner")
    print("-" * 55)
    stale_todos = scan_stale_todos(str(SAMPLE_DIR))
    # Also scan the experiments directory for a broader sample
    exp_todos = scan_stale_todos(str(Path(__file__).parent.parent))

    all_todos = stale_todos + exp_todos
    print(f"  Stale TODOs in sample_codebase: {len(stale_todos)}")
    print(f"  Stale TODOs in experiments/:    {len(exp_todos)}")
    for todo in all_todos[:10]:
        print(f"    [{todo['pattern']}] {todo['file']}:{todo['line']}: {todo['text'][:60]}")

    wasted_per_todo = 500  # estimated tokens wasted chasing one stale TODO
    potential_waste = len(all_todos) * wasted_per_todo
    print(f"\n  Potential token waste from stale TODOs: ~{potential_waste:,} tokens "
          f"({len(all_todos)} × {wasted_per_todo} est.)")
    print()

    print(f"Conclusion ({token_label}): Generated handoff costs {handoff_tokens} tokens")
    print(f"and saves {savings_pct:.0f}% vs reading all files. The stale-TODO scanner")
    print(f"found {len(all_todos)} potentially stale markers. Both require zero LLM calls.")

    summary = {
        "experiment": "38_generated_handoff",
        "simulated": False,
        "token_method": "tiktoken" if has_tiktoken else "word_estimate",
        "handoff_tokens": handoff_tokens,
        "handoff_lines": len(handoff.splitlines()),
        "without_handoff_tokens": all_files_tokens,
        "with_handoff_tokens": with_handoff_tokens,
        "token_savings_pct": round(savings_pct, 2),
        "stale_todos_found": len(all_todos),
        "stale_todo_details": all_todos[:20],
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
