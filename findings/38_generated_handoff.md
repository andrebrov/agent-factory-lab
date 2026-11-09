# Finding 38: Generated Session Handoff from Git Log + Spec (No Model Call)

## Sources

- Relai handoff: <https://x.com/GaultRudy/status/2119471161528484324>
- Stale-TODO trap: <https://x.com/deltaxevaluate/status/2119581458461581313>

## Idea

Build a handoff file automatically from structured sources — no LLM call
needed:
1. Recent git log (last N commits with messages)
2. Open tasks/issues
3. The task spec

This is cheaper and faster than having a model summarize the session, and
the output is deterministic.

Additionally, scan for stale TODOs — agents waste steps chasing TODO comments
that refer to already-completed work or obsolete requirements.

## Proposal for Gwaihir

1. On session handoff, auto-generate `HANDOFF.md` from:
   - `git log --oneline -20`
   - Open GitHub issues assigned to the agent
   - The current task spec
2. Scan the codebase for TODO/FIXME/HACK comments and flag any that reference
   completed commits or closed issues.
3. Include a stale-TODO section in the handoff so the next agent doesn't
   waste time on them.

## Experiment Design

**What can be tested:** Generate a handoff from the lab repo's own git log,
measure tokens, and scan for stale TODOs in the sample codebase.

**Real execution.**
