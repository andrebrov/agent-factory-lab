# Finding 6: SuperPlane Backlog-to-Ship Pattern

## Source

<https://x.com/darkofabijan/status/2115037955480048100>

## Idea

The SuperPlane pattern automates the full lifecycle from backlog item to
shipped code:

1. **Backlog triage:** An agent reads the issue/ticket, classifies complexity,
   and decides if it can be handled autonomously.
2. **Planning:** The agent produces a plan (which files to change, what tests
   to write) and optionally gets human approval.
3. **Execution:** The agent implements the plan, writes tests, and opens a PR.
4. **Review & ship:** Automated review (or human review for complex changes)
   followed by merge and deploy.

This is essentially a "coding factory" pattern — exactly what Landroval/Rex
aims to be. The key insight is treating the **entire pipeline** as automatable,
not just the code-writing step.

## Proposal for Landroval

Landroval already covers steps 2-3. To complete the SuperPlane pattern:

1. **Add backlog triage:** Landroval watches the issue tracker (Linear, GitHub
   Issues) and picks up issues tagged for automation.
2. **Add planning approval gate:** Before executing, Landroval posts its plan
   as a PR comment or Slack message and waits for approval (or auto-approves
   low-risk plans).
3. **Add deploy trigger:** After merge, Landroval triggers the deploy pipeline
   (or confirms it ran successfully).
4. **Metrics:** Track cycle time (issue created → PR merged → deployed) and
   compare with human-driven cycle time.

## Experiment Design

**Note:** This finding is primarily architectural — it describes a pattern
rather than a technique that can be microbenchmarked. The experiment is
therefore a **design exercise and protocol** rather than a runnable benchmark.

**Deliverable:**
- A state-machine diagram of the SuperPlane pipeline.
- A checklist of capabilities Landroval needs to complete the pattern.
- A protocol for measuring cycle time once the pattern is implemented.

**What can be tested in-sandbox:**
- The state-machine implementation (as a Python class) — runnable.
- Simulated issue → plan → execute → merge flow.

**What requires Landroval/Rex:**
- Actual integration with issue trackers and deploy pipelines.
