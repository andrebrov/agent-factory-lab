# Finding 12: HANDOFF.md + Context-Window Restart Policy

## Sources

- <https://x.com/iskakovdev/status/2115803578145394794>
- <https://x.com/AaronDelz/status/2115120640072323162>

## Idea

Instead of passing the full transcript between agents or sessions, write a
`HANDOFF.md` file of under 60 lines that summarizes: what was done, what
remains, key decisions, and file locations. Restart a pane (fresh context)
past ~150K tokens or after 60 minutes idle — long contexts degrade quality.

## Proposal for Gwaihir

1. When a sub-agent finishes or is interrupted, it writes `HANDOFF.md` (max
   60 lines) summarizing state.
2. The next agent (or a resumed session) reads only `HANDOFF.md` plus the
   relevant source files — not the full prior transcript.
3. Auto-restart policy: if context exceeds 150K tokens or the session has
   been idle for 60 minutes, save `HANDOFF.md` and start a fresh pane.

## Experiment Design

**Goal:** Measure context-window token usage and information fidelity with
handoff files vs full-transcript pass-through.

**What can be tested in-sandbox:** Generate handoff summaries of varying
lengths and measure token counts; verify that key information survives the
compression by checking a checklist of facts.

**What requires real models:** Whether LLM-generated handoffs preserve the
right information and whether fresh-context agents perform as well as
long-context agents on the same task.
