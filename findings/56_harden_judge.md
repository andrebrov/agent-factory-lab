# Finding 56: Harden the Judge — Tamper-Proof Review Rules

## Idea

Load gate and review rules from the **base branch**, not the PR branch, so a
PR cannot edit its own rules. Tie each approval to a commit SHA and void it
on a new push. Escalate to a human after 3 failed fix rounds.

## Experiment Design

Create crafted branches that try to (a) edit their own review rules, (b)
reuse a stale approval after pushing new commits. Measure attempts blocked,
false blocks on clean branches, and overhead.

**Real git execution.**
