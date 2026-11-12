# Finding 49: MCP Tool-Loading Audit — Token Cost of Upfront vs Deferred

## Idea

MCP servers inject tool definitions into the system prompt. Loading all
tools upfront adds thousands of tokens before the first user turn. Most
tools go unused in any given session.

Measure the token cost of:
- All tools loaded upfront
- Only frequently-used tools loaded; others deferred via search/describe
- Pruning servers the project never uses

## Experiment Design

Build realistic MCP tool definitions for common servers, measure tokens
with tiktoken, model the savings from pruning and deferral.

**Real token counting (tiktoken) on representative tool definitions.**
