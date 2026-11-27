# Finding 86: Docs-vs-Code Rule in AGENTS.md

## Source

<https://x.com/HowToPrompt__/status/2125982259635528171>

## Idea

AGENTS.md rule: "When the documentation and existing code disagree, follow
the code's conventions, and in your final reply, list all the inconsistencies
you found."

## Experiment Design

Build a fixture where docs and code clearly disagree in several places.
Test a deterministic mismatch checker (NOT a real coding agent) that flags
doc/code disagreements and verifies they are listed.

**Deterministic checker, not a model. Does not prove an agent will follow
the rule — only that the mismatches are detectable.**
