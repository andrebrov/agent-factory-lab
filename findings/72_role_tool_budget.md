# Finding 72: Per-Role Tool Budget

## Idea

Measure tokens each worker uses before its first prompt when all MCP servers
load. Then test loading only needed servers and loading the rest on demand.
Count the cost of discovering and loading a tool on demand, not only the
smaller initial prompt.

## Experiment Design

Define roles with tool needs, measure upfront vs on-demand tokens. Include
the on-demand discovery cost (search + describe + load) fairly.

**Measured: real tiktoken on representative tool definitions.**
