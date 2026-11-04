# Finding 25: Vercel Durable Harness — Step-Log Resume

## Source

<https://x.com/vercel/status/2112653833382027729>

## Idea

Maintain a step log that records each completed step of an agent's workflow.
If the agent crashes, it resumes from the last completed step without
re-executing (and re-paying for) finished API calls.

This is a durable-execution pattern (similar to Temporal, Durable Objects)
applied to coding agents. Key properties:
- **Exactly-once semantics** for expensive operations (LLM calls, deploys).
- **Crash recovery** without human intervention.
- **Cost savings** from not re-running completed steps.

## Proposal for Gwaihir

1. Each sub-agent maintains a `step_log.jsonl` recording completed steps
   with their inputs, outputs, and timestamps.
2. On restart, the agent reads the step log and skips completed steps.
3. For idempotent operations, replay is safe; for non-idempotent operations
   (e.g., git push), the log records the outcome so the agent knows not to
   repeat it.

## Experiment Design

**What can be tested in-sandbox:** Implement a step-log harness, simulate
a crash mid-workflow, and measure recovery time and step replay.

**Real execution** — fully runnable.
