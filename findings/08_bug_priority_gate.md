# Finding 8: Bug Priority Gate — Fix Only When freq × severity ≥ 5

## Source

<https://x.com/Voxyz_ai/status/2116575932957762004>

## Idea

Not every bug is worth fixing immediately. Gate bug-fix work on a priority
score: `frequency × severity`. Only fix bugs scoring 5 or above; otherwise,
file an issue and move on. Additionally, never treat a task as "done" on
another agent's word — always verify independently.

## Proposal for Gwaihir and Landroval

1. When a sub-agent reports a bug, Gwaihir computes the priority score from
   the bug's frequency (how often it triggers) and severity (impact level).
2. Bugs scoring < 5 are filed as issues, not fixed in the current PR.
3. The orchestrator independently verifies completion — never trusts a
   sub-agent's "done" signal without running its own checks.

## Experiment Design

**Goal:** Measure review comments, fix commits, and hidden-test pass rate
under gated vs ungated bug fixing.

**What can be tested in-sandbox:** Simulate a bug backlog with priority scores
and measure which bugs get fixed vs filed under different thresholds.

**What requires real models:** Whether agents correctly classify bug severity
and whether deferred bugs cause regressions.
