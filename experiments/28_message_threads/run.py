#!/usr/bin/env python3
"""
Experiment 28: Anthropic Message Threads — Payload Reduction Model
====================================================================

Simulates the payload-size reduction from message threads over a 30-turn
coding session. Threads avoid re-uploading the full conversation on each
turn; the model still reads everything (same token cost, lower latency).

REAL TOKEN COUNTS (tiktoken) for payload sizes.
TTFT improvement is Anthropic's claim (~35% for 500K–1M tokens), not measured.
"""
import json
import os
import argparse

SYSTEM_PROMPT = """You are an expert software engineer with access to file editing tools, 
shell execution, and code search. Fix bugs, write tests, and maintain code quality."""

TOOL_DEFINITIONS = """[
  {"name": "read_file", "parameters": {"path": "string"}},
  {"name": "write_file", "parameters": {"path": "string", "content": "string"}},
  {"name": "run_command", "parameters": {"cmd": "string"}},
  {"name": "search_files", "parameters": {"pattern": "string"}},
  {"name": "list_directory", "parameters": {"path": "string"}}
]"""

TURNS = [
    ("user", "Fix the authentication bypass in auth.py"),
    ("assistant", "I'll start by reading the auth module to understand the vulnerability."),
    ("tool_result", "# auth.py contents (200 lines of code)\ndef authenticate(token):\n    if not token:\n        return None\n    # BUG: missing signature verification\n    return decode_jwt(token)\n"),
    ("assistant", "Found the issue. The JWT token is decoded without signature verification. Let me fix it by adding proper verification."),
    ("tool_result", "File written successfully."),
    ("assistant", "Now let me run the existing tests to make sure nothing breaks."),
    ("tool_result", "FAILED: test_auth_bypass - expected 401, got 200\n12 passed, 1 failed"),
    ("assistant", "The test caught the old behavior. Let me update the test expectation and add a new test for the fix."),
    ("tool_result", "File written successfully."),
    ("assistant", "Running tests again."),
    ("tool_result", "13 passed in 0.5s"),
    ("assistant", "All tests pass. Let me also check for similar patterns in other files."),
    ("tool_result", "Found 2 more instances in api/middleware.py and services/token.py"),
    ("assistant", "Fixing the same issue in middleware.py and token.py."),
    ("tool_result", "Files written successfully."),
    ("assistant", "Running the full test suite."),
    ("tool_result", "47 passed in 2.3s"),
    ("assistant", "All tests pass. Let me verify the changes look correct."),
    ("tool_result", "diff --git a/auth.py b/auth.py\n--- a/auth.py\n+++ b/auth.py\n@@ -15,3 +15,5 @@ def authenticate(token):\n+    try:\n+        verified = verify_signature(token, PUBLIC_KEY)\n"),
    ("assistant", "The fix adds proper JWT signature verification in all three locations. Tests pass."),
    ("user", "Good. Now add rate limiting to the login endpoint."),
    ("assistant", "I'll implement rate limiting using a token bucket algorithm."),
    ("tool_result", "# login.py contents (150 lines)"),
    ("assistant", "Writing the rate limiter implementation."),
    ("tool_result", "File written successfully."),
    ("assistant", "Adding tests for rate limiting."),
    ("tool_result", "File written successfully."),
    ("assistant", "Running tests."),
    ("tool_result", "52 passed in 2.8s"),
    ("assistant", "Rate limiting implemented and tested. All 52 tests pass."),
]


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def main():
    parser = argparse.ArgumentParser(description="Experiment 28: Message Threads")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken
        has_tiktoken = True
    except ImportError:
        pass

    token_label = "REAL (tiktoken)" if has_tiktoken else "ESTIMATED"

    prefix = f"SYSTEM: {SYSTEM_PROMPT}\nTOOLS: {TOOL_DEFINITIONS}\n"
    prefix_tokens = count_tokens(prefix)

    print("=" * 65)
    print("EXPERIMENT 28: Anthropic Message Threads — Payload Model")
    print("=" * 65)
    print(f"Token counting: {token_label}")
    print(f"Turns: {len(TURNS)}")
    print(f"Stable prefix: {prefix_tokens} tokens")
    print()

    has_api_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if has_api_key:
        print("ANTHROPIC_API_KEY found — real TTFT test could run.")
    else:
        print("No ANTHROPIC_API_KEY — TTFT is Anthropic's claim, not measured.")
    print()

    cumulative = prefix
    total_without_threads = 0
    total_with_threads = 0
    turn_data = []

    for i, (role, content) in enumerate(TURNS):
        turn_text = f"\n{role.upper()}: {content}\n"
        cumulative += turn_text
        turn_tokens = count_tokens(turn_text)

        without_thread = count_tokens(cumulative)
        if i == 0:
            with_thread = without_thread  # create: full payload
        else:
            with_thread = turn_tokens + 50  # continue: new message + thread ref overhead

        total_without_threads += without_thread
        total_with_threads += with_thread

        turn_data.append({
            "turn": i + 1,
            "role": role,
            "payload_without": without_thread,
            "payload_with": with_thread,
        })

    payload_reduction = (total_without_threads - total_with_threads) / total_without_threads * 100

    print(f"{'Turn':>4} {'Role':<15} {'Without':>10} {'With Thread':>12} {'Saved':>8}")
    print("-" * 53)
    for t in turn_data:
        saved = t["payload_without"] - t["payload_with"]
        print(f"{t['turn']:>4} {t['role']:<15} {t['payload_without']:>10,} "
              f"{t['payload_with']:>12,} {saved:>8,}")

    print()
    print(f"{'Metric':<40} {'Without':>12} {'With Thread':>12}")
    print("-" * 66)
    print(f"{'Total payload tokens (all turns)':<40} {total_without_threads:>12,} {total_with_threads:>12,}")
    print(f"{'Payload reduction':<40} {'baseline':>12} {payload_reduction:>11.1f}%")
    print(f"{'TTFT improvement (Anthropic claim)':<40} {'baseline':>12} {'~35%':>12}")
    print(f"{'Token cost change':<40} {'baseline':>12} {'0% (same)':>12}")
    print()

    final_context = count_tokens(cumulative)
    print(f"Final conversation size: {final_context:,} tokens")
    if final_context >= 500_000:
        ttft_applicable = "Yes (>500K tokens, full benefit)"
    elif final_context >= 100_000:
        ttft_applicable = "Partial (~100K-500K range)"
    else:
        ttft_applicable = f"Minimal ({final_context:,} tokens is below the 500K+ sweet spot)"
    print(f"TTFT benefit applicability: {ttft_applicable}")
    print()

    print("Protocol for real TTFT measurement (requires ANTHROPIC_API_KEY):")
    print("  1. Send 30-turn session WITHOUT threads, measure TTFT per turn")
    print("  2. Send same session WITH threads (create + continue), measure TTFT")
    print("  3. Compare median TTFT for turns 10-30 (where context is large)")
    print("  4. Verify token usage is identical (threads don't save tokens)")
    print()
    print(f"Conclusion ({token_label}): Message threads reduce upload payload by")
    print(f"{payload_reduction:.0f}% over {len(TURNS)} turns. This is a latency optimization,")
    print("not a cost optimization — the model reads the same tokens either way.")
    print("Anthropic claims ~35% lower median TTFT for 500K-1M-token requests.")

    summary = {
        "experiment": "28_message_threads",
        "simulated": not has_api_key,
        "token_method": "tiktoken" if has_tiktoken else "word_estimate",
        "turns": len(TURNS),
        "total_payload_without": total_without_threads,
        "total_payload_with": total_with_threads,
        "payload_reduction_pct": round(payload_reduction, 2),
        "ttft_improvement_claim": "~35% for 500K-1M tokens (Anthropic, not verified)",
        "cost_change": "0% (same tokens, same cost)",
        "api_key_available": has_api_key,
        "final_context_tokens": final_context,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
