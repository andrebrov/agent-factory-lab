# Finding 81: Repo Map + Decisions + Traps on a Larger Fixture

## Idea

Keep map.md, decisions.md, and traps.md per repo. Load at pane start.
Measure tool calls and tokens before first edit.

Exps 70/73 used a 3-file repo. This experiment uses a larger fixture
(20+ files with nested directories and decoys).

## Experiment Design

Scripted search policy (not a live agent): with the map, open only named
files; without it, walk directories until the target is found. Same tasks
on both sides. Report tool calls, tokens, and whether quality was tested.

**Token counts MEASURED (tiktoken). Search policy is scripted, not a live
agent. Quality (finding the right file) checked on each task.**
