# Finding 74: Regression Gate with Full-Read Check

## Idea

Before approval, run the full test suite (not just new tests) and fail if
any previously-passing test now fails. The review report must list every
changed file actually read. CI workflow or install-hook changes are auto-
escalated to a human.

## Experiment Design

Real test-runner gate (deterministic, not a model). Cases include: existing
test breaks, full suite stays green, secret-stealing CI/hook change. The
file-read checker is tested on reports with skipped files.

**All gates are deterministic rules, not LLM review. Labeled as such.**
