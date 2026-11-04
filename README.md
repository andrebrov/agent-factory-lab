# Agent Factory Lab

Research lab for improvements to Andrei's coding agents:
**Gwaihir** (orchestrator for the herdr multi-agent coding tool) and
**Landroval** (orchestrator for the Rex coding factory).

Findings are collected from X, stored as structured markdown, and each one
has a runnable experiment that tests (or models) the idea as far as possible
in an isolated sandbox.

## Structure

```
findings/                           # One markdown file per research finding
  01_writer_reviewer_pipeline.md
  02_cheap_model_control_plane.md
  03_batched_tool_calls.md
  04_prompt_caching.md
  05_session_layer_pane_control.md
  06_superplane_backlog_to_ship.md

experiments/                        # One directory per experiment
  sample_codebase/                  #   Shared: 10-bug Python library + tests
    mathlib.py                      #     Buggy version (10 seeded bugs)
    mathlib_fixed.py                #     Corrected reference
    test_mathlib.py                 #     Tests (all fail on buggy, all pass on fixed)
  01_writer_reviewer/run.py         #   Monte Carlo: single-agent vs pipeline
  02_model_routing/run.py           #   Cost model: all-frontier vs two-tier
  03_batched_tool_calls/run.py      #   Token count: per-call vs batched script
  04_prompt_caching/run.py          #   Cost model: cached vs uncached sessions
  05_session_layer/run.py           #   tmux pane manager + session checkpoint
  06_superplane/run.py              #   Backlog-to-ship state machine

run_all.sh                          # Runs every experiment end-to-end
REPORT.md                           # Summary of results and recommendations
```

## Quick Start

```bash
# From a clean checkout:
pip install tiktoken pytest    # optional but recommended
bash run_all.sh
```

Each experiment writes a `results.json` in its directory and prints a
human-readable summary to stdout. See `REPORT.md` for the consolidated
analysis.

## What's Real vs. Simulated

| Experiment | Measurement Method | Real or Simulated |
|---|---|---|
| 01 Writer/Reviewer | Monte Carlo with configurable probabilities | Simulated (no LLM calls) |
| 02 Model Routing | Public pricing × synthetic session trace | Estimated (real prices, synthetic trace) |
| 03 Batched Tool Calls | tiktoken token counting on actual files | **Real token counts** |
| 04 Prompt Caching | tiktoken + public pricing for a 20-turn session | **Real token counts**, estimated costs |
| 05 Session Layer | tmux pane management + JSON checkpoint/restore | **Real execution** |
| 06 SuperPlane | State machine simulation | Simulated |

## Running with Real Models

Experiments 01 and 03 include documented hooks for replacing the simulation
layer with actual LLM API calls. Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
and follow the instructions in each experiment's docstring.

## Dependencies

- Python 3.10+
- `tiktoken` (for accurate token counting in experiments 03 and 04)
- `pytest` (for verifying the sample codebase)
- `tmux` (for experiment 05 pane management; falls back to simulation)
