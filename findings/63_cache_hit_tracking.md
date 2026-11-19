# Finding 63: Cache-Hit Tracking + Prompt Ordering

## Sources

- <https://x.com/nrachabathuni/status/2123326645025050860>
- <https://x.com/a2agent_ai/status/2123042082139025625>

## Idea

Log cached vs uncached tokens per task. Compare putting stable content first
(system prompt, repo facts, tools) with changing content last against mixed
ordering. Also compare chained tool calls (one script) vs sequential calls
by tokens returned to context.

## Experiment Design

Model cache-hit rates for different prompt orderings over a multi-turn
session. Measure tokens with tiktoken. No API key available — modeled, not
measured against a real cache endpoint.

**Modeled: token counts MEASURED (tiktoken), cache behavior MODELED.**
