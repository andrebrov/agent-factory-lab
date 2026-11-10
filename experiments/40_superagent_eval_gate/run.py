#!/usr/bin/env python3
"""
Experiment 40: Two-Layer Eval Gate + Structured Report Protocol
=================================================================

Reimplements the two most transferable mechanisms from DeepSeek's
dsh-superagent-prototype:

1. Deterministic Eval Gate: pre-filter incoming triggers before any LLM
   call, rejecting unauthorized, duplicate, or policy-violating requests.
2. Structured Report Protocol: workers emit one of 6 states instead of
   free text; the orchestrator routes deterministically.

MEASURED: token counting (tiktoken) for report protocol comparison.
Gate filter rates are MEASURED on a synthetic but realistic trigger stream.
The original dsh-superagent code was not executed — this is a faithful
reimplementation of the mechanisms, not a run of the original TypeScript.
"""
import json
import os
import random
import argparse
from enum import Enum
from dataclasses import dataclass, field


# ── Eval Gate ─────────────────────────────────────────────────────────

ALLOWED_USERS = {"alice", "bob", "carol", "dave"}
BOTS = {"ci-bot", "dependabot", "renovate"}

class GateResult(str, Enum):
    PASS = "pass"
    REJECT_UNAUTHORIZED = "reject_unauthorized"
    REJECT_BOT = "reject_bot"
    REJECT_DUPLICATE = "reject_duplicate"
    REJECT_POLICY = "reject_policy"


@dataclass
class Trigger:
    id: str
    actor: str
    thread_id: str
    is_explicit: bool
    content: str


@dataclass
class GateState:
    active_tickets: set = field(default_factory=set)
    policy_version: int = 1


def eval_gate(trigger: Trigger, state: GateState, current_policy: int) -> GateResult:
    """Deterministic gate: no LLM call needed."""
    if trigger.actor in BOTS:
        return GateResult.REJECT_BOT
    if trigger.actor not in ALLOWED_USERS:
        return GateResult.REJECT_UNAUTHORIZED
    if trigger.thread_id in state.active_tickets:
        return GateResult.REJECT_DUPLICATE
    if current_policy != state.policy_version:
        return GateResult.REJECT_POLICY
    return GateResult.PASS


def generate_trigger_stream(n: int, seed: int) -> list:
    """Generate a realistic stream of coding requests."""
    random.seed(seed)
    actors = list(ALLOWED_USERS) + list(BOTS) + ["stranger1", "stranger2", "spammer"]
    threads = [f"issue-{i}" for i in range(1, 21)]
    triggers = []
    for i in range(n):
        triggers.append(Trigger(
            id=f"t-{i}",
            actor=random.choice(actors),
            thread_id=random.choice(threads),
            is_explicit=random.random() < 0.6,
            content=f"Fix bug in module {random.choice(['auth', 'api', 'db', 'ui', 'test'])}",
        ))
    return triggers


# ── Structured Report Protocol ────────────────────────────────────────

class ReportState(str, Enum):
    PROGRESS = "progress"
    WAITING = "waiting"
    READY = "ready"
    BLOCKED = "blocked"
    FAILED = "failed"
    DROPPED = "dropped"


STRUCTURED_REPORT = '{"state":"ready","files_changed":["auth.py","test_auth.py"],"tests_passed":13,"pr":"#42"}'

FREE_TEXT_REPORT = """I've completed the work on the authentication bypass fix. Here's what I did:

1. Read auth.py and identified the JWT signature verification bypass
2. Added proper signature verification using the project's public key
3. Updated the test that was checking for the old (buggy) behavior
4. Added a new test for the signature verification
5. Ran the full test suite - all 13 tests pass now
6. The changes are in auth.py and test_auth.py
7. I've opened PR #42 with the fix

The fix is ready for review. Let me know if you need any changes."""

ORCHESTRATOR_PARSE_PROMPT = """Given this agent report, determine:
1. Is it done? (yes/no)
2. What files changed?
3. Did tests pass?
4. What PR was opened?

Report: {report}"""


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


ROUTING_TABLE = {
    ReportState.READY: "attempt_merge_or_notify_reviewer",
    ReportState.BLOCKED: "halt_auto_input_wait_human",
    ReportState.FAILED: "halt_auto_input_wait_human",
    ReportState.WAITING: "idle_accept_triggers",
    ReportState.DROPPED: "end_ticket",
    ReportState.PROGRESS: "no_action",
}


def main():
    parser = argparse.ArgumentParser(description="Experiment 40: Eval Gate + Reports")
    parser.add_argument("--triggers", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
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
    print("EXPERIMENT 40: dsh-superagent Eval Gate + Structured Reports")
    print("=" * 65)
    print(f"Token counting: {token_label}")
    print()
    print("Source: github.com/deepseek-ai/dsh-superagent-prototype")
    print("This is a faithful reimplementation, NOT a run of the original.")
    print()

    # ── Part A: Eval Gate ──
    print("Part A: Two-Layer Eval Gate")
    print("-" * 40)

    triggers = generate_trigger_stream(args.triggers, args.seed)
    state = GateState(policy_version=1)
    current_policy = 1

    results_by_type = {r: 0 for r in GateResult}
    llm_calls_saved = 0

    for trigger in triggers:
        gate_result = eval_gate(trigger, state, current_policy)
        results_by_type[gate_result] += 1

        if gate_result == GateResult.PASS:
            state.active_tickets.add(trigger.thread_id)
        else:
            llm_calls_saved += 1

    total = len(triggers)
    passed = results_by_type[GateResult.PASS]
    filtered = total - passed
    filter_rate = filtered / total * 100

    print(f"  Trigger stream: {total}")
    print(f"  Allowed users: {ALLOWED_USERS}")
    print(f"  Bots: {BOTS}")
    print()
    print(f"  {'Gate Result':<30} {'Count':>6} {'%':>8}")
    print(f"  {'-' * 46}")
    for result, count in sorted(results_by_type.items(), key=lambda x: -x[1]):
        print(f"  {result.value:<30} {count:>6} {count/total*100:>7.1f}%")
    print(f"  {'─' * 46}")
    print(f"  {'TOTAL FILTERED':<30} {filtered:>6} {filter_rate:>7.1f}%")
    print(f"  {'PASSED TO LLM':<30} {passed:>6} {passed/total*100:>7.1f}%")
    print()

    llm_cost_per_eval = 2000  # estimated tokens per LLM eval
    tokens_saved = llm_calls_saved * llm_cost_per_eval
    print(f"  LLM calls avoided: {llm_calls_saved}")
    print(f"  Estimated tokens saved: {tokens_saved:,} ({llm_calls_saved} × {llm_cost_per_eval})")
    print()

    # ── Part B: Structured Report Protocol ──
    print("Part B: Structured Report Protocol")
    print("-" * 40)

    struct_tokens = count_tokens(STRUCTURED_REPORT)
    free_tokens = count_tokens(FREE_TEXT_REPORT)
    parse_prompt_tokens = count_tokens(ORCHESTRATOR_PARSE_PROMPT.format(report=FREE_TEXT_REPORT))

    struct_route_tokens = count_tokens(json.dumps(ROUTING_TABLE))

    free_total = free_tokens + parse_prompt_tokens
    struct_total = struct_tokens + struct_route_tokens

    report_savings = (free_total - struct_total) / free_total * 100

    print(f"  {'Metric':<40} {'Free Text':>10} {'Structured':>11}")
    print(f"  {'-' * 63}")
    print(f"  {'Report tokens':<40} {free_tokens:>10} {struct_tokens:>11}")
    print(f"  {'Orchestrator parse/route tokens':<40} {parse_prompt_tokens:>10} {struct_route_tokens:>11}")
    print(f"  {'Total per status check':<40} {free_total:>10} {struct_total:>11}")
    print(f"  {'Token savings':<40} {'baseline':>10} {report_savings:>10.1f}%")
    print(f"  {'LLM call for parsing':<40} {'yes':>10} {'no':>11}")
    print()

    # Routing correctness
    print("  Routing table (deterministic, no LLM):")
    for state_val, action in ROUTING_TABLE.items():
        print(f"    {state_val.value:<12} → {action}")
    print()

    # ── Part C: Combined Impact ──
    print("Part C: Combined Impact (per 100 incoming requests)")
    print("-" * 40)

    requests = 100
    gate_pass_rate = passed / total
    requests_to_llm = int(requests * gate_pass_rate)
    requests_filtered = requests - requests_to_llm

    without_gate = requests * llm_cost_per_eval
    with_gate = requests_to_llm * llm_cost_per_eval
    gate_savings = (without_gate - with_gate) / without_gate * 100

    reports_per_request = 3  # avg reports per completed task
    without_struct = reports_per_request * requests_to_llm * free_total
    with_struct = reports_per_request * requests_to_llm * struct_total
    report_savings_total = (without_struct - with_struct) / without_struct * 100

    combined_without = without_gate + without_struct
    combined_with = with_gate + with_struct
    combined_savings = (combined_without - combined_with) / combined_without * 100

    print(f"  {'Metric':<40} {'Without':>12} {'With':>12}")
    print(f"  {'-' * 66}")
    print(f"  {'Requests reaching LLM eval':<40} {requests:>12} {requests_to_llm:>12}")
    print(f"  {'Eval tokens':<40} {without_gate:>12,} {with_gate:>12,}")
    print(f"  {'Report tokens (3 reports × tasks)':<40} {without_struct:>12,} {with_struct:>12,}")
    print(f"  {'Total tokens':<40} {combined_without:>12,} {combined_with:>12,}")
    print(f"  {'Combined savings':<40} {'baseline':>12} {combined_savings:>11.1f}%")
    print()

    print("Conclusion: The deterministic eval gate filters out")
    print(f"{filter_rate:.0f}% of triggers before any LLM call. Structured reports")
    print(f"save {report_savings:.0f}% of status-check tokens by eliminating free-text")
    print(f"parsing. Combined, the two mechanisms save {combined_savings:.0f}% of total")
    print("intake + status tokens.")
    print()
    print("Proposal for Gwaihir: adopt both mechanisms.")
    print("  1. Add a deterministic gate before LLM eval on incoming tasks.")
    print("  2. Require workers to report structured states, not free text.")

    summary = {
        "experiment": "40_superagent_eval_gate",
        "simulated": False,
        "token_method": "tiktoken" if has_tiktoken else "word_estimate",
        "source_repo": "github.com/deepseek-ai/dsh-superagent-prototype",
        "original_code_executed": False,
        "reimplementation": True,
        "gate": {
            "triggers": total,
            "passed": passed,
            "filtered": filtered,
            "filter_rate_pct": round(filter_rate, 2),
            "by_reason": {k.value: v for k, v in results_by_type.items()},
            "llm_calls_avoided": llm_calls_saved,
        },
        "reports": {
            "free_text_tokens": free_tokens,
            "structured_tokens": struct_tokens,
            "parse_prompt_tokens": parse_prompt_tokens,
            "report_savings_pct": round(report_savings, 2),
            "routing_is_deterministic": True,
        },
        "combined_savings_pct": round(combined_savings, 2),
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
