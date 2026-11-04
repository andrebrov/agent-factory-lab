#!/usr/bin/env python3
"""
Experiment 4: Cached vs Uncached Prompt Token Cost Analysis
=============================================================

Simulates a 20-turn coding session and computes the cost difference
between:
  (a) Uncached: every request sends the full conversation history at
      standard input pricing.
  (b) Cached: the stable prefix (system prompt + tools + early context)
      is cached and charged at the discounted rate; only new tokens pay
      full price.

Uses tiktoken for real token counts where available.
"""
import json
import os
import argparse
import math

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_codebase")

SYSTEM_PROMPT = (
    "You are an expert software engineer. You have access to the following tools:\n"
    "- read_file(path): Read a file and return its contents.\n"
    "- write_file(path, content): Write content to a file.\n"
    "- run_command(cmd): Run a shell command and return stdout/stderr.\n"
    "- search_files(pattern): Search for files matching a glob pattern.\n"
    "- list_directory(path): List files in a directory.\n\n"
    "You are working on a Python project. Fix bugs, write tests, and ensure "
    "code quality. Always explain your reasoning before making changes.\n"
)

TOOL_DEFINITIONS = """
[
  {"name": "read_file", "parameters": {"path": "string"}},
  {"name": "write_file", "parameters": {"path": "string", "content": "string"}},
  {"name": "run_command", "parameters": {"cmd": "string"}},
  {"name": "search_files", "parameters": {"pattern": "string"}},
  {"name": "list_directory", "parameters": {"path": "string"}}
]
"""

PRICING = {
    "anthropic": {
        "input_per_mtok": 3.00,
        "cached_input_per_mtok": 0.30,
        "cache_write_per_mtok": 3.75,
        "output_per_mtok": 15.00,
    },
    "openai": {
        "input_per_mtok": 2.50,
        "cached_input_per_mtok": 1.25,
        "cache_write_per_mtok": 2.50,
        "output_per_mtok": 10.00,
    },
}

TURN_TEMPLATES = [
    ("user", "Please look at the project structure and identify the bugs."),
    ("assistant", "I'll start by listing the files and reading the main module.\n\n"
     "Let me read mathlib.py first..."),
    ("user", "I see you found some issues. Please fix the factorial function."),
    ("assistant", "The factorial function has a bug: the range starts at 0 instead of 1. "
     "I'll fix it by changing range(0, n+1) to range(1, n+1)."),
    ("user", "Good. Now fix the fibonacci function."),
    ("assistant", "The fibonacci base case returns 0 for fib(1), but it should return 1."),
    ("user", "Fix is_prime next."),
    ("assistant", "The is_prime function uses integer division (//) instead of modulo (%). "
     "Changing n // i == 0 to n % i == 0."),
    ("user", "Fix binary_search."),
    ("assistant", "The binary_search function returns mid when the element isn't found. "
     "It should return -1."),
    ("user", "Fix the mean function."),
    ("assistant", "The mean function doesn't handle empty lists. Adding a guard clause "
     "that raises ValueError."),
    ("user", "Fix flatten."),
    ("assistant", "The flatten function only checks for tuples, not lists. Changing the "
     "isinstance check to include both list and tuple."),
    ("user", "Fix merge_sorted."),
    ("assistant", "The j index starts at 1 instead of 0. Fixing the initialization."),
    ("user", "Fix caesar_cipher."),
    ("assistant", "The cipher shifts all characters including non-alphabetic ones. "
     "Adding an isalpha() check."),
    ("user", "Fix unique and clamp, then run all tests."),
    ("assistant", "Fixed unique to preserve insertion order using a seen set. "
     "Fixed clamp's swapped lo/hi returns. Running pytest... all 10 tests pass."),
]


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def main():
    parser = argparse.ArgumentParser(description="Experiment 4: Prompt Caching Analysis")
    parser.add_argument("--provider", default="anthropic", choices=list(PRICING.keys()))
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken
        has_tiktoken = True
    except ImportError:
        pass

    prices = PRICING[args.provider]
    token_label = "REAL (tiktoken)" if has_tiktoken else "ESTIMATED (word-count)"

    prefix_text = f"SYSTEM: {SYSTEM_PROMPT}\nTOOLS: {TOOL_DEFINITIONS}\n"
    prefix_tokens = count_tokens(prefix_text)

    turns = []
    cumulative_context = prefix_text
    total_uncached_input_cost = 0.0
    total_cached_input_cost = 0.0
    total_output_cost = 0.0

    for i, (role, content) in enumerate(TURN_TEMPLATES):
        turn_text = f"\n{role.upper()}: {content}\n"
        cumulative_context += turn_text

        total_input_tokens = count_tokens(cumulative_context)
        new_tokens = count_tokens(turn_text)
        cached_tokens = total_input_tokens - new_tokens
        output_tokens = count_tokens(content) if role == "assistant" else 0

        uncached_cost = total_input_tokens * prices["input_per_mtok"] / 1_000_000
        if i == 0:
            cached_cost = (
                cached_tokens * prices["cache_write_per_mtok"] / 1_000_000
                + new_tokens * prices["input_per_mtok"] / 1_000_000
            )
        else:
            cached_cost = (
                cached_tokens * prices["cached_input_per_mtok"] / 1_000_000
                + new_tokens * prices["input_per_mtok"] / 1_000_000
            )
        output_cost = output_tokens * prices["output_per_mtok"] / 1_000_000

        total_uncached_input_cost += uncached_cost
        total_cached_input_cost += cached_cost
        total_output_cost += output_cost

        turns.append({
            "turn": i + 1,
            "role": role,
            "total_input_tokens": total_input_tokens,
            "new_tokens": new_tokens,
            "cached_tokens": cached_tokens,
            "output_tokens": output_tokens,
            "uncached_input_cost": round(uncached_cost, 6),
            "cached_input_cost": round(cached_cost, 6),
            "output_cost": round(output_cost, 6),
        })

    total_uncached = total_uncached_input_cost + total_output_cost
    total_cached = total_cached_input_cost + total_output_cost
    savings = total_uncached - total_cached
    savings_pct = savings / total_uncached * 100 if total_uncached > 0 else 0

    cache_hit_tokens = sum(t["cached_tokens"] for t in turns[1:])
    total_input_all_turns = sum(t["total_input_tokens"] for t in turns)
    cache_hit_rate = cache_hit_tokens / total_input_all_turns * 100

    breakeven_turn = None
    running_uncached = 0.0
    running_cached = 0.0
    for t in turns:
        running_uncached += t["uncached_input_cost"] + t["output_cost"]
        running_cached += t["cached_input_cost"] + t["output_cost"]
        if running_cached < running_uncached and breakeven_turn is None:
            breakeven_turn = t["turn"]

    print("=" * 65)
    print("EXPERIMENT 4: Cached vs Uncached Prompt Token Cost")
    print("=" * 65)
    print(f"Provider: {args.provider}")
    print(f"Token counting: {token_label}")
    print(f"Session: {len(TURN_TEMPLATES)} turns")
    print(f"Stable prefix: {prefix_tokens} tokens (system prompt + tools)")
    print()
    print("--- COSTS ARE ESTIMATED FROM PUBLIC PRICING ---")
    print()
    print(f"{'Metric':<40} {'Uncached':>12} {'Cached':>12}")
    print("-" * 66)
    print(f"{'Total input cost':<40} ${total_uncached_input_cost:>10.5f} "
          f"${total_cached_input_cost:>10.5f}")
    print(f"{'Output cost (same)':<40} ${total_output_cost:>10.5f} "
          f"${total_output_cost:>10.5f}")
    print(f"{'Total session cost':<40} ${total_uncached:>10.5f} "
          f"${total_cached:>10.5f}")
    print(f"{'Savings':<40} {'':>12} ${savings:>10.5f} ({savings_pct:.1f}%)")
    print(f"{'Cache hit rate':<40} {'n/a':>12} {cache_hit_rate:>11.1f}%")
    print(f"{'Break-even turn':<40} {'n/a':>12} {breakeven_turn or 'turn 1':>12}")
    print()

    print("Per-turn cost growth:")
    print(f"  {'Turn':>4} {'Role':<10} {'Input Tok':>10} {'Uncached$':>11} "
          f"{'Cached$':>11} {'Cumul Saved':>12}")
    cum_saved = 0.0
    for t in turns:
        saved = t["uncached_input_cost"] - t["cached_input_cost"]
        cum_saved += saved
        print(f"  {t['turn']:>4} {t['role']:<10} {t['total_input_tokens']:>10,} "
              f"${t['uncached_input_cost']:>10.5f} ${t['cached_input_cost']:>10.5f} "
              f"${cum_saved:>11.5f}")

    print()
    print(f"Conclusion ({token_label}): Prompt caching saves ~{savings_pct:.0f}% of")
    print(f"input costs over a {len(TURN_TEMPLATES)}-turn session. The cache write")
    print(f"premium is recovered by turn {breakeven_turn or 1}. Longer sessions")
    print("save proportionally more because the growing context is increasingly")
    print("dominated by cached tokens.")

    summary = {
        "experiment": "04_prompt_caching",
        "simulated": True,
        "token_method": "tiktoken" if has_tiktoken else "word_estimate",
        "provider": args.provider,
        "pricing": prices,
        "num_turns": len(TURN_TEMPLATES),
        "prefix_tokens": prefix_tokens,
        "total_uncached_cost": round(total_uncached, 6),
        "total_cached_cost": round(total_cached, 6),
        "savings_usd": round(savings, 6),
        "savings_pct": round(savings_pct, 2),
        "cache_hit_rate_pct": round(cache_hit_rate, 2),
        "breakeven_turn": breakeven_turn,
        "turns": turns,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
