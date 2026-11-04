# Finding 3: Programmatic / Batched Tool Calling

## Source

<https://x.com/MilanGlow/status/2116089358709370962>

## Idea

Instead of issuing tool calls one at a time (read file → think → edit file →
think → read another file → …), batch many operations into a single script
that the model writes and the runtime executes. The cited result: **~312
individual tool calls / 3.1M tokens compressed to ~2 requests / 61K tokens.**

The mechanism:
1. Model reasons about what it needs to do.
2. Model emits a script (shell, Python) that performs all the reads, edits,
   and checks in one shot.
3. Runtime executes the script and returns the combined output.
4. Model inspects the output and iterates if needed.

This dramatically reduces round-trips, token overhead from repeated context
windows, and latency.

## Proposal for Gwaihir and Landroval

1. **Gwaihir:** When a sub-agent's task involves multiple file edits or a
   sequence of shell commands, prefer emitting a single script over individual
   tool calls. The herdr runtime already supports shell execution; add a
   "batch mode" that encourages script emission.
2. **Landroval/Rex:** The factory pattern naturally batches (one task = one
   script). Ensure Rex's prompt encourages writing complete scripts rather
   than incremental tool calls.
3. **Guardrail:** Scripts must be deterministic and idempotent where possible.
   Add a dry-run/preview step for destructive operations.

## Experiment Design

**Goal:** Measure token count and request count for per-call vs. batched-script
approaches on the same set of file operations.

**Setup:**
- Define a set of 20 file operations (reads, edits, creates, deletes) on the
  sample codebase.
- **Per-call mode:** Simulate (or execute) each operation as a separate tool
  call, counting the tokens in each request/response including the repeated
  system prompt and conversation context.
- **Batched mode:** Write a single Python script that performs all 20
  operations, count the tokens for the one request that contains the script
  plus the one response with the output.

**Metrics:**
- Total tokens (input + output) for each mode
- Number of API requests
- Simulated latency (requests × per-request latency)
- Error rate (does batching introduce more failures?)

**What can be tested in-sandbox:**
- Token counting with `tiktoken` — fully runnable.
- Actual file operations on the sample codebase.

**What requires real models:**
- Measuring whether models actually produce correct batch scripts as reliably
  as they produce individual tool calls.
