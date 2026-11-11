# Finding 46: Cut Discovery Tokens — Quiet Tools + Trimmed Config + Agent Diff Guard

## Sources

- <https://x.com/Prayag12B/status/2120238060101390800>
- <https://x.com/benny1388/status/2120360462789537847>
- Malicious-gem context: <https://x.com/SagarKant14/status/2120351735537647647>

## Idea

Four levers to cut tokens spent during discovery/exploration:

1. **Quiet test/tool flags:** `pytest -q`, `vitest --reporter=dot` — output
   only pass/fail counts, not full test names and tracebacks.
2. **Trimmed AGENTS.md:** commands + gotchas only, no philosophy or history.
3. **Exploration sub-agent:** send a sub-agent to explore, return a ~10-line
   summary instead of dumping the full codebase into context.
4. **Compact before idle:** if cache TTL is ~5 min (API) or ~1 hr
   (subscription), compact context before the cache expires.

Additionally, add a diff guard that flags any commit touching `AGENTS.md` or
`CLAUDE.md` — a supply-chain attack vector where malicious instructions are
injected via seemingly innocuous PRs.

## Proposal for Gwaihir / Rex

1. Default to quiet output flags for all test/tool invocations.
2. Keep AGENTS.md under 2 KiB: commands, gotchas, tool names. Nothing else.
3. For repo exploration, spawn a sub-agent (exp 41) that returns summaries.
4. Add a pre-commit or PR check that alerts on AGENTS.md/CLAUDE.md changes.

## Experiment Design

**What can be tested:** Measure token savings from quiet flags, trimmed
configs, and sub-agent summaries. Test the diff guard on injected changes.

**Real token counting (tiktoken) + real git diff guard.**
