# Finding 30: Verifier-Only Lane — Separate Build from Verify

## Sources

- <https://x.com/ddsvibeacademy/status/2117972668964085940>
- <https://x.com/KlapChatGame/status/2118249831827488811>

## Idea

Add a dedicated worker that never builds code — it only reviews diffs and
runs tests. The builder hands off via a commit (or a diff artifact); the
verifier checks it independently. This separation means the verifier never
has "builder's bias" (assuming its own code is correct).

Benefits:
- Verifier has a fresh perspective — no sunk-cost attachment to the code.
- Builder and verifier can run in parallel on different machines.
- If the verifier rejects, the builder gets structured feedback, not just
  "tests failed."

## Proposal for Gwaihir

1. Split the current writer/reviewer pipeline (Finding 1) into:
   - **Builder lane:** writes code, never runs tests.
   - **Verifier lane:** never writes code, only reviews + runs tests.
2. Hand off via git commit (builder pushes to a branch, verifier checks out).
3. Verifier produces a structured verdict: pass/fail + specific failures.

## Experiment Design

**What can be tested:** Simulate builder+verifier separation on the sample
codebase. Measure catch rate vs a single-agent baseline.

**What requires real models:** Whether the verifier actually catches issues
the builder would miss due to builder's bias.
