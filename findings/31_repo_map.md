# Finding 31: Repo Map Before Reads — Folder Purposes + Hot Paths

## Source

- <https://x.com/moritzkrause_/status/2118137779213275196> (ProjectAtlas)

## Idea

Before opening any files, agents consult a short local map describing:
- Folder purposes (e.g., `src/auth/` = authentication module)
- Hot paths (most-edited files, files with most imports)
- Code graph (which modules depend on which)

This reduces wrong-file opens (agent reads irrelevant files) and cuts token
waste from reading code that doesn't matter for the task.

## Proposal for Gwaihir / Rex

1. Generate a `REPO_MAP.md` (or `.repomap.json`) at project setup time.
2. Before any file reads, the agent consults the map to pick the right
   files for the current task.
3. Regenerate the map periodically (or on significant structural changes).

## Experiment Design

**What can be tested:** Generate a repo map for the sample codebase, simulate
task routing with and without the map, and measure token usage and
wrong-file-open rate.

**Real execution** — fully runnable on the sample codebase.
