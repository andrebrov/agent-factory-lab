# Finding 34: Cache-Monotonic Prefix — Keep the Static Prefix Stable

## Source

<https://x.com/PatchOnChain/status/2118465641728622875>

## Idea

Prompt caching (Finding 4) saves money only when the prefix is stable across
turns. Volatile content near the head of the prompt — timestamps, UUIDs,
request IDs, randomized tool order — invalidates the cache and forces
re-processing of the entire prefix.

A **cache-monotonic prefix** means:
1. System prompt, tool definitions, and project context are fixed at the top.
2. Nothing volatile (timestamps, random IDs) appears before the first
   user message.
3. Tool definitions use a canonical JSON order (sorted keys, no whitespace
   variation).

Add a linter that flags violations before the agent starts.

## Proposal for Gwaihir / Rex

1. Lint the prompt template at startup: warn if any `${timestamp}`,
   `${uuid}`, or `Date.now()` appears in the static prefix.
2. Canonicalize tool JSON (sorted keys, consistent formatting).
3. Combined with Finding 4 (prompt caching) and Finding 28 (message threads),
   this maximizes cache hits.

## Experiment Design

**What can be tested:** Build the linter, measure cached vs uncached tokens
with and without volatile content in the prefix.

**Real token counting (tiktoken) + real linter execution.**
