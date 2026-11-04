#!/usr/bin/env python3
"""
Experiment 25: Durable Harness — Step-Log Resume After Crash
===============================================================

Implements a step-log based durable execution harness. Simulates a
crash mid-workflow and measures recovery: steps replayed vs skipped,
time saved, cost savings from not re-executing completed steps.

The log and resume execute locally; the crash is simulated between steps,
operations are synthetic, and token costs are estimates. Incomplete steps can
replay after an effect but before its completion is recorded. Effects must be
idempotent or protected by external deduplication for safe retries.
"""
import json
import os
import time
import tempfile
import argparse
from pathlib import Path


class StepLog:
    """Simple append-only step log, not a transactional durable store."""

    def __init__(self, log_path: str):
        self.log_path = log_path
        self.steps = []
        self._load()

    def _load(self):
        if os.path.exists(self.log_path):
            with open(self.log_path) as f:
                for line in f:
                    self.steps.append(json.loads(line))

    def is_completed(self, step_id: str) -> bool:
        return any(s["step_id"] == step_id and s["status"] == "completed" for s in self.steps)

    def get_result(self, step_id: str):
        for s in reversed(self.steps):
            if s["step_id"] == step_id and s["status"] == "completed":
                return s.get("result")
        return None

    def record(self, step_id: str, status: str, result=None, cost_tokens: int = 0):
        entry = {
            "step_id": step_id,
            "status": status,
            "result": result,
            "cost_tokens": cost_tokens,
            "timestamp": time.time(),
        }
        self.steps.append(entry)
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")


WORKFLOW_STEPS = [
    {"id": "read_issue",    "desc": "Read issue description",    "cost_tokens": 500,  "time_sec": 0.02},
    {"id": "analyze_code",  "desc": "Analyze codebase",          "cost_tokens": 3000, "time_sec": 0.05},
    {"id": "plan_fix",      "desc": "Generate fix plan",         "cost_tokens": 2000, "time_sec": 0.03},
    {"id": "write_code",    "desc": "Write code changes",        "cost_tokens": 5000, "time_sec": 0.08},
    {"id": "run_tests",     "desc": "Run test suite",            "cost_tokens": 1000, "time_sec": 0.04},
    {"id": "fix_failures",  "desc": "Fix test failures",         "cost_tokens": 3000, "time_sec": 0.05},
    {"id": "run_tests_2",   "desc": "Re-run tests",              "cost_tokens": 1000, "time_sec": 0.04},
    {"id": "write_pr",      "desc": "Write PR description",      "cost_tokens": 1500, "time_sec": 0.03},
    {"id": "final_check",   "desc": "Final verification",        "cost_tokens": 800,  "time_sec": 0.02},
    {"id": "submit",        "desc": "Submit PR",                  "cost_tokens": 200,  "time_sec": 0.01},
]


def execute_step(step: dict) -> str:
    time.sleep(step["time_sec"])
    return f"completed_{step['id']}"


def run_workflow(log: StepLog, crash_after: int = None) -> dict:
    """Run the workflow, optionally crashing after N steps."""
    executed = 0
    skipped = 0
    total_tokens = 0
    saved_tokens = 0

    for i, step in enumerate(WORKFLOW_STEPS):
        if crash_after is not None and i >= crash_after:
            return {
                "status": "crashed",
                "executed": executed,
                "skipped": skipped,
                "total_tokens": total_tokens,
                "saved_tokens": saved_tokens,
                "crash_at_step": i,
            }

        if log.is_completed(step["id"]):
            skipped += 1
            saved_tokens += step["cost_tokens"]
            continue

        log.record(step["id"], "started", cost_tokens=0)
        result = execute_step(step)
        log.record(step["id"], "completed", result=result, cost_tokens=step["cost_tokens"])
        executed += 1
        total_tokens += step["cost_tokens"]

    return {
        "status": "completed",
        "executed": executed,
        "skipped": skipped,
        "total_tokens": total_tokens,
        "saved_tokens": saved_tokens,
    }


def main():
    parser = argparse.ArgumentParser(description="Experiment 25: Durable Harness")
    parser.add_argument("--crash-after", type=int, default=4)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 25: Durable Harness — Step-Log Resume")
    print("=" * 65)
    print()
    print("--- Local log and resume; simulated crash and token costs ---")
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "step_log.jsonl")

        # Phase 1: Run until crash
        print(f"Phase 1: Running workflow (crash after step {args.crash_after})...")
        log1 = StepLog(log_path)
        start1 = time.monotonic()
        result1 = run_workflow(log1, crash_after=args.crash_after)
        time1 = time.monotonic() - start1
        print(f"  Status: {result1['status']}")
        print(f"  Steps executed: {result1['executed']}")
        print(f"  Tokens spent: {result1['total_tokens']:,}")
        print(f"  Time: {time1:.4f}s")
        print()

        # Phase 2: Resume from step log
        print("Phase 2: Resuming from step log...")
        log2 = StepLog(log_path)
        start2 = time.monotonic()
        result2 = run_workflow(log2)
        time2 = time.monotonic() - start2
        print(f"  Status: {result2['status']}")
        print(f"  Steps skipped (from log): {result2['skipped']}")
        print(f"  Steps executed (new): {result2['executed']}")
        print(f"  Tokens spent: {result2['total_tokens']:,}")
        print(f"  Tokens saved (not re-run): {result2['saved_tokens']:,}")
        print(f"  Time: {time2:.4f}s")
        print()

        # Phase 3: Compare with fresh run (no crash)
        fresh_log_path = os.path.join(tmpdir, "fresh_log.jsonl")
        log_fresh = StepLog(fresh_log_path)
        start_fresh = time.monotonic()
        result_fresh = run_workflow(log_fresh)
        time_fresh = time.monotonic() - start_fresh

    total_crash_tokens = result1["total_tokens"] + result2["total_tokens"]
    fresh_tokens = result_fresh["total_tokens"]
    token_savings = result2["saved_tokens"]
    token_savings_pct = token_savings / fresh_tokens * 100

    print("Comparison:")
    print(f"  {'Metric':<30} {'Fresh Run':>12} {'Crash+Resume':>12}")
    print(f"  {'-'*56}")
    print(f"  {'Total tokens':<30} {fresh_tokens:>12,} {total_crash_tokens:>12,}")
    print(f"  {'Tokens saved by resume':<30} {'n/a':>12} {token_savings:>12,}")
    print(f"  {'Savings %':<30} {'n/a':>12} {token_savings_pct:>11.1f}%")
    print(f"  {'Total time':<30} {time_fresh:>12.4f}s {time1 + time2:>12.4f}s")
    print()
    print(f"Conclusion: Skipping {result2['skipped']} recorded steps avoided an estimated")
    print(f"{token_savings:,} tokens ({token_savings_pct:.0f}% of modeled fresh-run tokens) on resume.")
    print("Incomplete steps may replay (at-least-once attempts on retry), including")
    print("after an effect succeeds but before completion is logged; exactly-once is not guaranteed.")
    print("Effects require idempotency or external deduplication for safe retries.")

    summary = {
        "experiment": "25_durable_harness",
        "simulated": True,
        "semantics": "At-least-once attempts on retry: effects may replay before completion is logged; idempotency or external deduplication is required. No exactly-once guarantee.",
        "limitations": "Crash is simulated between steps; token costs are estimates. Log writes are not transactional or fsync-protected.",
        "crash_after_step": args.crash_after,
        "total_steps": len(WORKFLOW_STEPS),
        "fresh_run_tokens": fresh_tokens,
        "crash_resume_tokens": total_crash_tokens,
        "tokens_saved": token_savings,
        "tokens_saved_pct": round(token_savings_pct, 2),
        "steps_skipped_on_resume": result2["skipped"],
        "steps_executed_on_resume": result2["executed"],
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
