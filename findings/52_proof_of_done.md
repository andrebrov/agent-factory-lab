# Finding 52: Proof-of-Done Gate + Skill Budget Audit

## Idea

Agents sometimes claim "tests passed" falsely. A proof-of-done gate re-runs
the test command and requires the actual command line, exit code, and output
tail as evidence. This catches false claims without trusting agent self-report.

Additionally, measure how many skill descriptions fit in a 1% context budget
(~2K tokens for a 200K window) and when descriptions should be cut to names.

## Experiment Design

Plant true and false "done" claims, compare trust-only vs gate. Measure
catch rate, false flags, and runtime. Count skill tokens for budget analysis.

**Measured: real pytest execution for the gate, real tiktoken for skills.**
