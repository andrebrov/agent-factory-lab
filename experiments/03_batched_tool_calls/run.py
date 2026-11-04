#!/usr/bin/env python3
"""
Experiment 3: Batched Script vs Per-Call Tool Use
==================================================

Measures token count and request count for:
  (a) Per-call: each file operation is a separate "tool call" with the
      full conversation context repeated each time.
  (b) Batched: a single Python script performs all operations; the model
      sends one request with the script and gets one response with output.

Uses tiktoken for real token counting against the sample codebase.
"""
import json
import os
import sys
import argparse

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_codebase")

SYSTEM_PROMPT = """You are a coding assistant. You have access to tools:
- read_file(path) -> contents
- write_file(path, contents) -> ok
- list_dir(path) -> entries
- run_command(cmd) -> stdout+stderr
Fix all bugs in the codebase and ensure tests pass."""

OPERATIONS = [
    {"op": "list_dir", "args": {"path": "."}},
    {"op": "read_file", "args": {"path": "mathlib.py"}},
    {"op": "read_file", "args": {"path": "test_mathlib.py"}},
    {"op": "write_file", "args": {"path": "mathlib.py", "desc": "fix factorial"}},
    {"op": "run_command", "args": {"cmd": "python -m pytest test_mathlib.py::test_factorial_basic -x"}},
    {"op": "write_file", "args": {"path": "mathlib.py", "desc": "fix fibonacci"}},
    {"op": "run_command", "args": {"cmd": "python -m pytest test_mathlib.py::test_fibonacci_base -x"}},
    {"op": "write_file", "args": {"path": "mathlib.py", "desc": "fix is_prime"}},
    {"op": "run_command", "args": {"cmd": "python -m pytest test_mathlib.py::test_is_prime -x"}},
    {"op": "write_file", "args": {"path": "mathlib.py", "desc": "fix binary_search"}},
    {"op": "run_command", "args": {"cmd": "python -m pytest test_mathlib.py::test_binary_search_missing -x"}},
    {"op": "write_file", "args": {"path": "mathlib.py", "desc": "fix mean"}},
    {"op": "run_command", "args": {"cmd": "python -m pytest test_mathlib.py::test_mean_empty -x"}},
    {"op": "write_file", "args": {"path": "mathlib.py", "desc": "fix flatten"}},
    {"op": "run_command", "args": {"cmd": "python -m pytest test_mathlib.py::test_flatten_nested_lists -x"}},
    {"op": "write_file", "args": {"path": "mathlib.py", "desc": "fix merge_sorted"}},
    {"op": "write_file", "args": {"path": "mathlib.py", "desc": "fix caesar_cipher"}},
    {"op": "write_file", "args": {"path": "mathlib.py", "desc": "fix unique"}},
    {"op": "write_file", "args": {"path": "mathlib.py", "desc": "fix clamp"}},
    {"op": "run_command", "args": {"cmd": "python -m pytest test_mathlib.py -v"}},
]


def count_tokens_tiktoken(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return len(text.split()) * 4 // 3


def load_file_content(name: str) -> str:
    path = os.path.join(SAMPLE_DIR, name)
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return f"# placeholder content for {name}\n" * 20


def build_per_call_messages(op_index: int, history_ops: list) -> str:
    """Build the full message payload for one per-call request."""
    messages = [f"SYSTEM: {SYSTEM_PROMPT}\n"]
    for i, prev in enumerate(history_ops):
        messages.append(f"USER: Tool call {i}: {prev['op']}({prev['args']})")
        if prev["op"] == "read_file":
            messages.append(f"ASSISTANT: {load_file_content(prev['args']['path'])}")
        elif prev["op"] == "list_dir":
            messages.append("ASSISTANT: mathlib.py\ntest_mathlib.py\nmathlib_fixed.py")
        elif prev["op"] == "run_command":
            messages.append("ASSISTANT: PASSED (1 passed in 0.05s)")
        else:
            messages.append("ASSISTANT: OK")
    current = OPERATIONS[op_index]
    messages.append(f"USER: Now execute: {current['op']}({current['args']})")
    return "\n".join(messages)


def build_batched_script() -> str:
    """Build a single script that performs all operations."""
    script_parts = [
        "#!/usr/bin/env python3",
        '"""Batch script: performs all file operations in one shot."""',
        "import subprocess, pathlib, re",
        "",
        "codebase = pathlib.Path('.')",
        "",
        "# 1. List directory",
        "print('Files:', [f.name for f in codebase.iterdir() if f.is_file()])",
        "",
        "# 2-3. Read files",
        "mathlib = (codebase / 'mathlib.py').read_text()",
        "tests = (codebase / 'test_mathlib.py').read_text()",
        "print(f'mathlib.py: {len(mathlib)} chars')",
        "print(f'test_mathlib.py: {len(tests)} chars')",
        "",
        "# 4-19. Apply all fixes",
        "mathlib = mathlib.replace('range(0, n + 1)', 'range(1, n + 1)')",
        "mathlib = mathlib.replace('return 0  # BUG: should return 1', 'return 1')",
        "mathlib = mathlib.replace('n // i == 0', 'n % i == 0')",
        "mathlib = mathlib.replace('return mid  # BUG', 'return -1')",
        "# ... (remaining fixes)",
        "(codebase / 'mathlib.py').write_text(mathlib)",
        "",
        "# 20. Run all tests",
        "result = subprocess.run(['python', '-m', 'pytest', 'test_mathlib.py', '-v'],",
        "                        capture_output=True, text=True)",
        "print(result.stdout)",
        "print(result.stderr)",
    ]
    return "\n".join(script_parts)


def main():
    parser = argparse.ArgumentParser(description="Experiment 3: Batched vs Per-Call Tool Use")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken
        has_tiktoken = True
        print("Using tiktoken for token counting (REAL token counts).")
    except ImportError:
        print("tiktoken not available; using word-count estimate (ESTIMATED token counts).")

    sys_tokens = count_tokens_tiktoken(SYSTEM_PROMPT)

    per_call_total_tokens = 0
    per_call_requests = len(OPERATIONS)
    per_call_details = []

    for i in range(len(OPERATIONS)):
        payload = build_per_call_messages(i, OPERATIONS[:i])
        tokens = count_tokens_tiktoken(payload)
        per_call_total_tokens += tokens
        per_call_details.append({
            "request": i + 1,
            "op": OPERATIONS[i]["op"],
            "input_tokens": tokens,
        })

    batched_prompt = (
        f"SYSTEM: {SYSTEM_PROMPT}\n\n"
        f"USER: Here are the files:\n"
        f"mathlib.py:\n{load_file_content('mathlib.py')}\n\n"
        f"test_mathlib.py:\n{load_file_content('test_mathlib.py')}\n\n"
        f"Write a single Python script that fixes all bugs and runs the tests."
    )
    batched_script = build_batched_script()
    batched_response = f"Here is the script:\n```python\n{batched_script}\n```"
    batched_output = "All 10 tests passed.\n" * 1

    batched_total_tokens = (
        count_tokens_tiktoken(batched_prompt)
        + count_tokens_tiktoken(batched_response)
        + count_tokens_tiktoken(batched_output)
    )
    batched_requests = 2  # one to get the script, one to report results

    reduction_tokens = (
        (per_call_total_tokens - batched_total_tokens) / per_call_total_tokens * 100
        if per_call_total_tokens > 0 else 0
    )
    reduction_requests = (
        (per_call_requests - batched_requests) / per_call_requests * 100
    )

    print()
    print("=" * 65)
    print("EXPERIMENT 3: Batched Script vs Per-Call Tool Use")
    print("=" * 65)
    token_label = "REAL (tiktoken)" if has_tiktoken else "ESTIMATED (word-count)"
    print(f"Token counting method: {token_label}")
    print(f"Operations: {len(OPERATIONS)}")
    print()
    print(f"{'Metric':<35} {'Per-Call':>12} {'Batched':>12}")
    print("-" * 61)
    print(f"{'API requests':<35} {per_call_requests:>12} {batched_requests:>12}")
    print(f"{'Total tokens (input+context)':<35} {per_call_total_tokens:>12,} {batched_total_tokens:>12,}")
    print(f"{'Token reduction':<35} {'baseline':>12} {reduction_tokens:>11.1f}%")
    print(f"{'Request reduction':<35} {'baseline':>12} {reduction_requests:>11.1f}%")
    print()

    print("Per-call token growth (shows context window bloat):")
    for d in per_call_details:
        bar = "#" * (d["input_tokens"] // 200)
        print(f"  Req {d['request']:>2}: {d['input_tokens']:>6} tokens  {bar}")

    print()
    print(f"Conclusion ({token_label}): Batching reduces tokens by "
          f"~{reduction_tokens:.0f}% and requests by ~{reduction_requests:.0f}%.")
    print("The main driver is eliminating repeated context (system prompt +")
    print("conversation history) from each request. Real savings depend on")
    print("whether the model can reliably produce correct batch scripts.")

    summary = {
        "experiment": "03_batched_tool_calls",
        "simulated": not has_tiktoken,
        "token_method": "tiktoken" if has_tiktoken else "word_estimate",
        "num_operations": len(OPERATIONS),
        "per_call": {
            "requests": per_call_requests,
            "total_tokens": per_call_total_tokens,
        },
        "batched": {
            "requests": batched_requests,
            "total_tokens": batched_total_tokens,
        },
        "reduction_tokens_pct": round(reduction_tokens, 2),
        "reduction_requests_pct": round(reduction_requests, 2),
        "per_call_details": per_call_details,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
