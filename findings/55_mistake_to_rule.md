# Finding 55: Mistake-to-Rule Loop + Instruction Diet

## Idea

Two parts:

**(a) Mistake-to-rule:** Turn repeated agent failures into automated checks
(lint rules, test assertions, git hooks). When the same mistake appears
twice, add a check that blocks it. Measure how many repeat failures the
checks prevent.

**(b) Instruction diet:** Prune unneeded always-loaded instructions from
AGENTS.md and tool definitions. Measure the token reduction and whether
task success changes.

## Experiment Design

(a) Plant repeated failures in sample logs, derive checks, measure block rate.
(b) Compare full vs pruned instructions on sample tasks.

**Measured: real token counts, real pytest for derived checks.**
