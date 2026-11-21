# Finding 69: "Done" Needs a Test Count

## Idea

A worker's done report must state how many tests ran out of the full suite,
e.g. "212/212". If the report cites only one file or gives no count, send
the work back. Catches incomplete test runs.

## Experiment Design

Build done reports: some with full counts, some with partial counts, some
with no counts. Run the gate. Measure catches and false rejections.

**Measured: gate logic on labeled done reports.**
