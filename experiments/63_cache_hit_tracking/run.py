#!/usr/bin/env python3
"""
Experiment 63: Cache-Hit Tracking + Prompt Ordering
======================================================

Models cache-hit rates for different prompt orderings over a 15-turn session.
Compares stable-first vs mixed ordering. Also models chained vs sequential
tool calls by context tokens.

MODELED: cache behavior modeled from prompt structure. Token counts MEASURED
with tiktoken. No real API cache endpoint available.
Sample: 15-turn session, 3 orderings, 5 tool-call comparisons.
"""
import json
import os
import argparse

SYSTEM_PROMPT = "You are an expert software engineer. Fix bugs, write tests, maintain quality."
REPO_FACTS = "Test: pytest -q. Build: not needed. Bugs in mathlib.py. Reference: mathlib_fixed.py."
TOOL_DEFS = """[{"name":"read_file","params":{"path":"str"}},{"name":"write_file","params":{"path":"str","content":"str"}},{"name":"run_command","params":{"cmd":"str"}},{"name":"search","params":{"pattern":"str"}}]"""

TURN_MESSAGES = [
    "Fix the factorial bug in mathlib.py",
    "I see the range starts at 0. Changing to range(1, n+1).",
    "File read: mathlib.py (105 lines)",
    "Fix applied. Running tests.",
    "Test output: 1 passed, 9 failed",
    "Now fixing fibonacci base case.",
    "Changed return 0 to return 1.",
    "Running tests again.",
    "Test output: 2 passed, 8 failed",
    "Fixing is_prime: // to %",
    "Applied modulo fix.",
    "Test output: 3 passed, 7 failed",
    "Fixing binary_search return value.",
    "Changed return mid to return -1.",
    "Test output: 4 passed, 6 failed",
]

CACHE_PRICING = {"standard": 3.0, "cached": 0.30}  # $/M tokens


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def model_session(ordering: str, turns: list) -> dict:
    """Model cache behavior for a prompt ordering over N turns."""
    sys_tok = count_tokens(SYSTEM_PROMPT)
    facts_tok = count_tokens(REPO_FACTS)
    tools_tok = count_tokens(TOOL_DEFS)
    stable_prefix = sys_tok + facts_tok + tools_tok

    total_input = 0
    total_cached = 0
    total_uncached = 0
    history = ""

    for i, msg in enumerate(turns):
        turn_tok = count_tokens(msg)
        history_tok = count_tokens(history) if history else 0

        if ordering == "stable_first":
            # System + facts + tools (stable) | history + new (changing)
            prefix_cacheable = stable_prefix + (history_tok if i > 0 else 0)
            new_tokens = turn_tok
        elif ordering == "mixed":
            # System | new message | facts | history | tools (unstable order)
            prefix_cacheable = sys_tok  # only system prompt is stable
            new_tokens = turn_tok + facts_tok + tools_tok + history_tok
        else:  # changing_first
            # New message | history | system + facts + tools
            prefix_cacheable = 0
            new_tokens = turn_tok + history_tok + stable_prefix

        input_this_turn = stable_prefix + history_tok + turn_tok

        if i == 0:
            cached = 0
            uncached = input_this_turn
        else:
            cached = min(prefix_cacheable, input_this_turn)
            uncached = input_this_turn - cached

        total_input += input_this_turn
        total_cached += cached
        total_uncached += uncached
        history += f"\n{msg}"

    cache_rate = total_cached / total_input * 100 if total_input > 0 else 0
    cost_uncached = total_input * CACHE_PRICING["standard"] / 1e6
    cost_cached = (total_uncached * CACHE_PRICING["standard"] + total_cached * CACHE_PRICING["cached"]) / 1e6
    savings = (cost_uncached - cost_cached) / cost_uncached * 100 if cost_uncached > 0 else 0

    return {
        "total_input": total_input,
        "total_cached": total_cached,
        "total_uncached": total_uncached,
        "cache_rate_pct": round(cache_rate, 1),
        "cost_all_uncached": round(cost_uncached, 6),
        "cost_with_cache": round(cost_cached, 6),
        "savings_pct": round(savings, 1),
    }


def model_tool_calls() -> dict:
    """Compare chained (one script) vs sequential (N calls) tool tokens."""
    sequential_calls = [
        {"call": "read_file('mathlib.py')", "response": "# 105 lines of code...\n" * 10},
        {"call": "read_file('test_mathlib.py')", "response": "# 76 lines of tests...\n" * 7},
        {"call": "write_file('mathlib.py', ...)", "response": "OK"},
        {"call": "run_command('pytest -q')", "response": "3 passed, 7 failed"},
    ]

    chained_script = """
import pathlib
mathlib = pathlib.Path('mathlib.py').read_text()
tests = pathlib.Path('test_mathlib.py').read_text()
mathlib = mathlib.replace('range(0, n + 1)', 'range(1, n + 1)')
pathlib.Path('mathlib.py').write_text(mathlib)
import subprocess
result = subprocess.run(['pytest', '-q'], capture_output=True, text=True)
print(f'mathlib: {len(mathlib)} chars')
print(f'tests: {len(tests)} chars')
print(result.stdout[-100:])
"""

    seq_context = sum(count_tokens(c["call"] + c["response"]) for c in sequential_calls)
    # Sequential: each call re-sends the growing context
    seq_total = 0
    running = 0
    for c in sequential_calls:
        call_tok = count_tokens(c["call"] + c["response"])
        running += call_tok
        seq_total += running

    chain_tokens = count_tokens(chained_script)
    chain_response = count_tokens("mathlib: 2800 chars\ntests: 1900 chars\n3 passed, 7 failed\n")
    chain_total = chain_tokens + chain_response

    return {
        "sequential_context_tokens": seq_context,
        "sequential_total_with_growth": seq_total,
        "chained_tokens": chain_tokens + chain_response,
        "savings_pct": round((seq_total - chain_total) / seq_total * 100, 1),
    }


def main():
    parser = argparse.ArgumentParser(description="Experiment 63: Cache-Hit Tracking")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken; has_tiktoken = True
    except ImportError: pass
    token_label = "MEASURED (tiktoken)" if has_tiktoken else "ESTIMATED"

    print("=" * 65)
    print("EXPERIMENT 63: Cache-Hit Tracking + Prompt Ordering")
    print("=" * 65)
    print(f"Token counting: {token_label}")
    print(f"Session: {len(TURN_MESSAGES)} turns")
    print(f"NOTE: Cache behavior is MODELED, not measured against a real API.")
    print()

    sys_tok = count_tokens(SYSTEM_PROMPT)
    facts_tok = count_tokens(REPO_FACTS)
    tools_tok = count_tokens(TOOL_DEFS)
    print(f"Stable prefix: system({sys_tok}) + facts({facts_tok}) + tools({tools_tok}) = {sys_tok+facts_tok+tools_tok} tokens")
    print()

    print("Prompt Ordering Comparison (MODELED)")
    print("-" * 55)

    orderings = ["stable_first", "mixed", "changing_first"]
    ordering_results = {}
    for ordering in orderings:
        r = model_session(ordering, TURN_MESSAGES)
        ordering_results[ordering] = r

    print(f"{'Ordering':<20} {'Cache Rate':>10} {'Cost (uncached)':>15} {'Cost (cached)':>13} {'Savings':>8}")
    print("-" * 68)
    for ordering, r in ordering_results.items():
        print(f"  {ordering:<18} {r['cache_rate_pct']:>9.1f}% ${r['cost_all_uncached']:>13.6f} "
              f"${r['cost_with_cache']:>12.6f} {r['savings_pct']:>7.1f}%")

    best = max(ordering_results.items(), key=lambda x: x[1]["cache_rate_pct"])
    print(f"\n  Best: {best[0]} ({best[1]['cache_rate_pct']}% cache rate, {best[1]['savings_pct']}% savings)")
    print()

    # Tool call comparison
    print("Tool Call Comparison: Chained vs Sequential (MODELED)")
    print("-" * 55)
    tools = model_tool_calls()
    print(f"  Sequential (4 calls, growing context): {tools['sequential_total_with_growth']:,} tokens")
    print(f"  Chained (1 script):                    {tools['chained_tokens']:,} tokens")
    print(f"  Savings: {tools['savings_pct']}%")
    print()

    print(f"Conclusion (token sizes {token_label}, cache behavior MODELED):")
    print(f"  Stable-first ordering: {best[1]['cache_rate_pct']}% cache rate, {best[1]['savings_pct']}% cost savings.")
    print(f"  Mixed ordering drops cache rate to {ordering_results['mixed']['cache_rate_pct']}%.")
    print(f"  Chained tool calls save {tools['savings_pct']}% vs sequential.")
    print(f"  Sample: {len(TURN_MESSAGES)}-turn session, {len(orderings)} orderings.")

    summary = {
        "experiment": "63_cache_hit_tracking",
        "simulated": True,
        "token_sizes_measured": has_tiktoken,
        "cache_behavior_modeled": True,
        "turns": len(TURN_MESSAGES),
        "orderings": ordering_results,
        "best_ordering": best[0],
        "best_cache_rate_pct": best[1]["cache_rate_pct"],
        "best_savings_pct": best[1]["savings_pct"],
        "tool_chained_savings_pct": tools["savings_pct"],
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
