# Finding 35: Cheap Status Notes vs Re-Reading Full Transcripts

## Sources

- <https://x.com/sabrielatmojo/status/2118525147279687839>
- <https://x.com/jacobho79/status/2118547799126233579>
- <https://x.com/mareni_musashi/status/2118664526921142714>

## Idea

Agents frequently poll status by re-reading the full transcript or full file
contents. This is wasteful — the status can be captured in short summary
notes that cost a fraction of the tokens.

Additionally, when multiple agents work on the same task and diverge, an
append-only `decisions.md` log records which agent took which path and why,
preventing contradictory work.

## Proposal for Gwaihir

1. Replace transcript re-reads with short status notes (1-3 lines) appended
   to a running `status.md`.
2. Agents read `status.md` instead of scrolling back through history.
3. Add `decisions.md` — append-only log of key decisions with timestamps
   and agent IDs.
4. On divergence detection, the orchestrator reads `decisions.md` to
   reconcile.

## Experiment Design

**What can be tested:** Measure token cost of re-reading a full transcript
vs reading a short status note, across multiple polling intervals.

**Real token counting (tiktoken).**
