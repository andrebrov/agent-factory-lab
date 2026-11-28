# Finding 90: Locked Acceptance Tests

## Source
<https://x.com/sonuv_dev/status/2126570118692147318>

## Idea
Keep acceptance tests in a folder worker lanes cannot write to. Reject any
diff that touches that folder. Prevents a worker from rewriting tests to
make a wrong implementation pass.

## Experiment
Diff-based gate on real git. Cannot simulate a real Rex/herdr lane — tests
only the gate. Cases constructed before the gate: test-folder edits (should
block), code-only diffs (should allow).
