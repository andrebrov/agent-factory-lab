# Finding 45: Blocking-Only Reviewer + Eval-First Loop

## Source

- <https://x.com/YunfengB/status/2120196033716310276>

## Idea

Restrict the reviewer to blocking issues only: bugs, failing tests, scope
creep. No style nits, no formatting comments, no "consider renaming this
variable." Pair with an eval-first loop: write the test/eval first, confirm
it fails, write the fix, confirm it passes.

This reduces noise (fewer false rejections of good patches), keeps diffs
small (no style-driven rewrites), and focuses reviewer attention on what
actually breaks.

## Proposal for Gwaihir

1. Reviewer instructions: flag only bugs, test failures, security issues,
   and scope creep. Ignore style, naming, and formatting.
2. Eval-first loop: before writing any fix, write the failing test first.
   Confirm it fails. Then write the fix. Confirm the test passes.
3. Compare: defect catch rate, false rejections, comment count, diff growth.

## Experiment Design

**What can be tested:** Apply both unrestricted and blocking-only review
criteria to correct and adversarial patches. Measure catch rate, false
rejections, and comment count.

**Real pytest execution on the sample codebase.**
