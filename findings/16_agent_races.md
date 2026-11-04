# Finding 16: Agent Races — Run 2–3 Models, Pick the Winner

## Sources

- <https://x.com/stretchcloud/status/2115937472550965267>
- <https://x.com/kinabalu/status/2117732717131391359>

## Idea

For hard tasks, run 2–3 different models in separate worktrees in parallel.
Pick the winner based on test results, code quality, or a scoring rubric.
For risky actions (destructive operations, config changes), require a
majority vote across models before proceeding.

## Proposal for Gwaihir

1. On tasks classified as "hard" (high complexity, many files, architectural
   changes), Gwaihir spawns 2–3 agents on separate worktree branches.
2. Each agent works independently on the same task.
3. A scoring function evaluates outputs: tests passing, lint score, diff
   size, code quality metrics.
4. The best result is selected and merged; losers are discarded.
5. For risky actions: require ≥2 of 3 agents to agree before executing.

## Experiment Design

**Goal:** Measure pass rate improvement and cost overhead of racing.

**What can be tested in-sandbox:** Simulate races with different success
probabilities and measure how often racing finds at least one correct
solution vs single-agent.

**What requires real models:** Running actual model races on real coding
tasks and comparing solution quality.
