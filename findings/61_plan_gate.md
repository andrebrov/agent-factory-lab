# Finding 61: Plan Gate + Context Hygiene (Read-Deny Rules)

## Sources

- <https://x.com/techNmak/status/2122945654326694125>
- <https://x.com/Geraltbhai/status/2122749188027064730>

## Idea

(a) On medium/high-risk tasks, review the plan before any code edits. Catch
bad plans (wrong files, missing tests, scope creep) before tokens are spent.

(b) Read-deny rules for lockfiles, fixtures, and generated files. Agents
waste tokens reading files they can't meaningfully edit.

## Experiment Design

(a) Label plans as good/bad, run through a plan checker, measure catches.
(b) Apply deny rules to a file list, measure tokens saved vs files blocked
that were actually needed.

**Measured: real tiktoken for (b). Pattern matching for (a).**
