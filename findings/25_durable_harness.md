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

**What can be tested in-sandbox:** Implement a step-log harness, simulate
a crash mid-workflow, and measure recovery time and step replay.

The log and resume run locally with synthetic steps and estimated token costs.
The crash is simulated between steps, not an actual process or power failure;
the log has no fsync or transactional crash-consistency guarantee.
