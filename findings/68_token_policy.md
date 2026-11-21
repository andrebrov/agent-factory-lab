# Finding 68: Token Policy for herdr Workers

## Idea

A four-part token policy: (a) compact context at a fixed limit even when
the model window is larger, (b) clear session between tasks, (c) default
to a cheap model with Opus reserved for planning, (d) send repo searches
to cheap scout subagents so the main worker doesn't read the repo.

## Experiment Design

Model token/cost for a multi-task sequence under this policy vs a baseline
that keeps one long Opus session reading the repo in context. Token sizes
are measured with tiktoken; costs are modeled from public pricing.

**Token sizes MEASURED. Cost model ESTIMATED. No real LLM calls.**
