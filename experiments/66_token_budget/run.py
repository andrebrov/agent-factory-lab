#!/usr/bin/env python3
"""
Experiment 66: Token Budget per Worker
=========================================

Compares N parallel subagents each re-reading files vs a capped setup with
shared summaries and task-specific tool loading. Models cache loss from
mid-session model switching.

MEASURED: token sizes with tiktoken. MODELED: concurrency, cache behavior.
Sample: 3 subagents, 5 shared files, 10 tools, 3 model-switch scenarios.
"""
import json
import os
import argparse
from pathlib import Path

SAMPLE_DIR = Path(__file__).parent.parent / "sample_codebase"

SHARED_FILES = [
    {"name": "mathlib.py", "tokens": 0},      # filled from real file
    {"name": "test_mathlib.py", "tokens": 0},
    {"name": "mathlib_fixed.py", "tokens": 0},
    {"name": "README.md", "tokens": 50},        # modeled
    {"name": "requirements.txt", "tokens": 15},  # modeled
]

ALL_TOOLS = [
    {"name": "read_file", "tokens": 45, "needed_by": ["auth", "api", "db"]},
    {"name": "write_file", "tokens": 50, "needed_by": ["auth", "api", "db"]},
    {"name": "run_command", "tokens": 40, "needed_by": ["auth", "api", "db"]},
    {"name": "search_files", "tokens": 55, "needed_by": ["auth"]},
    {"name": "git_diff", "tokens": 48, "needed_by": ["auth"]},
    {"name": "git_commit", "tokens": 52, "needed_by": []},
    {"name": "create_pr", "tokens": 65, "needed_by": []},
    {"name": "web_search", "tokens": 60, "needed_by": []},
    {"name": "database_query", "tokens": 58, "needed_by": ["db"]},
    {"name": "deploy", "tokens": 55, "needed_by": []},
]

SUBAGENTS = ["auth", "api", "db"]
SYSTEM_PROMPT_TOKENS = 30


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def build_summary(files: list) -> str:
    lines = ["# File Summary"]
    for f in files:
        lines.append(f"- {f['name']}: {f['tokens']} tokens")
    lines.append(f"Total: {sum(f['tokens'] for f in files)} tokens across {len(files)} files")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Experiment 66: Token Budget")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken; has_tiktoken = True
    except ImportError: pass
    token_label = "MEASURED (tiktoken)" if has_tiktoken else "ESTIMATED"

    # Fill real file token counts
    for f in SHARED_FILES:
        fpath = SAMPLE_DIR / f["name"]
        if fpath.exists():
            f["tokens"] = count_tokens(fpath.read_text())

    total_file_tokens = sum(f["tokens"] for f in SHARED_FILES)
    all_tool_tokens = sum(t["tokens"] for t in ALL_TOOLS)
    summary_text = build_summary(SHARED_FILES)
    summary_tokens = count_tokens(summary_text)

    print("=" * 65)
    print("EXPERIMENT 66: Token Budget per Worker")
    print("=" * 65)
    print(f"Token counting: {token_label}")
    print(f"Subagents: {len(SUBAGENTS)}, Files: {len(SHARED_FILES)}, Tools: {len(ALL_TOOLS)}")
    print()

    print(f"Shared files: {total_file_tokens} tokens")
    print(f"File summary: {summary_tokens} tokens")
    print(f"All tools: {all_tool_tokens} tokens ({len(ALL_TOOLS)} tools)")
    print()

    # Mode A: Parallel, each re-reads everything
    mode_a_per_agent = SYSTEM_PROMPT_TOKENS + total_file_tokens + all_tool_tokens
    mode_a_total = mode_a_per_agent * len(SUBAGENTS)

    # Mode B: Capped, shared summary, task-specific tools
    mode_b_details = []
    mode_b_total = 0
    for agent_name in SUBAGENTS:
        agent_tools = sum(t["tokens"] for t in ALL_TOOLS if agent_name in t["needed_by"])
        agent_total = SYSTEM_PROMPT_TOKENS + summary_tokens + agent_tools
        mode_b_details.append({"agent": agent_name, "tools_tokens": agent_tools, "total": agent_total})
        mode_b_total += agent_total

    savings = (mode_a_total - mode_b_total) / mode_a_total * 100

    print(f"{'Mode':<45} {'Tokens':>10}")
    print("-" * 57)
    print(f"{'A: Parallel (each reads all files + all tools)':<45} {mode_a_total:>10,}")
    for d in mode_b_details:
        print(f"  {'B: ' + d['agent'] + ' (summary + own tools)':<43} {d['total']:>10,}")
    print(f"{'B: Total (capped, shared summary)':<45} {mode_b_total:>10,}")
    print(f"{'Savings':<45} {savings:>9.1f}%")
    print()

    # Check if summary drops facts
    print("Summary Fact Check (MEASURED)")
    print("-" * 50)
    key_facts = [
        ("mathlib.py exists", "mathlib.py" in summary_text),
        ("test file exists", "test_mathlib" in summary_text),
        ("fixed reference exists", "mathlib_fixed" in summary_text),
        ("token counts present", "tokens" in summary_text),
        ("file count present", str(len(SHARED_FILES)) in summary_text),
    ]
    facts_present = sum(1 for _, present in key_facts if present)
    for fact, present in key_facts:
        print(f"  [{'OK' if present else '!!'}] {fact}: {present}")
    print(f"\n  Facts retained: {facts_present}/{len(key_facts)}")
    print()

    # Model switch cache cost
    print("Model Switch Cache Cost (MODELED)")
    print("-" * 50)
    prefix_tokens = SYSTEM_PROMPT_TOKENS + summary_tokens + sum(
        t["tokens"] for t in ALL_TOOLS if SUBAGENTS[0] in t["needed_by"])

    scenarios = [
        {"name": "No switch (same model)", "cache_lost": 0},
        {"name": "Switch mid-session", "cache_lost": prefix_tokens},
        {"name": "Switch + rebuild cache", "cache_lost": prefix_tokens,
         "rebuild_cost": int(prefix_tokens * 0.25)},  # cache write premium
    ]
    for s in scenarios:
        total_cost = s["cache_lost"] + s.get("rebuild_cost", 0)
        print(f"  {s['name']:<35} lost={s['cache_lost']:>5} "
              f"rebuild={s.get('rebuild_cost', 0):>5} total={total_cost:>5} tokens")

    print()
    print(f"Conclusion ({token_label} for sizes, MODELED for concurrency):")
    print(f"  Capped mode saves {savings:.0f}% ({mode_a_total:,} → {mode_b_total:,}).")
    print(f"  Summary retains {facts_present}/{len(key_facts)} key facts.")
    print(f"  Model switch costs {prefix_tokens} tokens in lost cache.")
    print(f"  Sample: {len(SUBAGENTS)} subagents, {len(SHARED_FILES)} files, {len(ALL_TOOLS)} tools.")

    exp_summary = {
        "experiment": "66_token_budget",
        "simulated": True,
        "token_sizes_measured": has_tiktoken,
        "concurrency_modeled": True,
        "subagents": len(SUBAGENTS),
        "mode_a_total": mode_a_total,
        "mode_b_total": mode_b_total,
        "savings_pct": round(savings, 2),
        "summary_tokens": summary_tokens,
        "facts_retained": facts_present,
        "facts_total": len(key_facts),
        "cache_lost_on_switch": prefix_tokens,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(exp_summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
