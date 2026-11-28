# Finding 92: Measure Before Trimming Tokens

## Sources
- <https://x.com/EngineerHMS/status/2126600711337103638>
- <https://x.com/FarryQQQ/status/2126569400723718250>
- <https://x.com/TechScout0_0/status/2126660235423297541>

## Idea
Log billed tokens per lane (including cache hits and MCP overhead) BEFORE
adding token-saving wrappers. Turn off unused MCP servers per role first.

## Experiment
No API keys — cannot measure real billed tokens or cache hits. Implements
and unit-tests a logger. Measures MCP/tool schema overhead from fixture
descriptors (all-enabled vs role-trimmed). Costs labeled as modeled.
