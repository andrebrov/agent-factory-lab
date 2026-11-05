# Finding 33: Write/Review Router — Strong Model for Judgment, Cheap for Checks

## Source

- <https://x.com/SysDesignSimple/status/2118289925141340175>

## Idea

Extend the two-tier model routing (Finding 2) to the review phase: use a
strong/frontier model for judgment calls (architectural decisions, security
review, design critique) and a cheap/fast model for mechanical checks
(lint, type errors, test execution, formatting).

This is more granular than Finding 2's control-plane/data-plane split —
it applies specifically to the review step of the writer/reviewer pipeline
(Finding 1).

## Proposal for Gwaihir

1. When the reviewer examines a diff, classify each check as:
   - **Judgment:** needs frontier model (security, correctness, design)
   - **Mechanical:** can use cheap model (lint, types, formatting, tests)
2. Route accordingly. Mechanical checks run first (fast, cheap) as a gate;
   judgment checks run only if mechanical checks pass.
3. Estimated savings: mechanical checks are ~60-70% of review work.

## Experiment Design

**What can be tested:** Cost model extending experiment 2's pricing data,
applied specifically to the review phase.

**Simulated with real pricing data.**
