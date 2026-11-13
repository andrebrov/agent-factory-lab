# Finding 51: Compact Status Dashboard + Diff Review

## Idea

When reviewing N subagent results, raw scrollback is expensive to read.
A compact status table saves tokens. Adding a per-agent diff further
focuses the reviewer on what changed rather than re-reading everything.

## Experiment Design

Compare tokens and lines for raw scrollback, compact table, and table+diff
across N agents. Real tiktoken counts on realistic sample logs.

**Measured: real tiktoken on realistic logs.**
