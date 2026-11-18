#!/usr/bin/env python3
"""
Experiment 59: Hand Off Instead of Compacting
================================================

Simulates a 10-step coding task under three context-management modes:
  (a) Keep going: accumulate context until the task finishes or the window
      fills (simulated at 200K tokens).
  (b) Compact at 60%: summarize old context at the 60% mark and keep going.
  (c) Hand off at 60%: write handoff.md and start a fresh pane.

MEASURED: real tiktoken for handoff/summary/context sizes.
SIMULATED: task execution model (steps are synthetic, not real LLM calls).
Sample: 1 ten-step task, 3 modes.
"""
import json
import os
import argparse
from pathlib import Path

SAMPLE_DIR = Path(__file__).parent.parent / "sample_codebase"
CONTEXT_WINDOW = 16_000  # realistic for a mid-session worker pane
HANDOFF_THRESHOLD = 0.60

# A realistic multi-bug fix session: explore, fix 3 bugs, test each, write PR.
# Each step adds to context. Tool results (file contents, test output) are
# the main contributor. Sizes are representative, not from real LLM calls.
TASK_STEPS = [
    {"step": "read_issue", "new_tokens": 300, "output_tokens": 200},
    {"step": "explore_codebase", "new_tokens": 200, "output_tokens": 2500},
    {"step": "read_target_file", "new_tokens": 100, "output_tokens": 900},
    {"step": "read_test_file", "new_tokens": 100, "output_tokens": 700},
    {"step": "plan_fixes", "new_tokens": 100, "output_tokens": 800},
    {"step": "write_fix_1", "new_tokens": 100, "output_tokens": 600},
    {"step": "run_tests_1", "new_tokens": 50, "output_tokens": 1200},
    {"step": "write_fix_2", "new_tokens": 100, "output_tokens": 600},
    {"step": "run_tests_2", "new_tokens": 50, "output_tokens": 1200},
    {"step": "write_fix_3", "new_tokens": 100, "output_tokens": 600},
    {"step": "run_tests_3", "new_tokens": 50, "output_tokens": 1200},
    {"step": "final_check", "new_tokens": 50, "output_tokens": 800},
    {"step": "write_pr", "new_tokens": 50, "output_tokens": 500},
]

SYSTEM_PROMPT_TOKENS = 200

HANDOFF_TEMPLATE = """# Handoff
## Goal: Fix {bug_name} in mathlib.py
## Done: {done_steps}
## Next: {next_step}
## Open files: mathlib.py, test_mathlib.py
## Key decisions: {decisions}
"""

COMPACT_SUMMARY_RATIO = 0.15  # summary is ~15% of the original tokens


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def simulate_keep_going(steps, system_tokens):
    """Mode A: keep accumulating context."""
    context = system_tokens
    total_input = 0
    for s in steps:
        context += s["new_tokens"] + s["output_tokens"]
        total_input += context  # each step re-reads the full context
    return {"total_input_tokens": total_input, "final_context": context,
            "handoffs": 0, "compactions": 0}


def simulate_compact(steps, system_tokens, threshold_pct):
    """Mode B: compact (summarize) at the threshold."""
    context = system_tokens
    total_input = 0
    compactions = 0
    threshold = int(CONTEXT_WINDOW * threshold_pct)

    for s in steps:
        context += s["new_tokens"] + s["output_tokens"]
        total_input += context
        if context > threshold:
            compacted = int(context * COMPACT_SUMMARY_RATIO) + system_tokens
            context = compacted
            compactions += 1

    return {"total_input_tokens": total_input, "final_context": context,
            "handoffs": 0, "compactions": compactions}


def simulate_handoff(steps, system_tokens, threshold_pct):
    """Mode C: hand off to a fresh pane at the threshold."""
    context = system_tokens
    total_input = 0
    handoffs = 0
    threshold = int(CONTEXT_WINDOW * threshold_pct)

    handoff_text = HANDOFF_TEMPLATE.format(
        bug_name="factorial", done_steps="explored, planned",
        next_step="write fix", decisions="use range(1, n+1)")
    handoff_tokens = count_tokens(handoff_text)
    target_file_tokens = count_tokens((SAMPLE_DIR / "mathlib.py").read_text())

    for s in steps:
        context += s["new_tokens"] + s["output_tokens"]
        total_input += context
        if context > threshold:
            context = system_tokens + handoff_tokens + target_file_tokens
            handoffs += 1

    return {"total_input_tokens": total_input, "final_context": context,
            "handoffs": handoffs, "compactions": 0,
            "handoff_tokens": handoff_tokens}


def main():
    parser = argparse.ArgumentParser(description="Experiment 59: Handoff vs Compact")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken; has_tiktoken = True
    except ImportError: pass
    token_label = "MEASURED (tiktoken)" if has_tiktoken else "ESTIMATED"

    print("=" * 65)
    print("EXPERIMENT 59: Hand Off Instead of Compacting")
    print("=" * 65)
    print(f"Token counting: {token_label}")
    print(f"Task: 10 steps, context window: {CONTEXT_WINDOW:,}, threshold: {HANDOFF_THRESHOLD:.0%}")
    print()

    handoff_text = HANDOFF_TEMPLATE.format(
        bug_name="factorial", done_steps="explored, planned",
        next_step="write fix", decisions="use range(1, n+1)")
    handoff_tokens = count_tokens(handoff_text)
    target_tokens = count_tokens((SAMPLE_DIR / "mathlib.py").read_text())

    print(f"Handoff.md size: {handoff_tokens} tokens")
    print(f"Target file (mathlib.py): {target_tokens} tokens")
    print(f"System prompt: {SYSTEM_PROMPT_TOKENS} tokens")
    print()

    keep = simulate_keep_going(TASK_STEPS, SYSTEM_PROMPT_TOKENS)
    compact = simulate_compact(TASK_STEPS, SYSTEM_PROMPT_TOKENS, HANDOFF_THRESHOLD)
    handoff = simulate_handoff(TASK_STEPS, SYSTEM_PROMPT_TOKENS, HANDOFF_THRESHOLD)

    keep_t = keep["total_input_tokens"]
    compact_t = compact["total_input_tokens"]
    handoff_t = handoff["total_input_tokens"]

    compact_save = (keep_t - compact_t) / keep_t * 100
    handoff_save = (keep_t - handoff_t) / keep_t * 100

    print(f"{'Mode':<35} {'Total Input':>12} {'Savings':>10} {'Handoffs':>9} {'Compacts':>9}")
    print("-" * 78)
    print(f"{'(a) Keep going':<35} {keep_t:>12,} {'baseline':>10} {0:>9} {0:>9}")
    print(f"{'(b) Compact at 60%':<35} {compact_t:>12,} {compact_save:>9.1f}% {0:>9} {compact['compactions']:>9}")
    print(f"{'(c) Hand off at 60%':<35} {handoff_t:>12,} {handoff_save:>9.1f}% {handoff['handoffs']:>9} {0:>9}")
    print()

    print(f"Final context size:")
    print(f"  Keep going:  {keep['final_context']:>8,} tokens")
    print(f"  Compact:     {compact['final_context']:>8,} tokens")
    print(f"  Hand off:    {handoff['final_context']:>8,} tokens")
    print()

    # The cited claim: 47% of cost was re-reading old chat
    old_chat_fraction = 1 - (TASK_STEPS[-1]["new_tokens"] + TASK_STEPS[-1]["output_tokens"]) / keep["final_context"]
    print(f"Old-chat fraction at task end (keep-going): {old_chat_fraction:.0%}")
    print(f"Cited claim: 47%. Our simulation: {old_chat_fraction:.0%}")
    print()

    print(f"Conclusion ({token_label} for sizes, SIMULATED for execution model):")
    print(f"  Handoff saves {handoff_save:.0f}% vs keep-going, {handoff_save - compact_save:.0f}pp more than compact.")
    print(f"  Handoff starts each fresh pane with {handoff_tokens + target_tokens + SYSTEM_PROMPT_TOKENS} tokens")
    print(f"  vs the growing context of keep-going ({keep['final_context']:,} tokens by end).")
    print(f"  Sample: 1 ten-step task, 3 modes. The task model is synthetic.")

    summary = {
        "experiment": "59_handoff_vs_compact",
        "simulated": True,
        "token_sizes_measured": True,
        "execution_model_simulated": True,
        "task_steps": len(TASK_STEPS),
        "keep_going_tokens": keep_t,
        "compact_tokens": compact_t,
        "handoff_tokens_total": handoff_t,
        "compact_savings_pct": round(compact_save, 2),
        "handoff_savings_pct": round(handoff_save, 2),
        "handoff_md_tokens": handoff_tokens,
        "handoffs_triggered": handoff["handoffs"],
        "compactions_triggered": compact["compactions"],
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
