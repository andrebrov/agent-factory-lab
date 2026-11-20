# Finding 65: Agent Inbox — Human Reply Queue

## Source

<https://x.com/plannotator/status/2123539854802010353>

## Idea

A single inbox where agents waiting on the human post messages, questions,
and reviews. The human replies when available. Agents don't block — they
continue or end their turn after writing. Inspired by Plannotator Inbox.

Plannotator is not installable in this headless VM (requires browser + agent
hooks). This experiment builds a minimal equivalent.

## Experiment Design

Build a minimal inbox, populate with agent messages, measure: did the right
items surface, could any be missed, how many steps to reply. Compare with
exp 64's needs-you view.

**Measured: inbox logic on labeled messages.**
