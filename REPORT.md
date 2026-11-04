# Agent Factory Lab — Experiment Report

> Generated from experiment runs on 2026-11-04.
> All experiments ran from a clean checkout. Each result below comes from
> the actual `results.json` produced by that experiment's `run.py`.

---

## Overview

Six research findings about coding-agent improvements were collected from X,
documented in `findings/`, and tested via runnable experiments. Three
experiments produce **real measurements** (token counts, execution times);
three use **simulated or estimated** data (Monte Carlo, cost modeling). Every
number below is labeled accordingly.

---

## Experiment 1: Writer/Reviewer Pipeline vs Single-Agent

**Finding:** A cross-model writer/reviewer/QA pipeline with isolated worktrees
and risk-gated auto-merge
([source](https://x.com/brag_sheet/status/2117474234431869338)).

**Method:** Monte Carlo simulation — 1,000 trials per bug, 10 bugs, configurable
probabilities (P(correct)=0.65, P(approve\_good)=0.95, P(catch\_bad)=0.70).

**Status: SIMULATED** (no LLM API calls)

| Metric | Single-Agent | Pipeline | Delta |
|---|---|---|---|
| Fix success rate | 64.2% | 79.2% | +15.0 pp |
| Failed fixes shipped | 3,582 | 2,084 | -42% |
| Avg tokens/attempt | 3,001 | 5,122 | +71% |
| Avg review rounds | 1 | 1.28 | — |

**Interpretation:** Under these probability assumptions, the reviewer pipeline
catches ~42% more bad fixes before they ship, at the cost of ~71% more tokens.
The net fix rate improves by 15 percentage points. These numbers are sensitive
to the probability parameters — the harness accepts `--p-correct`,
`--p-approve-good`, and `--p-catch-bad` to explore different assumptions.

**To validate with real models:** Replace `simulate_writer_fix()` and
`simulate_reviewer()` in `experiments/01_writer_reviewer/run.py` with LLM
API calls against `experiments/sample_codebase/mathlib.py`. The harness,
scoring, and reporting logic are ready.

---

## Experiment 2: Cheap vs Frontier Model Routing

**Finding:** Keep frontier models off the control plane; route orchestration
to cheap models
([source](https://x.com/adamhjk/status/2116417623789613265)).

**Method:** Cost model using public API pricing (Claude Opus vs Claude Haiku)
applied to a synthetic 17-step coding session.

**Status: ESTIMATED** (real prices, synthetic session trace)

| Metric | Value |
|---|---|
| Session steps | 17 (12 control-plane, 5 data-plane) |
| Control-plane share of input tokens | 28% |
| All-frontier cost | $1.3808 |
| Two-tier cost | $1.0924 |
| **Savings** | **$0.2884 (20.9%)** |

**Interpretation:** Even though control-plane steps are only 28% of input
tokens, routing them to Haiku ($0.25/M) instead of Opus ($15/M) saves ~21%
of the total session cost. In sessions where orchestration is a larger share
(e.g., multi-agent coordination with many status checks), savings could reach
50%+.

**Caveat:** This assumes cheap models handle routing/status tasks without
quality degradation. The experiment provides the framework; A/B testing on
real Gwaihir tasks is needed to validate.

---

## Experiment 3: Batched Script vs Per-Call Tool Use

**Finding:** Batch many tool calls into one script to slash token overhead
([source](https://x.com/MilanGlow/status/2116089358709370962)).

**Method:** Real token counting with tiktoken (cl100k\_base / GPT-4o encoding)
on 20 file operations against the sample codebase.

**Status: REAL TOKEN COUNTS**

| Metric | Per-Call | Batched | Reduction |
|---|---|---|---|
| API requests | 20 | 2 | 90% |
| Total tokens | 32,981 | 1,819 | **94.5%** |

**Interpretation:** The per-call approach re-sends the growing conversation
context with every request, causing quadratic token growth (request 1: 74
tokens → request 20: 2,151 tokens). Batching eliminates this entirely.
The 94.5% reduction aligns with the cited claim of ~312 calls/3.1M tokens
→ ~2 requests/61K tokens (a ~98% reduction; our smaller example shows a
proportionally similar pattern).

**Caveat:** This measures token overhead, not correctness. Whether models
produce reliable batch scripts (vs. iterating with feedback) is the open
question for Gwaihir/Rex to test.

---

## Experiment 4: Cached vs Uncached Prompt Cost

**Finding:** Server-side prompt caching for long sessions
([source 1](https://x.com/ClaudeDevs/status/2117332449382510884),
[source 2](https://x.com/tokenscost/status/2117638485075206393)).

**Method:** Real token counting with tiktoken, cost modeling with Anthropic's
public pricing (Sonnet-class: $3/M input, $0.30/M cached, $3.75/M cache write).

**Status: REAL TOKEN COUNTS, ESTIMATED COSTS**

| Metric | Uncached | Cached |
|---|---|---|
| Total session cost | $0.0274 | $0.0076 |
| **Savings** | — | **$0.0198 (72.3%)** |
| Cache hit rate | n/a | 92.7% |
| Break-even turn | n/a | Turn 2 |

**Interpretation:** Prompt caching saves 72% of input costs over a 20-turn
session. The cache write premium on turn 1 is recovered by turn 2. After
that, every turn benefits from ~93% of its input tokens being served from
cache at 10x discount. For Gwaihir's typically long sessions (50-100+ turns),
savings would be even larger.

**Action for Gwaihir:** Ensure the system prompt, tool definitions, and
project context are placed at the top of every request (stable prefix) and
that messages are append-only. Enable Anthropic's `cache_control` breakpoints
or rely on OpenAI's automatic prefix caching.

---

## Experiment 5: Session Layer & Pane Control

**Finding:** Native pane/tab control for Rex and herdr-core as a durable
session layer
([pane control](https://x.com/dani_avila7/status/2116352019564777669),
[herdr-core](https://x.com/herdrdev/status/2115841099575222765),
[orchestration](https://x.com/nicoritschel/status/2116931517415141724)).

**Method:** Real tmux pane management and JSON-based session checkpoint/restore.

**Status: REAL EXECUTION**

### Part A: Pane Manager

| Metric | Sequential | Parallel (tmux) |
|---|---|---|
| Avg execution time | 0.300s | 0.164s |
| **Speedup** | baseline | **1.83x** |

### Part B: Session Checkpoint/Restore

| Metric | Value |
|---|---|
| Steps completed before crash | 2 / 5 |
| State recovered on resume | Yes |
| Steps replayed after resume | 3 |
| Resume time | 0.061s |

**Interpretation:** Multi-pane execution gives a measurable speedup for
parallelizable workflows (edit + test + log check). The checkpoint/restore
system achieves zero state loss across simulated crashes. Both components
are lightweight (the pane manager is ~80 lines, the session store is ~40
lines) and ready for integration.

**To integrate:** The pane manager needs Rex's tool-calling interface; the
session store needs herdr-core's persistence API. Protocols for both are
documented in `findings/05_session_layer_pane_control.md`.

---

## Experiment 6: SuperPlane Backlog-to-Ship

**Finding:** The SuperPlane pattern — fully automated issue → ship pipeline
([source](https://x.com/darkofabijan/status/2115037955480048100)).

**Method:** State machine implementation with 5 sample issues of varying risk.

**Status: SIMULATED** (design exercise)

| Outcome | Count |
|---|---|
| Shipped (auto) | 4 |
| Escalated to human | 1 |
| Failed | 0 |

The state machine correctly routes:
- **Low-risk** (ISS-1, ISS-2): auto-approve → auto-merge → deploy.
- **Medium-risk** (ISS-3): auto-approve → human review merge → deploy.
- **High-risk with tests** (ISS-4): human approval → human merge → deploy.
- **High-risk without tests** (ISS-5): escalated immediately.

**Landroval capability gap:** 10 capabilities needed for the full pattern
(see `experiments/06_superplane/results.json` for the checklist). Landroval
currently covers code generation and test execution; the gaps are issue triage,
approval gates, deploy triggers, and metrics collection.

---

## Conclusions & Recommended Next Steps

### High-Confidence Recommendations (backed by real measurements)

1. **Adopt batched tool calling in Gwaihir and Rex.** The 94.5% token
   reduction is real and dramatic. Even if batch scripts are slightly less
   reliable than iterative calls, the token savings are so large that a
   10-20% retry rate would still be net positive.

2. **Enable prompt caching immediately.** 72% cost savings with a turn-2
   break-even point. This is essentially free money — it requires only
   structuring prompts correctly (stable prefix, append-only history).

3. **Add pane management to Rex.** The 1.83x speedup from parallel
   pane execution is modest but real, and the implementation is trivial
   (~80 lines of tmux wrapper).

### Medium-Confidence Recommendations (backed by cost models)

4. **Implement two-tier model routing in Gwaihir.** The 21% cost saving
   is conservative (our synthetic session has only 28% control-plane tokens;
   real orchestration-heavy sessions likely have more). Validate with an A/B
   test on 50 real coding tasks.

5. **Make writer/reviewer the default Gwaihir pipeline.** The simulated
   +15pp fix rate and -42% defect escape rate are compelling, but the
   probability assumptions need calibration against real model performance.
   Run the harness with real LLM calls on the sample codebase as a first
   validation step.

### Longer-Term Recommendations (design-stage)

6. **Build toward the SuperPlane pattern in Landroval.** The state machine
   and risk-gate logic are ready. The 10-item capability checklist
   provides a concrete roadmap. Start with issue triage + approval gate
   (the highest-value gaps).

7. **Integrate herdr-core session persistence into Gwaihir.** The
   checkpoint/restore prototype demonstrates zero state loss; wiring it
   into herdr-core's actual API is the next step.

---

## What Could Not Be Tested

The following require access to real LLM APIs or to herdr/Rex running on
Andrei's machine:

- **Experiment 1:** Whether real LLMs produce correct fixes at the assumed
  rates, and whether a reviewer model actually catches bugs the writer misses.
- **Experiment 2:** Whether cheap models handle routing decisions without
  quality loss on real coding tasks.
- **Experiment 3:** Whether LLMs reliably produce correct batch scripts
  (vs. needing iterative feedback).
- **Experiment 5:** Integration with Rex's tool-calling interface and
  herdr-core's session API.

Harnesses and protocols for all of these are provided and ready to run once
API keys or herdr/Rex access are available.
