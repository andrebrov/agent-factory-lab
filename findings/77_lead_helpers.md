# Finding 77: Lead-Owned Helpers with File-Ownership Plan

## Idea

Before opening helper panes, the lead writes a plan assigning each helper
its files. Helpers only open for real parallel work (independent file sets).
Helpers report to the lead, never to each other.

## Experiment Design

Real git fixture: uncoordinated baseline (overlapping edits) vs planned
(disjoint file assignments). Measure conflict rate and plan enforcement.
Parallel-work detection tested as a predefined rule with held-out cases.

**Git conflicts: MEASURED. Plan enforcement: RULE-BASED. Idle panes: not
measurable without a live herdr session — labeled as such.**
