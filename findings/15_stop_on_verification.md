# Finding 15: Stop Writing Once Verification Passes

## Source

<https://x.com/Best_Ethan_/status/2116070176395301057>

## Idea

Once all verification checks pass (tests, typecheck, build), the agent should
stop immediately — no verbose summary, no restating what it did. Emit a 3-line
completion report and use lower reasoning effort on the final turn. Particle
reports ~45% fewer output tokens with this approach (their own benchmarks).

## Proposal for Gwaihir and Rex

1. After verification passes, the agent emits only:
   - Status: PASS
   - Files changed (list)
   - Tests passed (count)
2. The final turn uses reduced reasoning effort (lower temperature, shorter
   max_tokens, or a cheaper model).
3. No summary paragraphs, no explanations of what was done.

## Experiment Design

**Goal:** Measure output token reduction and whether quality is maintained.

**What can be tested in-sandbox:** Simulate verbose vs terse completion
messages and count tokens. Model the cost savings.

**What requires real models:** Confirming the ~45% output token reduction
(Particle's benchmark) and verifying that terse completions don't omit
critical information.
