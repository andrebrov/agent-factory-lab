# Finding 64: Cross-Machine 'Needs You' View (herdr-switchboard style)

## Source

<https://x.com/AleJL98/status/2123064391788569087>

## Idea

Simulate several machines' pane states, sort by which need the human,
measure ranking accuracy and time to find the actionable pane. Reuses exp
58's status-card structure but fixes the keyword-match bug on 'done'.

## Experiment Design

Build a multi-machine pane inventory with labeled states. Rank by urgency.
Measure correct ranking, false urgency, and scan time vs flat list.

**Measured: ranking logic on labeled states.**
