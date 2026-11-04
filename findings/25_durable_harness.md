# Finding 25: Vercel Durable Harness — Step-Log Resume

## Source

<https://x.com/vercel/status/2112653833382027729>

## Idea

Maintain a step log that records each completed step of an agent's workflow.
On restart it skips steps with a completion record. An effect that succeeds
before its completion is logged may be executed again on retry.

This is a durable-execution pattern (similar to Temporal, Durable Objects)
applied to coding agents. Key properties:
- **At-least-once attempts on retry**, not exactly-once effects: incomplete
  steps can replay. Safe retries require idempotent effects or external
  deduplication, such as a service-supported idempotency key.
- **Resume** skips completion records that can be read back.
- **Potential cost savings** from not re-running recorded steps.

## Proposal for Gwaihir

1. Each sub-agent maintains a `step_log.jsonl` recording completed steps
   with their inputs, outputs, and timestamps.
2. On restart, the agent reads the step log and skips completed steps.
3. Require idempotent effects or external deduplication/reconciliation before
   retrying non-idempotent operations. A local log cannot atomically record
   an external effect, so it cannot by itself prevent duplicates.

## Experiment Design

**What is tested in-sandbox:** A local step-log harness simulates an
interruption between synthetic steps and records skipped and executed steps.
Elapsed time is local wall-clock time for synthetic sleeps and file operations,
not production recovery time; token costs are assigned estimates, not measured usage.

The log and resume run locally with synthetic steps and estimated token costs.
The crash is simulated between steps, not an actual process or power failure;
the log has no fsync or transactional crash-consistency guarantee.
`--crash-after` accepts 1 through 9 for the ten-step workflow. Invalid,
malformed, or unterminated log records stop loading with a line number; no
record is silently discarded or automatically repaired. Manual reconciliation
is required before retrying because an effect may already have happened.

The JSON fields `skipped_step_tokens_on_resume` and
`skipped_step_tokens_pct_of_fresh` describe avoided re-execution during resume,
not net savings. For compatibility, `tokens_saved` and `tokens_saved_pct`
remain aliases for those values. `net_tokens_saved_vs_fresh` is fresh-run
estimated tokens minus total crash-plus-resume estimated tokens (zero in this
between-step simulation).
