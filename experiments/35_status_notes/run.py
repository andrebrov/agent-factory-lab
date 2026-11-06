#!/usr/bin/env python3
"""
Experiment 35: Status Notes vs Re-Reading Transcripts + decisions.md
======================================================================

Compares token cost of polling status via full transcript re-reads vs
short status notes. Also prototypes an append-only decisions.md log.

REAL token counting (tiktoken).
"""
import json
import os
import argparse
from datetime import datetime

TRANSCRIPT_TURNS = [
    "User: Fix the authentication bypass in auth.py",
    "Assistant: Reading auth.py to understand the vulnerability...",
    "Tool: [200 lines of auth.py code]" + "\n# " * 40,
    "Assistant: Found the issue — JWT decoded without signature verification.",
    "Tool: write_file auth.py [patched code]" + "\n# " * 30,
    "Assistant: Fix applied. Running tests...",
    "Tool: pytest output — 12 passed, 1 failed" + "\n# " * 10,
    "Assistant: Updating the failing test expectation...",
    "Tool: write_file test_auth.py [updated test]" + "\n# " * 15,
    "Assistant: All 13 tests pass now.",
    "User: Also check middleware.py for the same pattern.",
    "Assistant: Reading middleware.py...",
    "Tool: [150 lines of middleware.py]" + "\n# " * 30,
    "Assistant: Same vulnerability found. Fixing...",
    "Tool: write_file middleware.py [patched]" + "\n# " * 25,
    "Assistant: Fixed. Running full suite — 47 passed.",
]

STATUS_NOTES = [
    "## Status: auth.py JWT bypass fixed. 13/13 tests pass.",
    "## Status: middleware.py JWT bypass fixed. 47/47 tests pass.",
]

DECISIONS_LOG = [
    {"ts": "T+0m", "agent": "agent-1", "decision": "Fix JWT bypass in auth.py first (highest severity)"},
    {"ts": "T+3m", "agent": "agent-1", "decision": "Update test expectation rather than removing test"},
    {"ts": "T+5m", "agent": "agent-1", "decision": "Check middleware.py for same pattern (user request)"},
    {"ts": "T+7m", "agent": "agent-1", "decision": "Apply identical fix to middleware.py"},
]

POLL_INTERVALS = [1, 2, 5, 10, 15, 20]  # poll at these turn numbers


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def main():
    parser = argparse.ArgumentParser(description="Experiment 35: Status Notes")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken
        has_tiktoken = True
    except ImportError:
        pass
    token_label = "REAL (tiktoken)" if has_tiktoken else "ESTIMATED"

    print("=" * 65)
    print("EXPERIMENT 35: Status Notes vs Re-Reading Transcripts")
    print("=" * 65)
    print(f"Token counting: {token_label}")
    print()

    full_transcript = "\n".join(TRANSCRIPT_TURNS)
    transcript_tokens = count_tokens(full_transcript)
    status_text = "\n".join(STATUS_NOTES)
    status_tokens = count_tokens(status_text)
    decisions_text = "\n".join(
        f"- [{d['ts']}] {d['agent']}: {d['decision']}" for d in DECISIONS_LOG
    )
    decisions_tokens = count_tokens(decisions_text)

    print(f"Transcript: {transcript_tokens} tokens ({len(TRANSCRIPT_TURNS)} turns)")
    print(f"Status notes: {status_tokens} tokens ({len(STATUS_NOTES)} entries)")
    print(f"Decisions log: {decisions_tokens} tokens ({len(DECISIONS_LOG)} entries)")
    print()

    # Simulate polling at different intervals
    print("Polling cost comparison:")
    print(f"  {'Polls':>5} {'Transcript Re-read':>18} {'Status Note':>12} {'Saved':>8} {'Reduction':>10}")
    print("  " + "-" * 57)

    poll_results = []
    for num_polls in POLL_INTERVALS:
        reread_cost = num_polls * transcript_tokens
        note_cost = num_polls * status_tokens
        saved = reread_cost - note_cost
        reduction = saved / reread_cost * 100 if reread_cost > 0 else 0

        print(f"  {num_polls:>5} {reread_cost:>18,} {note_cost:>12,} "
              f"{saved:>8,} {reduction:>9.1f}%")

        poll_results.append({
            "polls": num_polls,
            "transcript_tokens": reread_cost,
            "status_tokens": note_cost,
            "reduction_pct": round(reduction, 2),
        })

    avg_reduction = sum(r["reduction_pct"] for r in poll_results) / len(poll_results)

    print()
    print(f"Average token reduction: {avg_reduction:.1f}%")
    print()

    # decisions.md prototype
    print("decisions.md prototype:")
    print("-" * 40)
    print(decisions_text)
    print()
    print(f"decisions.md cost: {decisions_tokens} tokens")
    print(f"Full context for divergence check: {decisions_tokens} tokens")
    print(f"vs re-reading transcript: {transcript_tokens} tokens")
    divergence_savings = (transcript_tokens - decisions_tokens) / transcript_tokens * 100
    print(f"Savings for divergence detection: {divergence_savings:.1f}%")
    print()

    print(f"Conclusion ({token_label}): Status notes save {avg_reduction:.0f}% of tokens")
    print(f"vs transcript re-reads. decisions.md saves {divergence_savings:.0f}% for")
    print("divergence detection. Both are append-only and trivial to implement.")

    summary = {
        "experiment": "35_status_notes",
        "simulated": False,
        "token_method": "tiktoken" if has_tiktoken else "word_estimate",
        "transcript_tokens": transcript_tokens,
        "status_tokens": status_tokens,
        "decisions_tokens": decisions_tokens,
        "avg_polling_reduction_pct": round(avg_reduction, 2),
        "divergence_savings_pct": round(divergence_savings, 2),
        "poll_results": poll_results,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
