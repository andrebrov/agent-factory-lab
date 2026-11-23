#!/usr/bin/env python3
"""
Experiment 75: Cache and Compaction Hygiene
==============================================

Tests prefix stability (byte-identical across turns), cache-hit modeling
on synthetic traces, and cost modeling for 400K vs 967K compaction.

MEASURED: prefix byte-comparison (mechanistic test).
MODELED: cache-hit rates on synthetic traces. Compaction cost on modeled
token volumes. Quality at 400K compaction threshold: UNTESTED — no real
LLM calls were made.

Sample: 3 prefix variants, 15-turn synthetic trace, 2 compaction thresholds.
"""
import json
import os
import hashlib
import argparse

SYSTEM_PROMPT = "You are an expert software engineer. Fix bugs and write tests."
REPO_FACTS = "Test: pytest -q. Build: not needed. Bugs in mathlib.py."
TOOL_DEFS_STABLE = '[{"name":"read_file","params":"path"},{"name":"run_command","params":"cmd"},{"name":"write_file","params":"path,content"}]'
TOOL_DEFS_REORDERED = '[{"name":"run_command","params":"cmd"},{"name":"write_file","params":"path,content"},{"name":"read_file","params":"path"}]'

PRICING = {"input": 3.00, "cached": 0.30, "output": 15.00}  # $/M tokens


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def build_prefix(variant: str, turn: int) -> str:
    base = SYSTEM_PROMPT + "\n" + REPO_FACTS + "\n"
    if variant == "stable":
        return base + TOOL_DEFS_STABLE
    elif variant == "reordered":
        return base + (TOOL_DEFS_STABLE if turn % 2 == 0 else TOOL_DEFS_REORDERED)
    elif variant == "timestamped":
        return base + TOOL_DEFS_STABLE + f"\nRequest #{turn} at timestamp={1000+turn}"
    return base


def main():
    parser = argparse.ArgumentParser(description="Experiment 75: Cache Hygiene")
    parser.add_argument("--turns", type=int, default=15)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken; has_tiktoken = True
    except ImportError: pass
    token_label = "MEASURED (tiktoken)" if has_tiktoken else "ESTIMATED"

    print("=" * 65)
    print("EXPERIMENT 75: Cache and Compaction Hygiene")
    print("=" * 65)
    print(f"Token counting: {token_label}")
    print(f"Turns: {args.turns}")
    print()

    # ── Part A: Prefix Stability (MEASURED — byte comparison) ──
    print("Part A: Prefix Stability (MEASURED — byte comparison)")
    print("-" * 55)

    variants = ["stable", "reordered", "timestamped"]
    stability_results = {}

    for variant in variants:
        hashes = set()
        for turn in range(args.turns):
            prefix = build_prefix(variant, turn)
            h = hashlib.sha256(prefix.encode()).hexdigest()
            hashes.add(h)

        stable = len(hashes) == 1
        stability_results[variant] = {
            "unique_prefixes": len(hashes),
            "stable": stable,
            "would_cache": stable,
        }
        status = "STABLE" if stable else f"UNSTABLE ({len(hashes)} variants)"
        print(f"  {variant:<15} {status}")

    print()

    # ── Part B: Cache-Hit Modeling (MODELED on synthetic trace) ──
    print("Part B: Cache-Hit Rate (MODELED — synthetic trace)")
    print("-" * 55)
    print("  These are MODELED hit rates, not measured against a real API cache.")
    print()

    prefix_tokens = count_tokens(build_prefix("stable", 0))

    for variant in variants:
        total_input = 0
        total_cached = 0
        prev_prefix_hash = None

        for turn in range(args.turns):
            prefix = build_prefix(variant, turn)
            prefix_hash = hashlib.sha256(prefix.encode()).hexdigest()
            ptok = count_tokens(prefix)
            msg_tokens = 50 + turn * 30  # growing message history

            total_input += ptok + msg_tokens
            if prev_prefix_hash is not None and prefix_hash == prev_prefix_hash:
                total_cached += ptok  # prefix is identical → cache hit
            prev_prefix_hash = prefix_hash

        hit_rate = total_cached / total_input * 100 if total_input > 0 else 0
        flag = hit_rate < 80
        stability_results[variant]["hit_rate_pct"] = round(hit_rate, 1)
        stability_results[variant]["flagged_below_80"] = flag
        print(f"  {variant:<15} hit_rate={hit_rate:.1f}%  {'⚠ FLAGGED' if flag else 'OK'}")

    print()

    # ── Part C: Compaction Cost (MODELED) ──
    print("Part C: Compaction at 400K vs 967K (MODELED)")
    print("-" * 55)
    print("  Quality at 400K: UNTESTED — no real LLM calls.")
    print()

    # Model: a session that grows from 0 to 1.2M tokens over 60 turns
    session_turns = 60
    tokens_per_turn = 20_000  # typical turn adds ~20K (tool results, code)

    for threshold_name, threshold in [("400K", 400_000), ("967K", 967_000)]:
        context = prefix_tokens
        total_input = 0
        compactions = 0

        for turn in range(session_turns):
            context += tokens_per_turn
            total_input += context
            if context > threshold:
                # Compact: keep 15% as summary + prefix
                context = prefix_tokens + int((context - prefix_tokens) * 0.15)
                compactions += 1

        cost = total_input * PRICING["input"] / 1e6
        print(f"  {threshold_name}: {compactions} compactions, {total_input:,} total input, "
              f"${cost:.2f} (modeled)")

    compact_400k_compactions = 0
    compact_967k_compactions = 0
    compact_400k_input = 0
    compact_967k_input = 0

    for threshold, label in [(400_000, "400k"), (967_000, "967k")]:
        ctx = prefix_tokens
        total = 0
        comps = 0
        for _ in range(session_turns):
            ctx += tokens_per_turn
            total += ctx
            if ctx > threshold:
                ctx = prefix_tokens + int((ctx - prefix_tokens) * 0.15)
                comps += 1
        if label == "400k":
            compact_400k_compactions = comps
            compact_400k_input = total
        else:
            compact_967k_compactions = comps
            compact_967k_input = total

    savings = (compact_967k_input - compact_400k_input) / compact_967k_input * 100
    print(f"\n  400K saves {savings:.1f}% input tokens vs 967K")
    print(f"  400K: {compact_400k_compactions} compactions; 967K: {compact_967k_compactions}")
    print(f"  CAVEAT: more compactions means more summarization calls")
    print(f"  and potential quality loss. Quality is UNTESTED.")
    print()

    print(f"Conclusion:")
    print(f"  Prefix stability: stable variant caches perfectly; reordered and")
    print(f"  timestamped variants break the cache (MEASURED byte comparison).")
    print(f"  Hit rates are MODELED, not measured against a real API.")
    print(f"  Compaction at 400K saves {savings:.0f}% input tokens vs 967K (MODELED)")
    print(f"  but quality is UNTESTED — no real LLM calls were made.")
    print(f"  Sample: 3 variants, {args.turns}-turn trace, 2 thresholds.")

    summary = {
        "experiment": "75_cache_hygiene",
        "prefix_stability_measured": True,
        "cache_hits_modeled": True,
        "compaction_cost_modeled": True,
        "quality_untested": True,
        "variants": stability_results,
        "compaction": {
            "400k_input": compact_400k_input,
            "967k_input": compact_967k_input,
            "savings_pct": round(savings, 2),
            "400k_compactions": compact_400k_compactions,
            "967k_compactions": compact_967k_compactions,
        },
        "turns": args.turns,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
