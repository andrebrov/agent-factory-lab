# Finding 78: Cost per Merged PR + Cheaper Scout Subagents

## Idea

Log total tokens and cost per landed PR, including retries and subagent
calls. Produce a weekly top-5 most expensive PRs view. Pin read-only scouts
(grep, test runs) to a cheaper model.

## Experiment Design

Instrumentation test on synthetic PR traces with known totals (including
retries and nested subagents). Routing savings modeled from public pricing.
Scout quality untested without real model calls.

**Logger: MEASURED on synthetic traces. Routing savings: MODELED. Scout
quality: UNTESTED.**
