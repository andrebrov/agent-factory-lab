#!/usr/bin/env python3
"""
Experiment 6: SuperPlane Backlog-to-Ship State Machine
=======================================================

Implements and exercises a state machine for the SuperPlane pattern:
issue → triage → plan → approve → execute → review → merge → deploy.

This is a design/protocol experiment — it validates the state machine
logic and simulates a full cycle, measuring transition times.
"""
import json
import os
import time
import argparse
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class State(str, Enum):
    BACKLOG = "backlog"
    TRIAGING = "triaging"
    PLANNING = "planning"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    MERGING = "merging"
    DEPLOYING = "deploying"
    SHIPPED = "shipped"
    ESCALATED = "escalated"
    FAILED = "failed"


TRANSITIONS = {
    State.BACKLOG: [State.TRIAGING],
    State.TRIAGING: [State.PLANNING, State.ESCALATED],
    State.PLANNING: [State.AWAITING_APPROVAL, State.EXECUTING],
    State.AWAITING_APPROVAL: [State.EXECUTING, State.ESCALATED],
    State.EXECUTING: [State.REVIEWING, State.FAILED],
    State.REVIEWING: [State.MERGING, State.EXECUTING, State.ESCALATED],
    State.MERGING: [State.DEPLOYING, State.FAILED],
    State.DEPLOYING: [State.SHIPPED, State.FAILED],
    State.SHIPPED: [],
    State.ESCALATED: [],
    State.FAILED: [State.BACKLOG],
}

RISK_THRESHOLDS = {
    "low": {"max_lines": 50, "max_files": 3, "auto_approve": True, "auto_merge": True},
    "medium": {"max_lines": 200, "max_files": 10, "auto_approve": True, "auto_merge": False},
    "high": {"max_lines": float("inf"), "max_files": float("inf"), "auto_approve": False, "auto_merge": False},
}


@dataclass
class Issue:
    id: str
    title: str
    lines_changed: int = 0
    files_changed: int = 0
    has_tests: bool = True
    complexity: str = "low"


@dataclass
class PipelineRun:
    issue: Issue
    state: State = State.BACKLOG
    history: list = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0

    def transition(self, new_state: State, reason: str = ""):
        allowed = TRANSITIONS.get(self.state, [])
        if new_state not in allowed:
            raise ValueError(
                f"Invalid transition: {self.state.value} → {new_state.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )
        self.history.append({
            "from": self.state.value,
            "to": new_state.value,
            "reason": reason,
            "timestamp": time.monotonic(),
        })
        self.state = new_state


def classify_risk(issue: Issue) -> str:
    for level in ["low", "medium", "high"]:
        t = RISK_THRESHOLDS[level]
        if issue.lines_changed <= t["max_lines"] and issue.files_changed <= t["max_files"]:
            return level
    return "high"


def run_pipeline(issue: Issue) -> PipelineRun:
    """Simulate a full SuperPlane pipeline run."""
    run = PipelineRun(issue=issue)
    run.start_time = time.monotonic()

    run.transition(State.TRIAGING, "Agent picks up issue")
    time.sleep(0.01)

    risk = classify_risk(issue)
    issue.complexity = risk

    if risk == "high" and not issue.has_tests:
        run.transition(State.ESCALATED, f"High risk ({risk}), no tests — escalate to human")
        run.end_time = time.monotonic()
        return run

    run.transition(State.PLANNING, f"Risk={risk}, generating plan")
    time.sleep(0.01)

    thresholds = RISK_THRESHOLDS[risk]
    if thresholds["auto_approve"]:
        run.transition(State.EXECUTING, "Auto-approved (low/medium risk)")
    else:
        run.transition(State.AWAITING_APPROVAL, "High risk — waiting for human approval")
        time.sleep(0.01)
        run.transition(State.EXECUTING, "Human approved")

    time.sleep(0.02)  # simulate code generation

    if issue.has_tests:
        run.transition(State.REVIEWING, "Code generated, tests passed")
    else:
        run.transition(State.FAILED, "Tests failed")
        run.end_time = time.monotonic()
        return run

    time.sleep(0.01)

    if thresholds["auto_merge"]:
        run.transition(State.MERGING, "Auto-merge (low risk, tests pass)")
    else:
        run.transition(State.MERGING, "Human review approved merge")

    time.sleep(0.01)
    run.transition(State.DEPLOYING, "PR merged, triggering deploy")
    time.sleep(0.01)
    run.transition(State.SHIPPED, "Deploy succeeded")

    run.end_time = time.monotonic()
    return run


SAMPLE_ISSUES = [
    Issue("ISS-1", "Fix typo in README", lines_changed=2, files_changed=1, has_tests=True),
    Issue("ISS-2", "Add input validation to API endpoint", lines_changed=45, files_changed=2, has_tests=True),
    Issue("ISS-3", "Refactor auth module", lines_changed=180, files_changed=8, has_tests=True),
    Issue("ISS-4", "Migrate database schema", lines_changed=500, files_changed=15, has_tests=True),
    Issue("ISS-5", "Emergency hotfix (no tests)", lines_changed=300, files_changed=12, has_tests=False),
]


def main():
    parser = argparse.ArgumentParser(description="Experiment 6: SuperPlane State Machine")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 6: SuperPlane Backlog-to-Ship State Machine")
    print("=" * 65)
    print()

    print("State machine transitions:")
    for state, targets in TRANSITIONS.items():
        targets_str = ", ".join(t.value for t in targets) if targets else "(terminal)"
        print(f"  {state.value:<20} → {targets_str}")
    print()

    print("Risk thresholds:")
    for level, t in RISK_THRESHOLDS.items():
        print(f"  {level:<8} max_lines={t['max_lines']:<6} max_files={t['max_files']:<4} "
              f"auto_approve={t['auto_approve']}  auto_merge={t['auto_merge']}")
    print()

    results = []
    print("Pipeline runs:")
    print("-" * 65)
    for issue in SAMPLE_ISSUES:
        run = run_pipeline(issue)
        cycle_time = run.end_time - run.start_time
        risk = classify_risk(issue)

        status_icon = {
            State.SHIPPED: "SHIPPED",
            State.ESCALATED: "ESCALATED",
            State.FAILED: "FAILED",
        }.get(run.state, "???")

        print(f"  {issue.id}: {issue.title}")
        print(f"    Risk: {risk}  |  Lines: {issue.lines_changed}  |  "
              f"Files: {issue.files_changed}  |  Tests: {issue.has_tests}")
        print(f"    Outcome: {status_icon}  |  Steps: {len(run.history)}  |  "
              f"Cycle: {cycle_time:.3f}s (simulated)")
        print(f"    Path: {' → '.join(h['to'] for h in run.history)}")
        print()

        results.append({
            "issue_id": issue.id,
            "title": issue.title,
            "risk": risk,
            "lines_changed": issue.lines_changed,
            "files_changed": issue.files_changed,
            "has_tests": issue.has_tests,
            "outcome": run.state.value,
            "num_steps": len(run.history),
            "cycle_time_sec": round(cycle_time, 4),
            "path": [h["to"] for h in run.history],
        })

    shipped = sum(1 for r in results if r["outcome"] == "shipped")
    escalated = sum(1 for r in results if r["outcome"] == "escalated")
    failed = sum(1 for r in results if r["outcome"] == "failed")

    print("Summary:")
    print(f"  Total issues:  {len(results)}")
    print(f"  Shipped:       {shipped}")
    print(f"  Escalated:     {escalated}")
    print(f"  Failed:        {failed}")
    print()

    landroval_checklist = [
        "Issue tracker integration (Linear, GitHub Issues)",
        "Automatic issue triage and risk classification",
        "Plan generation and approval gate",
        "Code generation in isolated worktree",
        "Automated test execution",
        "Risk-gated auto-merge",
        "Deploy pipeline trigger",
        "Cycle time metrics collection",
        "Escalation notifications (Slack/email)",
        "Retry/recovery for failed pipeline runs",
    ]
    print("Landroval capability checklist for full SuperPlane:")
    for i, item in enumerate(landroval_checklist, 1):
        print(f"  {i:>2}. {item}")

    print()
    print("Conclusion: The state machine correctly routes issues through the")
    print("pipeline, escalating high-risk/no-test cases and auto-merging low-risk")
    print("changes. Landroval needs 10 capabilities to complete the pattern.")

    summary = {
        "experiment": "06_superplane",
        "simulated": True,
        "issues": results,
        "summary": {
            "total": len(results),
            "shipped": shipped,
            "escalated": escalated,
            "failed": failed,
        },
        "landroval_checklist": landroval_checklist,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
