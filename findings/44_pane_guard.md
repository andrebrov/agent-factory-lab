# Finding 44: Don't Type Over the Human — Pane Input Guard

## Source

- stampede 0.1.9 on Herdr Core: <https://x.com/vib_z/status/2120457580153635135>

## Idea

Before injecting a message into a terminal pane, detect whether the human
has unsent input (a partial draft in the readline buffer). If input is
present, queue the agent's message until the draft is submitted or cleared.
Without this guard, the agent clobbers the human's typing.

Also add a doctor-style preflight check: verify the pane exists, is not in
a broken state, and has no pending input before sending.

## Proposal for Gwaihir / Rex

1. Before every `send-keys` to a tmux pane, read the current cursor position
   and input buffer.
2. If non-empty input is detected, queue the message and retry after a
   short delay.
3. Add a preflight check: pane exists, shell is at a prompt, no pending
   input.

## Experiment Design

**What can be tested:** Simulate a tmux pane with partial input, measure
clobber rate with and without the guard, and delivery latency.

**Real tmux execution.**
