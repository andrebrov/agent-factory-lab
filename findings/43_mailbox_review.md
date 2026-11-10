# Finding 43: File-Based Implementer/Reviewer Mailbox

## Source

- Repo: <https://github.com/infonomic/agent-coordination>
- <https://x.com/58bits/status/2119801061548732710>

## Idea

Two independent agent sessions — different harnesses, no shared process —
coordinate through a mailbox on the shared filesystem. One implements, one
reviews. They exchange handoffs (snapshots) and reviews through files.

Key protocol features:
- **Roles explicitly assigned** (never inferred): implementer or reviewer.
- **Snapshots are commit objects** — exact revision a review evaluates.
- **Approval names the snapshot** — not implicit, not carried across revisions.
- **Verification commands declared** with mutation classification (source/
  artifacts/none) — reviewer knows which commands are safe to run.
- **Timeout is not approval** — silence never releases dependent work.

The repo has 6 Python CLI tools, harness shims for Claude Code and Codex,
and unit + smoke tests. MIT license.

## Proposal for Gwaihir

1. Use the mailbox protocol between Gwaihir's builder and verifier lanes.
2. The implementer publishes snapshots at defined checkpoints.
3. The reviewer verifies against the snapshot, publishes structured findings.
4. Approval is explicit and snapshot-specific.

## Experiment Design

**What can be tested:** Reimplement the mailbox exchange, measure defect
catch rate and token cost vs single-agent self-review and vs exp 37's fresh
reviewer.

**Real execution on the sample codebase.**
