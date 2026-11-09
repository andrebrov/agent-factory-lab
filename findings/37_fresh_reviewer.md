# Finding 37: Fresh-Reviewer Step — Spec-Based Review with Bug Reproduction

## Sources

- Elephant-Goldfish plugin: <https://x.com/ApollonVisual/status/2119718157589827748>
- Agent Reliability Engineering: <https://x.com/0xkvro/status/2119480383620149518>

## Idea

Each task starts with a short spec (what should change, what should not).
A fresh reviewer — with no history of the build process — checks the diff
against the spec and confirms:
1. The bug reproduces on the original code (before the fix).
2. The bug is gone after the fix.
3. No unrelated changes were introduced.

This catches cases where tests pass but the bug is still present (e.g., the
test was written to match the buggy behavior, or the fix addressed a symptom
rather than the root cause).

## Proposal for Gwaihir

1. Before a task begins, generate a 5-line spec: what's broken, what the
   fix should achieve, what the expected test behavior is.
2. After the builder finishes, a fresh reviewer (no session history) receives
   only the spec + the diff + the test results.
3. The reviewer independently runs the test against the original code (should
   fail) and the patched code (should pass).

## Experiment Design

**What can be tested:** Run spec-based review on the sample codebase with
seeded bugs. Include adversarial cases where tests pass but the fix is wrong.

**Real execution** on the sample codebase.
