# Finding 66: Token Budget per Worker

## Sources

- <https://x.com/iamleannmuller/status/2123508322477469721>
- <https://x.com/neuronium_ai/status/2123525329872384450>
- <https://x.com/Bzr495/status/2123529688802885868>

## Idea

Compare N parallel subagents each re-reading the same files against a capped
setup: limited concurrent subagents, one shared file summary, task-specific
MCP tool loading, and reasoning effort scaled by task size. Also measure the
cache cost of switching models mid-session.

## Experiment Design

Model token usage for parallel-with-duplication vs capped-with-sharing.
Measure token sizes with tiktoken. Check if the shared summary drops facts.

**Token sizes MEASURED (tiktoken). Concurrency model SIMULATED.**
