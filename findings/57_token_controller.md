# Finding 57: Per-Repo Token Controller (TokenEconomizer-style)

## Idea

Keep a per-repo facts file learned from past runs (build commands, test
patterns, env vars needed). Inject these facts at session start. Turn off
unused tools/MCPs. Stop loops after N iterations where tests aren't improving.
Compare against existing baselines (exp 3 batching, exp 4 caching, exp 42
efficiency stack).

## Experiment Design

Build a facts file for the sample codebase, measure tokens per task with and
without facts injection, tool pruning, and loop stopping. Real tiktoken.

**Measured: real token counting. Pass rate on sample tasks.**
