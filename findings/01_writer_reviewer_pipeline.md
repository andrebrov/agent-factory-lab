# Finding 1: Cross-Model Writer/Reviewer/QA Pipeline

## Source

<https://x.com/brag_sheet/status/2117474234431869338>

## Idea

Use a multi-agent pipeline where distinct models fill separate roles — writer,
reviewer, and QA — each operating in an isolated git worktree. A risk gate
inspects the diff before auto-merging: low-risk changes merge automatically,
while high-risk changes pause for human review.

Key elements:
- **Writer agent** produces code in its own worktree.
- **Reviewer agent** (potentially a different model) reviews the diff for
  correctness, style, and security.
- **QA agent** runs tests and verifies the change doesn't regress.
- **Risk gate** scores the change (lines changed, files touched, blast radius)
  and decides merge vs. escalate.

## Proposal for Gwaihir

Make this pipeline Gwaihir's **default execution mode** for herdr multi-agent
coding tasks:

1. Gwaihir spawns a writer sub-agent on a fresh worktree branch.
2. On completion, a reviewer sub-agent receives the diff and produces
   structured feedback (approve / request-changes / reject).
3. If approved, a QA sub-agent runs the project's test suite and any
   Gwaihir-defined acceptance checks.
4. A deterministic risk gate (not LLM-based) scores the change:
   - **Low risk** (≤ N lines, no config/infra files, tests pass) → auto-merge.
   - **Medium risk** → merge with notification.
   - **High risk** → block and request human review.

## Experiment Design

**Goal:** Compare single-agent vs. writer+reviewer pipeline on a seeded-bug
sample codebase.

**Setup:**
- A small Python project with 10 intentionally seeded bugs of varying
  difficulty (off-by-one, missing null check, wrong operator, etc.).
- Each bug has a corresponding failing test.

**Single-agent baseline:**
- One simulated agent attempts to fix each bug. Success = test passes.

**Pipeline treatment:**
- Writer agent produces a fix; reviewer agent checks it; QA agent runs tests.
- The reviewer can reject and send back to the writer (max 2 rounds).

**Metrics:**
- Fix success rate (tests passing)
- False-positive rate (reviewer rejects correct fixes)
- Total "token cost" (simulated or measured)
- Number of rounds to convergence

**What can be tested in-sandbox:**
- The harness, sample codebase, and scoring logic can all run locally.
- Without real LLM API keys, fixes are simulated with a mix of correct and
  incorrect patches to measure the pipeline's value-add from review.

**What requires real models:**
- Actual LLM-generated fixes and reviews (protocol provided for Gwaihir to
  run later).
