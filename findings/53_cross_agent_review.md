# Finding 53: Cross-Agent Review Gate (herdr-style)

## Idea

A writer agent produces a diff. A second-model reviewer examines it and
applies its findings before reporting done. The reviewer is a separate
agent instance with no shared history — a fresh perspective.

Compare writer-alone vs writer+reviewer on seeded-bug tasks: bugs caught,
false findings (reviewer wrongly rejects a correct fix), and extra tokens.

## Experiment Design

Apply correct and incorrect patches to the sample codebase. The "reviewer"
runs the targeted test on the original code (should fail = bug reproduces)
and on the patched code (should pass = fix works). If both conditions hold,
approve; otherwise reject and specify which condition failed.

No real LLM calls available — the reviewer is a deterministic test-based
gate (reimplementation of the herdr-style review). Labeled as such.

**Real pytest execution, simulated agent decision-making.**
