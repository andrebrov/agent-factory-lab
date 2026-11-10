# Finding 40: Two-Layer Eval Gate + Structured Report Protocol (dsh-superagent)

## Source

- Repo: <https://github.com/deepseek-ai/dsh-superagent-prototype>
- Paper reference: *Towards a More Autonomous Agent System* (adapted for publication)

## What dsh-superagent Is

dsh-superagent is a research prototype from DeepSeek's Harness team for a
proactive coding agent that listens to GitHub/Feishu, triages incoming
requests, executes work in isolated per-ticket directories with git worktrees,
and reports back. It is **not** a production product — the repo has 1 commit,
11K+ lines of TypeScript, 60 test files, MIT license, and a disclaimer that
it may contain bugs and inconsistent engineering.

## Architecture Summary

- **Sources** (GitHub, Feishu) produce Triggers (immutable events).
- **Threads** group Triggers in time order per conversation/issue.
- **Eval** (two layers): a deterministic **gate** checks authorization and
  strength before an LLM-based **assessment** decides whether to accept work.
- **Tickets** are units of authorized work, each with a Mandate (scope,
  strength, policy version).
- **Executors** run in isolated sessions with their own worktree directories.
- **Structured Reports**: workers report one of 6 states
  (`progress|waiting|ready|blocked|failed|dropped`) — never free text status.
- **Orchestrator separation**: the main session only routes; it never makes
  technical decisions or reads code.
- **Background work**: shell jobs move to background after 5s; a 30-min
  timeout kills stuck jobs.
- **Recovery**: on restart, interrupted assignments resume with a recovery
  note; the agent checks git history before repeating outside actions.

## Most Transferable Mechanisms

### 1. Two-Layer Eval Gate (deterministic pre-filter + LLM assessment)

Before any model call, a deterministic gate checks:
- Is the sender authorized (on the allowed list)?
- Does the trigger have sufficient strength (explicit request vs inferred)?
- Is there already an active ticket for this thread?
- Is the policy version current?

Only triggers that pass the gate reach the LLM for assessment. This avoids
wasting model calls on unauthorized, duplicate, or policy-violating requests.

### 2. Structured Report Protocol

Workers report structured states, not free text. The orchestrator makes
deterministic routing decisions based on the state:
- `ready` → attempt merge / notify reviewer
- `blocked` / `failed` → halt automatic input, wait for human
- `waiting` → idle, can receive new triggers
- `dropped` → end ticket, no PR needed
- `progress` → working, no action needed

This eliminates the "is it done?" ambiguity that causes premature completion
claims (Finding 10) and wasted polling (Finding 35).

## Experiment Design

**What can be tested:** Implement both mechanisms in Python and measure:
1. Gate: how many LLM calls are avoided by deterministic pre-filtering.
2. Reports: token cost of structured reports vs free-text status parsing.
Both tested on a synthetic but realistic stream of coding requests.

**What cannot be tested:** The full dsh-superagent system requires DeepSeek
Harness, API keys, and GitHub/Feishu integrations. The repo's `npm test`
was not attempted (TypeScript, pnpm, many dependencies); our experiment is a
faithful reimplementation of the two mechanisms, not a run of the original.
