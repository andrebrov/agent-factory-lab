# Finding 59: Hand Off Instead of Compacting

## Source

<https://x.com/omerbarness/status/2122846790475014623> (47% of cost was re-reading old chat)

## Idea

When a worker pane passes ~60% of its context window, instead of compacting
(summarize-and-keep-going), write a short handoff.md and start a fresh pane.
The fresh pane reads only the handoff + relevant files — no old chat history.

## Experiment Design

Simulate a multi-step task. Compare three modes: (a) keep going until context
full, (b) compact at 60%, (c) hand off at 60%. Measure tokens per finished
task and whether the task succeeds.

**Measured: real tiktoken. Simulated: task execution model.**
