# Finding 11: Mutation Check — Deliberate Breaks to Verify Test Quality

## Source

<https://x.com/ganesh2412/status/2115458572519968930>

## Idea

After an agent writes code and tests, verify test quality by mutation testing:
make 3–5 deliberate breaks in each changed function and require at least one
test to fail for each mutation. If a mutation doesn't cause a test failure,
the test suite has a blind spot.

## Proposal for Gwaihir

1. After a sub-agent completes a fix, Gwaihir generates 3–5 mutations per
   changed function (e.g., flip a comparison, remove a return, change a
   constant).
2. For each mutation, run the test suite. At least one test must fail.
3. If any mutation survives (no test fails), flag the test suite as
   incomplete and send the agent back to add tests.

## Experiment Design

**Goal:** Measure mutation kill rate and test completeness.

**What can be tested in-sandbox:** Apply mutations to the sample codebase's
fixed version, run the test suite, and measure the kill rate.

**What requires real models:** Whether agents can generate effective mutations
and whether they write better tests after being told about surviving mutants.
