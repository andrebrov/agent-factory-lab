# Finding 80: "Tests Must Fail Without the Change" Gate

## Idea

Before a PR counts as done, revert the non-test diff, keep the new/changed
tests, rerun them. If they still pass, the tests don't actually verify the
change. Auto-feed failures back to the agent.

## Experiment Design

Real git revert + pytest. Cases constructed BEFORE the gate: (a) tests that
fail when feature reverted, (b) tests that still pass (weak/unrelated),
(c) mixed, (d) test-only PR, (e) no-new-tests PR.

**Deterministic gate (git + pytest), not a model.**
