# Finding 4: Server-Side Conversation / Prompt Caching

## Source

- <https://x.com/ClaudeDevs/status/2117332449382510884>
- <https://x.com/tokenscost/status/2117638485075206393>

## Idea

Long coding sessions accumulate massive context windows. Without caching, every
API call re-sends the full conversation history, paying full price for tokens
the server has already processed. **Prompt caching** (offered by Anthropic,
OpenAI, and others) lets the server store and reuse prefixes of the
conversation, charging cached tokens at a steep discount (often 90% off).

Key considerations:
- Cached prefixes must be **stable** — appending to the end is fine, but
  inserting or reordering messages in the middle invalidates the cache.
- System prompts and tool definitions are ideal cache candidates (they never
  change within a session).
- For multi-turn sessions, keeping the conversation prefix stable maximizes
  cache hits.

## Proposal for Gwaihir and Landroval

1. **Structure prompts for cacheability:**
   - Put the system prompt, tool definitions, and project context at the
     **top** of every request (stable prefix).
   - Append new user/assistant turns at the **end** (growing suffix).
   - Never reorder or edit earlier messages mid-session.
2. **Enable cache control headers** where the API supports them (Anthropic's
   `cache_control` breakpoints, OpenAI's automatic prefix caching).
3. **Measure cache hit rate** in production to verify savings.
4. **Long sessions:** For sessions exceeding the context window, use a
   summary-and-reset strategy that preserves the cacheable prefix while
   compacting old turns.

## Experiment Design

**Goal:** Quantify the token-cost difference between cached and uncached
prompts across a simulated multi-turn coding session.

**Setup:**
- Simulate a 20-turn coding session with a realistic system prompt (~2K
  tokens), tool definitions (~1K tokens), and growing conversation.
- For each turn, compute:
  - **Uncached cost:** full input tokens × standard price.
  - **Cached cost:** cached prefix tokens × cached price + new tokens ×
    standard price.

**Metrics:**
- Total input tokens paid (cached vs. uncached)
- Cost savings (absolute and percentage)
- Cache hit rate (what fraction of tokens are cacheable)
- Break-even point (at which turn does caching start saving money, given
  the cache-write premium on the first call)

**What can be tested in-sandbox:**
- Token counting with `tiktoken` and cost modeling — fully runnable.
- Simulating the conversation structure and computing savings.

**What requires real models:**
- Actual API calls to verify cache hit behavior and real latency
  improvements.
