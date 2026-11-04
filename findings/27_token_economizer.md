# Finding 27: TokenEconomizer — Experience-Driven Black-Box Cost Control

## Source

<https://x.com/mehdizare/status/2117966977851335108>

## Paper & Repo

- Paper: [arXiv:2610.22732](https://arxiv.org/abs/2610.22732) (Microsoft Research + UC Berkeley)
- Repo: <https://github.com/microsoft/TokenEconomizer>
- Project page: <https://tokeneconomizer.github.io/>

## Idea

TokenEconomizer is an external controller that makes coding agents cheaper
without changing the agent or model. It learns from past sessions in a
repository and applies three mechanisms to future sessions:

1. **Micro-skills:** Remember operational facts about the repo (e.g., the
   right build command, where tests live, which env vars are needed).
2. **Tool pruning:** Remove tools the agent never uses in this repo.
3. **Loop guard:** Detect and interrupt unproductive failure loops.

Paper claims on SWE-Bench (277 tasks, 6 repos, 5 agent-model combos):
- 18.4–30.9% lower mean cache-aware cost
- Pass@1 up in 4 of 5 settings
- Cheaper in all 30 repo × setting cells

Also works on Web-Bench (16–21% savings) and security benchmarks (6–20%).

## Proposal for Gwaihir / Landroval

1. Install TokenEconomizer as a plugin for the agent runtime.
2. Let it accumulate micro-skills per repository across sessions.
3. Monitor Pass@1 to verify quality is maintained.

## Experiment Design

**What was tested in-sandbox:**
- Cloned the repo, ran the offline test suite (643 passed, 1 failed, 15
  skipped in 8.4s). The one failure is an environment-specific CLI detection
  issue (detects "cursor" instead of "codex" in this VM's environment).
- Inspected the three mechanisms (micro-skills, tool pruning, loop guard) and
  the pricing model.

**What cannot be tested without additional infrastructure:**
- The SWE-Bench experiments require Docker, ~200 GB disk for container images,
  and API keys for Anthropic and OpenAI.
- The paper's cost claims are unverified by us; we can confirm the code exists
  and its offline tests pass.
