# Finding 50: 'Needs Human' Queue — Filter Agent Updates to Actionable Items

## Idea

Agents generate many status updates. Most are informational (running, done).
Only a few require human action (blocked, errored, waiting-for-input).
Filtering updates to only the actionable items reduces notification fatigue.

## Experiment Design

Simulate agent panes with states, compare all-updates vs filtered-to-blocked.
Measure message volume and state-detection accuracy on ambiguous pane text.

**Simulated states + measured state detection on labeled text samples.**
