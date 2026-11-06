# Finding 36: Session Migrate/Restore + Pegboard Config Sync

## Sources

- moshi-hook mux migrate/dump/restore: <https://getmoshi.app/docs/multiplexer-migrate>
- Pegboard (single config → multiple harnesses): <https://x.com/rmandevs/status/2118485153685066133>

## Idea

### 36a: Session Migrate/Restore (moshi-hook)

`moshi-hook mux migrate` moves workspaces and agent sessions between
multiplexers (tmux, herdr, Rex). `mux dump` saves layout + sessions to a
file; `mux restore` rebuilds them after a reboot. This gives:
- Survive reboots without losing agent state.
- Move agents between multiplexers without restarting them.
- Fork a layout by restoring the same dump to multiple targets.

### 36b: Pegboard — Single MCP/Skills Config

Maintain one configuration file (`pegboard.json`) that describes all MCP
servers, skills, and tool definitions. Sync it to multiple agent harnesses
(Claude Code, Codex, Rex) so they all share the same capabilities without
per-harness configuration drift.

## Proposal for Gwaihir / Rex

1. Integrate `moshi-hook mux dump/restore` into the session durability
   pipeline (Finding 5, Finding 17).
2. Use Pegboard to keep MCP/skills config in sync across harnesses.

## Experiment Design

**What can be tested:**
- moshi-hook mux: `ls` and `migrate --dry-run` work (installed 0.4.50);
  `dump`/`restore` need 0.4.51+ (not available yet).
- Pegboard: prototype a config-sync mechanism and measure drift.
- tmux session dump/restore simulation as a fallback.
