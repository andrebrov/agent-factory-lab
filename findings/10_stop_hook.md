# Finding 10: Stop Hook — Block "Done" Until Tests, Typecheck, and Build Pass

## Sources

- <https://x.com/Cozy2054934/status/2113838957901537487>
- <https://x.com/Hotfixdaily/status/2112969533203869787>

## Idea

Agents frequently declare "done" prematurely. Add a stop hook that gates
the "done" signal on three checks: test suite passes, typecheck passes,
and build succeeds. The agent's completion report must include the actual
command output as evidence.

## Proposal for Gwaihir and Rex

1. Before any sub-agent can report completion, the orchestrator runs:
   - `pytest` (or the project's test runner)
   - `mypy` / `tsc` (typecheck)
   - `make build` / `npm run build` (build)
2. If any check fails, the agent is told to fix the issue, not mark done.
3. The completion report includes raw command output as evidence.

## Current experiment limitation

Experiment 10 validates only the buggy and fixed pytest fixtures (10 tests each).
It does not measure reopening frequency, hidden-test performance, typecheck/build
gating, or general completion reliability. Partial-fix examples are simulated.

## Experiment Design

**Goal:** Measure reopen rate and hidden-test pass rate with and without the
stop hook.

**What can be tested in-sandbox:** Run the sample codebase's test suite as a
stop hook and measure how often a simulated agent's "done" signal is gated.

**What requires real models:** Whether agents can reliably fix issues surfaced
by the stop hook without entering infinite fix loops.
