# Finding 41: Subagent Spawn — Short Task File vs Cloned History

## Source

<https://x.com/Les_pauvres/status/2120133322722713787>

## Idea

When spawning a sub-agent, pass a short task file (< 400 tokens) containing
only target paths, constraints, and acceptance checks — not the parent
session's full history. The sub-agent starts with a clean context focused
entirely on its task.

This differs from Finding 38 (generated handoff): handoff transfers *ongoing
session state* between peers, while spawn starts a *fresh child* for a scoped
subtask. Handoff preserves context continuity; spawn intentionally discards it.

## Proposal for Gwaihir

1. When Gwaihir spawns a sub-agent, generate a task file (< 400 tokens):
   target files, constraints, acceptance criteria, and nothing else.
2. The sub-agent reads only the task file + the relevant source files.
3. No parent history, no transcript, no prior conversation.

## Experiment Design

**What can be tested:** Measure tokens per task for task-file spawn vs
history-clone spawn. Compare on the sample codebase.

**Real token counting (tiktoken).**
