#!/usr/bin/env python3
"""
Experiment 52: Proof-of-Done Gate + Skill Budget Audit
========================================================

Part A: Plants true and false "done" claims, compares trusting the claim
vs a gate that re-runs the test command and checks exit code + output.

Part B: Measures how many skill descriptions fit in a 1% context budget
(~2K tokens for a 200K window) and when to cut to names only.

MEASURED: real pytest execution for the gate, real tiktoken for skills.
Sample: 8 done claims (4 true, 4 false), 15 sample skills.
"""
import json
import os
import sys
import subprocess
import shutil
import tempfile
import argparse
from pathlib import Path

SAMPLE_DIR = Path(__file__).parent.parent / "sample_codebase"

DONE_CLAIMS = [
    {"id": "claim-1", "text": "All tests passed!", "true": True,
     "code_file": "mathlib_fixed.py", "test": "test_factorial_basic"},
    {"id": "claim-2", "text": "Tests pass, fix applied.", "true": True,
     "code_file": "mathlib_fixed.py", "test": "test_fibonacci_base"},
    {"id": "claim-3", "text": "Fixed and verified.", "true": True,
     "code_file": "mathlib_fixed.py", "test": "test_is_prime"},
    {"id": "claim-4", "text": "Tests pass.", "true": True,
     "code_file": "mathlib_fixed.py", "test": "test_mean_empty"},
    # False claims — using buggy code but claiming success
    {"id": "claim-5", "text": "All tests passed!", "true": False,
     "code_file": "mathlib.py", "test": "test_factorial_basic"},
    {"id": "claim-6", "text": "Fix verified, tests green.", "true": False,
     "code_file": "mathlib.py", "test": "test_fibonacci_base"},
    {"id": "claim-7", "text": "Tests pass on my machine.", "true": False,
     "code_file": "mathlib.py", "test": "test_is_prime"},
    {"id": "claim-8", "text": "Done! All checks pass.", "true": False,
     "code_file": "mathlib.py", "test": "test_mean_empty"},
]

SAMPLE_SKILLS = [
    {"name": "run_tests", "description": "Execute the project's test suite using pytest, capture output, and report pass/fail counts. Supports -v for verbose, -q for quiet, --tb=short for tracebacks."},
    {"name": "lint_code", "description": "Run the project's linter (ruff, eslint, or the configured tool) and report violations. Auto-fix safe issues with --fix flag."},
    {"name": "format_code", "description": "Apply the project's code formatter (black, prettier, ruff format). Reports files changed. Never modifies test files."},
    {"name": "type_check", "description": "Run the type checker (mypy, tsc, pyright) and report type errors. Focus on new/changed files to keep output manageable."},
    {"name": "search_code", "description": "Search the codebase for a pattern using ripgrep. Returns matching files, line numbers, and context. Supports regex and glob filters."},
    {"name": "read_file", "description": "Read the contents of a file. Supports line ranges for large files. Returns the file content as a string."},
    {"name": "write_file", "description": "Write content to a file, creating parent directories if needed. Requires the full file content, not a diff."},
    {"name": "run_command", "description": "Execute a shell command and return stdout, stderr, and exit code. Commands run in the project root. Long-running commands are backgrounded after 30 seconds."},
    {"name": "git_status", "description": "Show the current git status: staged, unstaged, and untracked files. Equivalent to git status --short."},
    {"name": "git_diff", "description": "Show the diff of uncommitted changes or between two refs. Supports path filtering and --stat for summary."},
    {"name": "create_pr", "description": "Create a pull request on GitHub with the given title, body, and base branch. Pushes the current branch first."},
    {"name": "list_issues", "description": "List open issues from the project's issue tracker. Supports label and assignee filters."},
    {"name": "web_search", "description": "Search the web for documentation, error messages, or API references. Returns snippets and URLs."},
    {"name": "ask_human", "description": "Ask the human operator a question and wait for their response. Use sparingly — only for decisions that cannot be inferred."},
    {"name": "spawn_subagent", "description": "Spawn a sub-agent with a task file. The sub-agent runs independently and reports back with results."},
]


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def proof_of_done_gate(claim: dict) -> dict:
    """Re-run the test command and check exit code + output."""
    import time
    start = time.monotonic()

    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copy(SAMPLE_DIR / claim["code_file"], os.path.join(tmpdir, "mathlib.py"))
        shutil.copy(SAMPLE_DIR / "test_mathlib.py", tmpdir)

        r = subprocess.run(
            [sys.executable, "-m", "pytest", f"test_mathlib.py::{claim['test']}",
             "-v", "--tb=short"],
            capture_output=True, text=True, cwd=tmpdir,
        )
        elapsed = time.monotonic() - start
        test_passed = r.returncode == 0
        output_tail = (r.stdout + r.stderr).strip()[-200:]

    return {
        "claim_id": claim["id"],
        "claimed_done": True,
        "claim_true": claim["true"],
        "gate_passed": test_passed,
        "exit_code": r.returncode,
        "output_tail": output_tail,
        "runtime_sec": round(elapsed, 4),
        "correct_verdict": (test_passed == claim["true"]),
    }


def main():
    parser = argparse.ArgumentParser(description="Experiment 52: Proof of Done")
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
    print("EXPERIMENT 52: Proof-of-Done Gate + Skill Budget Audit")
    print("=" * 65)
    print(f"Token counting: {token_label}")
    print()

    # Part A: Proof-of-Done Gate
    print("Part A: Proof-of-Done Gate (MEASURED — real pytest)")
    print("-" * 55)
    print(f"Claims: {len(DONE_CLAIMS)} ({sum(1 for c in DONE_CLAIMS if c['true'])} true, "
          f"{sum(1 for c in DONE_CLAIMS if not c['true'])} false)")
    print()

    gate_results = []
    for claim in DONE_CLAIMS:
        r = proof_of_done_gate(claim)
        gate_results.append(r)
        icon = "OK" if r["correct_verdict"] else "!!"
        print(f"  [{icon}] {claim['id']}: claimed=done, "
              f"truly={'done' if claim['true'] else 'NOT done'}, "
              f"gate={'PASS' if r['gate_passed'] else 'BLOCK'} "
              f"({r['runtime_sec']*1000:.0f}ms)")

    false_claims_caught = sum(1 for r in gate_results if not r["claim_true"] and not r["gate_passed"])
    false_claims_missed = sum(1 for r in gate_results if not r["claim_true"] and r["gate_passed"])
    true_claims_blocked = sum(1 for r in gate_results if r["claim_true"] and not r["gate_passed"])
    true_claims_passed = sum(1 for r in gate_results if r["claim_true"] and r["gate_passed"])
    total_false = sum(1 for c in DONE_CLAIMS if not c["true"])
    total_true = sum(1 for c in DONE_CLAIMS if c["true"])
    avg_runtime = sum(r["runtime_sec"] for r in gate_results) / len(gate_results)

    print()
    print(f"  {'Metric':<35} {'Trust Only':>12} {'With Gate':>10}")
    print(f"  {'-' * 59}")
    print(f"  {'False claims caught':<35} {'0':>12} {false_claims_caught:>8}/{total_false}")
    print(f"  {'False claims missed':<35} {total_false:>12} {false_claims_missed:>10}")
    print(f"  {'True claims passed':<35} {total_true:>12} {true_claims_passed:>8}/{total_true}")
    print(f"  {'True claims blocked (false flag)':<35} {'0':>12} {true_claims_blocked:>10}")
    print(f"  {'Avg gate runtime':<35} {'0ms':>12} {avg_runtime*1000:>8.0f}ms")
    print()

    # Part B: Skill Budget Audit
    print("Part B: Skill Budget Audit (MEASURED — tiktoken)")
    print("-" * 55)

    context_window = 200_000
    budget_pct = 1.0
    budget_tokens = int(context_window * budget_pct / 100)

    full_descriptions = "\n".join(
        f"- {s['name']}: {s['description']}" for s in SAMPLE_SKILLS
    )
    names_only = "\n".join(f"- {s['name']}" for s in SAMPLE_SKILLS)

    full_tokens = count_tokens(full_descriptions)
    names_tokens = count_tokens(names_only)

    per_skill_full = []
    cumulative = 0
    fits_full = 0
    for s in SAMPLE_SKILLS:
        t = count_tokens(f"- {s['name']}: {s['description']}")
        cumulative += t
        per_skill_full.append({"name": s["name"], "tokens": t, "cumulative": cumulative})
        if cumulative <= budget_tokens:
            fits_full += 1

    per_skill_name = count_tokens("- " + SAMPLE_SKILLS[0]["name"])
    fits_names = min(len(SAMPLE_SKILLS), budget_tokens // max(per_skill_name, 1))

    print(f"  Context window: {context_window:,} tokens")
    print(f"  Budget (1%): {budget_tokens:,} tokens")
    print(f"  Skills: {len(SAMPLE_SKILLS)}")
    print(f"  Full descriptions: {full_tokens} tokens ({fits_full} fit in budget)")
    print(f"  Names only: {names_tokens} tokens ({min(fits_names, len(SAMPLE_SKILLS))} fit in budget)")
    print()

    cutover = None
    for i, s in enumerate(per_skill_full):
        if s["cumulative"] > budget_tokens:
            cutover = i
            break

    if cutover is not None:
        print(f"  Cut to names-only after skill #{cutover} ({per_skill_full[cutover-1]['name']})")
        print(f"  At that point: {per_skill_full[cutover-1]['cumulative']} tokens used")
    else:
        print(f"  All {len(SAMPLE_SKILLS)} skills fit with full descriptions")
    print()

    print(f"Conclusion:")
    print(f"  Gate: catches {false_claims_caught}/{total_false} false claims, "
          f"{true_claims_blocked} false flags, {avg_runtime*1000:.0f}ms overhead.")
    print(f"  Skills: {fits_full}/{len(SAMPLE_SKILLS)} fit with descriptions in 1% budget;")
    print(f"  {min(fits_names, len(SAMPLE_SKILLS))}/{len(SAMPLE_SKILLS)} fit as names only.")

    summary = {
        "experiment": "52_proof_of_done",
        "simulated": False,
        "token_method": "tiktoken" if has_tiktoken else "word_estimate",
        "gate": {
            "claims_total": len(DONE_CLAIMS),
            "true_claims": total_true,
            "false_claims": total_false,
            "false_caught": false_claims_caught,
            "false_missed": false_claims_missed,
            "true_passed": true_claims_passed,
            "true_blocked": true_claims_blocked,
            "avg_runtime_ms": round(avg_runtime * 1000, 1),
        },
        "skills": {
            "total": len(SAMPLE_SKILLS),
            "full_tokens": full_tokens,
            "names_tokens": names_tokens,
            "budget_tokens": budget_tokens,
            "fits_full": fits_full,
            "fits_names": min(fits_names, len(SAMPLE_SKILLS)),
            "cutover_at_skill": cutover,
        },
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
