# Finding 48: Stale-Instruction Guard for AGENTS.md

## Idea

AGENTS.md can go stale: its instructions contradict the code that evolved
since they were written. Agents following stale instructions introduce
regressions.

Two defences:
1. Add a meta-instruction: "When existing code consistently contradicts
   these instructions, follow the code and flag the mismatch."
2. Build a checker that flags instruction lines whose described targets
   (files, functions, patterns) are newer in git than the instruction.

## Experiment Design

Plant stale instructions, measure compliance with and without the override
directive. Build the staleness checker and measure precision/recall.

**Real git execution + simulated agent compliance.**
