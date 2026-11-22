# Finding 73: Repo Map + "Who's Working Here" Pane

## Idea

Build on exp 70: give lanes a shared repo map plus a status pane showing
active agents and the files they're editing. Avoids overlapping edits.
Both baseline and treatment include real file-content reads.

## Experiment Design

Measure tokens with and without the map (including real file reads). Test
the status pane's agent-file listing and overlap detection accuracy.

**Measured: real tiktoken for map/files. Status pane logic on labeled agents.**
