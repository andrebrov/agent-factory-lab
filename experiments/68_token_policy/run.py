#!/usr/bin/env python3
"""
Experiment 68: Token Policy for herdr Workers
================================================

Models a four-part policy against a long-session Opus baseline:
  (a) Compact at 8K tokens (even though the model supports 200K)
  (b) Clear session between tasks
  (c) Cheap model (Haiku) by default, Opus for planning only
  (d) Scout subagents for repo search instead of main-context reads

No real LLM calls. Token sizes are MEASURED (tiktoken). Costs are MODELED
from public pricing. The policy and baseline are both modeled, not run.
Sample: 3 sequential tasks on the sample codebase.
"""
import json
import os
import argparse
from pathlib import Path

SAMPLE_DIR = Path(__file__).parent.parent / "sample_codebase"

PRICING = {
    "opus":  {"input": 15.00, "output": 75.00, "cached": 1.50},
    "haiku": {"input": 0.25,  "output": 1.25,  "cached": 0.03},
}

SYSTEM_PROMPT_TOKENS = 30
COMPACT_LIMIT = 8000
COMPACT_RATIO = 0.15  # summary is ~15% of compacted content

TASKS = [
    {"name": "fix_factorial", "test": "test_factorial_basic",
     "planning_tokens": 300, "coding_tokens": 800, "test_output_tokens": 400},
    {"name": "fix_fibonacci", "test": "test_fibonacci_base",
     "planning_tokens": 250, "coding_tokens": 700, "test_output_tokens": 350},
    {"name": "fix_is_prime", "test": "test_is_prime",
     "planning_tokens": 280, "coding_tokens": 750, "test_output_tokens": 380},
]


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def cost(tokens_in: int, tokens_out: int, model: str, cached_in: int = 0) -> float:
    p = PRICING[model]
    return ((tokens_in - cached_in) * p["input"] + cached_in * p["cached"] + tokens_out * p["output"]) / 1e6


def main():
    parser = argparse.ArgumentParser(description="Experiment 68: Token Policy")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken; has_tiktoken = True
    except ImportError: pass
    token_label = "MEASURED (tiktoken)" if has_tiktoken else "ESTIMATED"

    # Measure real file sizes
    mathlib_tokens = count_tokens((SAMPLE_DIR / "mathlib.py").read_text())
    test_tokens = count_tokens((SAMPLE_DIR / "test_mathlib.py").read_text())
    all_file_tokens = mathlib_tokens + test_tokens

    print("=" * 65)
    print("EXPERIMENT 68: Token Policy for herdr Workers")
    print("=" * 65)
    print(f"Token counting: {token_label}")
    print(f"Tasks: {len(TASKS)}, File sizes: mathlib={mathlib_tokens}, tests={test_tokens}")
    print(f"No real LLM calls. Costs are MODELED from public pricing.")
    print()

    # ── Baseline: one long Opus session, reads repo in context ──
    print("Baseline: One long Opus session, reads repo in main context")
    print("-" * 55)
    baseline_context = SYSTEM_PROMPT_TOKENS + all_file_tokens
    baseline_input_total = 0
    baseline_output_total = 0

    for i, task in enumerate(TASKS):
        # Each task reads growing context (prior task history stays)
        task_input = baseline_context + task["planning_tokens"] + task["coding_tokens"]
        task_output = task["coding_tokens"] + task["test_output_tokens"]
        baseline_input_total += task_input
        baseline_output_total += task_output
        baseline_context += task["planning_tokens"] + task["coding_tokens"] + task["test_output_tokens"]
        print(f"  Task {i+1}: input={task_input:,}, context_after={baseline_context:,}")

    baseline_cost = cost(baseline_input_total, baseline_output_total, "opus")
    print(f"  Total input: {baseline_input_total:,}, output: {baseline_output_total:,}")
    print(f"  Cost (all Opus): ${baseline_cost:.6f}")
    print()

    # ── Policy: compact, clear, cheap model, scout subagents ──
    print("Policy: compact@8K, clear between tasks, Haiku+Opus, scouts")
    print("-" * 55)

    # Scout reads: a cheap subagent reads the files and returns a summary
    scout_summary_tokens = 120  # ~10-line summary of what the scout found
    scout_read_cost = cost(all_file_tokens + SYSTEM_PROMPT_TOKENS, scout_summary_tokens, "haiku")

    policy_input_total = 0
    policy_output_total = 0
    policy_opus_input = 0
    policy_haiku_input = 0
    policy_opus_output = 0
    policy_haiku_output = 0

    for i, task in enumerate(TASKS):
        # (d) Scout reads files, returns summary — main worker never reads the repo
        # (c) Planning step: Opus
        plan_input = SYSTEM_PROMPT_TOKENS + scout_summary_tokens + task["planning_tokens"]
        plan_output = task["planning_tokens"]
        policy_opus_input += plan_input
        policy_opus_output += plan_output

        # (c) Coding step: Haiku
        code_input = SYSTEM_PROMPT_TOKENS + scout_summary_tokens + task["planning_tokens"] + task["coding_tokens"]
        code_output = task["coding_tokens"] + task["test_output_tokens"]
        policy_haiku_input += code_input
        policy_haiku_output += code_output

        # (a) Compact if context exceeds limit (won't here, sessions are short)
        # (b) Clear session — next task starts fresh (already modeled above)

        task_input = plan_input + code_input
        task_output = plan_output + code_output
        policy_input_total += task_input
        policy_output_total += task_output
        print(f"  Task {i+1}: plan(Opus)={plan_input}, code(Haiku)={code_input}, total={task_input}")

    # Costs
    policy_opus_cost = cost(policy_opus_input, policy_opus_output, "opus")
    policy_haiku_cost = cost(policy_haiku_input, policy_haiku_output, "haiku")
    policy_scout_cost = scout_read_cost * len(TASKS)  # one scout per task
    policy_total_cost = policy_opus_cost + policy_haiku_cost + policy_scout_cost

    print(f"\n  Opus tokens:  in={policy_opus_input:,}, out={policy_opus_output:,}")
    print(f"  Haiku tokens: in={policy_haiku_input:,}, out={policy_haiku_output:,}")
    print(f"  Scout reads:  {len(TASKS)} × {all_file_tokens + SYSTEM_PROMPT_TOKENS} tokens (Haiku)")
    print(f"  Policy cost: Opus ${policy_opus_cost:.6f} + Haiku ${policy_haiku_cost:.6f} "
          f"+ scouts ${policy_scout_cost:.6f} = ${policy_total_cost:.6f}")
    print()

    # Summary
    input_savings = (baseline_input_total - policy_input_total) / baseline_input_total * 100
    cost_savings = (baseline_cost - policy_total_cost) / baseline_cost * 100

    print(f"{'Metric':<40} {'Baseline':>12} {'Policy':>12}")
    print("-" * 66)
    print(f"{'Total input tokens':<40} {baseline_input_total:>12,} {policy_input_total:>12,}")
    print(f"{'Input token reduction':<40} {'—':>12} {input_savings:>11.1f}%")
    print(f"{'Total cost (modeled)':<40} ${baseline_cost:>11.6f} ${policy_total_cost:>11.6f}")
    print(f"{'Cost reduction':<40} {'—':>12} {cost_savings:>11.1f}%")
    print(f"{'Main worker reads repo':<40} {'yes':>12} {'no (scouts)':>12}")
    print(f"{'Session between tasks':<40} {'continuous':>12} {'cleared':>12}")
    print(f"{'Planning model':<40} {'Opus':>12} {'Opus':>12}")
    print(f"{'Coding model':<40} {'Opus':>12} {'Haiku':>12}")
    print()

    print(f"Conclusion (token sizes {token_label}, costs MODELED):")
    print(f"  Input tokens: {input_savings:.0f}% reduction (context doesn't grow across tasks).")
    print(f"  Cost: {cost_savings:.0f}% reduction (Haiku for coding, scouts for reads).")
    print(f"  CAVEAT: No real LLM calls — we don't know if Haiku produces")
    print(f"  correct fixes or if scout summaries lose needed detail.")
    print(f"  Quality impact is UNKNOWN. Sample: {len(TASKS)} tasks.")

    summary = {
        "experiment": "68_token_policy",
        "simulated": True,
        "no_real_llm_calls": True,
        "token_sizes_measured": has_tiktoken,
        "costs_modeled": True,
        "quality_unknown": True,
        "tasks": len(TASKS),
        "baseline_input": baseline_input_total,
        "policy_input": policy_input_total,
        "input_reduction_pct": round(input_savings, 2),
        "baseline_cost": round(baseline_cost, 6),
        "policy_cost": round(policy_total_cost, 6),
        "cost_reduction_pct": round(cost_savings, 2),
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
