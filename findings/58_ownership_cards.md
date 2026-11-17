# Finding 58: Ownership + Status Cards

## Idea

Each spawned agent declares the branch or files it owns. A write by a second
agent without a handoff is blocked. Each pane keeps a one-line status card
(goal, blocker, next step), rolled up into a morning summary.

## Experiment Design

Simulate N agents with ownership claims, test conflict detection on overlapping
writes, measure false blocks on non-overlapping writes. Build status cards and
verify summary accuracy against labeled pane states.

**Measured: conflict detection logic. Simulated: agent write attempts.**
