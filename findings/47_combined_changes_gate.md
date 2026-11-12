# Finding 47: Combined-Changes Gate for Parallel Worktrees

## Idea

When agents work in parallel worktrees, each branch passes its own tests.
But branches can conflict semantically: one changes an interface, another
uses the old one. Per-branch testing misses this.

The gate: before merging, create a temporary branch combining all pending
changes, run the full suite, and do a combined-diff check. Catches
integration conflicts that per-branch testing misses.

## Experiment Design

Build 2–3 branches with semantic conflicts, test per-branch and combined.
Measure breaks caught, false positives, and added runtime.

**Real execution** on the sample codebase with real git + pytest.
