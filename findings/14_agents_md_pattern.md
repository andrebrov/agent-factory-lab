# Finding 14: AGENTS.md as Single Source + CLAUDE.md Pointer

## Sources

- <https://x.com/mariioalexandre/status/2116333676048892182>
- <https://x.com/sachintwtss/status/2114947225780355191>
- <https://x.com/triedthatai/status/2117255711537426839>

## Idea

Maintain one `AGENTS.md` as the single source of truth for agent configuration
(rules, style, constraints). Then create a `CLAUDE.md` that simply says
`@AGENTS.md` — a pointer, not a copy. For sub-agents, use `omitClaudeMd` so
they inherit only what's relevant, avoiding conflicting or stale instructions.

## Proposal for Gwaihir and Rex

1. Write one `AGENTS.md` in the repo root with all agent rules.
2. `CLAUDE.md` contains only `@AGENTS.md` (or a short include directive).
3. Sub-agents spawned by Gwaihir use `omitClaudeMd` and receive a
   task-specific subset of rules from the orchestrator.
4. No duplication of rules across files — single source of truth.

## Experiment Design

**Goal:** Measure config drift and instruction consistency across agent
configurations.

**What can be tested in-sandbox:** Simulate multi-file configs, introduce
edits, and measure divergence rates (single-source vs duplicated).

**What requires real models:** Whether agents follow the `@AGENTS.md` pointer
correctly and whether `omitClaudeMd` improves sub-agent focus.
