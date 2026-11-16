# Finding 54: Resume-After-Restart for Rex-Style Panes

## Idea

Save each pane's agent type, session ID, and launch flags to a manifest.
On server restart, restore each pane with the correct session and flags.
Builds on exp 5 (session layer) and exp 36 (session migrate).

## Experiment Design

Create N tmux panes with distinct configurations, save a manifest, kill
and recreate the panes from the manifest, verify each pane's properties.
Measure restore correctness (fields match) and time.

**Real tmux execution.**
