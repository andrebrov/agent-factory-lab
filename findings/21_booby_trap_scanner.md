# Finding 21: Booby-Trapped Repos — Scan Before Opening

## Source

<https://x.com/its_LtDan/status/2114390037835968857>

## Idea

`core.fsmonitor` in a repo's `.git/config` runs an arbitrary command on every
`git status`. This means cloning and inspecting an untrusted repo can execute
code before the agent even looks at the source. Other attack vectors:
- `.git/hooks/` (post-checkout, pre-commit, etc.)
- `.mcp.json` (MCP server definitions that auto-connect)
- `AGENTS.md` / `CLAUDE.md` (prompt injection via agent instructions)

Defense: open untrusted repos in a container first, and **scan** `.git/config`,
hooks directory, `.mcp.json`, and agent instruction files before any `git`
operation.

## Proposal for Gwaihir / Rex

1. Before any `git status`, `git checkout`, or `git diff` on an untrusted
   repo, run a scanner that checks for:
   - `core.fsmonitor`, `core.hooksPath`, `core.sshCommand` in `.git/config`
   - Executable files in `.git/hooks/`
   - `.mcp.json` with `command` or `url` fields
   - Suspicious directives in `AGENTS.md` / `CLAUDE.md`
2. If threats are found: neutralize (remove the offending config) or refuse
   to proceed.
3. For maximum safety: clone into a container, scan, then mount the
   cleaned worktree.

## Experiment Design

**What can be tested in-sandbox:** Build a booby-trapped repo with
`core.fsmonitor`, malicious hooks, and `.mcp.json`, then run the scanner
and verify it detects/neutralizes all threats.

**Real execution** — fully runnable.
