# Finding 29: AGENTS.md Size Check & Repo Root Guard

## Source

Internal lab finding — operational hygiene for agent configuration.

## Idea

Two lightweight guards:

1. **AGENTS.md size check:** Warn when the combined AGENTS.md (plus any
   included files) exceeds 32 KiB. Oversized agent instructions waste tokens
   on every request and often contain stale or contradictory rules.

2. **Repo root guard:** Refuse to start agents outside a git repo root or
   worktree. Running agents from a subdirectory or non-repo path leads to
   broken relative paths, missing configs, and wasted debugging time.

## Proposal for Gwaihir / Rex

1. Before starting any agent session, check:
   - `AGENTS.md` + `CLAUDE.md` total size ≤ 32 KiB. Warn if exceeded.
   - Current directory is a git repo root or worktree root. Refuse if not.
2. These checks take <1ms and prevent common misconfigurations.

## Experiment Design

**Fully testable in-sandbox** — both checks are simple file/directory operations.
