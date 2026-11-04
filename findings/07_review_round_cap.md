# Finding 7: Cap AI Review at 3 Rounds with a Findings Log

## Sources

- <https://x.com/i/status/2114604912520921136>
- <https://x.com/Bic_Revelation/status/2115286181592346745>

## Idea

Unbounded review loops waste tokens and rarely converge after 3 rounds. Cap
AI code review at 3 rounds maximum and maintain a `findings.jsonl` log that
the reviewer must check before commenting — avoiding repeated notes on the
same issue. After round 3, the coder re-plans from scratch instead of
attempting another incremental fix.

## Proposal for Gwaihir

1. Set `MAX_REVIEW_ROUNDS = 3` in the writer/reviewer pipeline.
2. Each review round appends its findings to a structured `findings.jsonl`.
3. Before generating a new review, the reviewer reads `findings.jsonl` and
   skips any issue already noted.
4. After round 3, if still not approved, the writer discards its approach and
   re-plans from the original task description.

## Experiment Design

**Goal:** Measure rounds, tokens per PR, and escaped bugs under capped vs
uncapped review.

**Success criterion:** Rounds and tokens drop by ≥30% with no increase in
escaped bugs.

**What can be tested in-sandbox:** Simulate review loops with configurable
round caps and measure token overhead from repeated context.

**What requires real models:** Whether the findings log actually prevents
repeated comments and whether re-planning after round 3 produces better code.
