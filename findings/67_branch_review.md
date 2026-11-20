# Finding 67: Whole-Branch Review Before Done

## Source

<https://x.com/alexmichael/status/2123541121271812523>

## Idea

Before marking a branch "done," a reviewer checks the entire branch diff
(not just the last commit). Catches cross-file bugs that per-commit review
misses. Findings are sent back to the worker for one fix round.

## Experiment Design

Build branches with planted multi-file bugs plus clean branches. Run a
reviewer (rule-based, no real LLM — clearly labeled). Measure bugs caught,
false flags, extra tokens, and whether one fix round resolves them.

**Real git + pytest. Reviewer is a rule-based stand-in, not a real model.**
