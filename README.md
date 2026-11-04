# Agent Factory Lab

[![GitHub Pages](https://img.shields.io/badge/docs-live-blue?logo=github)](https://andrebrov.github.io/agent-factory-lab/)

**Open research lab testing techniques to make AI coding agents faster, cheaper, and more reliable.**

Agent Factory Lab collects research findings on coding-agent optimization from X, turns each into a runnable experiment, and reports honest results — real measurements where possible, clearly labeled simulations where not. The lab targets two agents: **Gwaihir** (orchestrator for the [herdr](https://herdr.dev) multi-agent coding tool) and **Landroval** (orchestrator for the Rex coding factory).

## Headline Results (17 experiments)

| Technique | Result | Measurement |
|---|---|---|
| **Batched tool calls** | **94.5% fewer tokens**, 90% fewer requests | Real (tiktoken) |
| **Terse completions** | **95.7% fewer output tokens** | Real (tiktoken) |
| **Prompt caching** | **72.3% cost savings**, break-even at turn 2 | Real token counts |
| **HANDOFF.md context** | **53% fewer tokens**, 100% fact retention | Real (tiktoken) |
| **Parallel pane execution** | **1.83x speedup**, zero-state-loss | Real (tmux) |
| **Mutation check** | **100% kill rate** on 10 mutations | Real (pytest) |
| **Stop hook** | Blocks premature "done" on buggy code | Real (pytest) |
| **Remote VM sessions** | **100% survival** across 5 disconnect cycles | Real (tmux) |
| Writer/reviewer pipeline | +15pp fix rate, -42% defect escapes | Simulated |
| Agent races | 60% → 91% success at 3x cost | Simulated |
| Cheap model routing | 20.9% cost savings | Estimated |
| Bug priority gate | 18% token savings, 0 missed high-severity | Simulated |
| AGENTS.md single source | Eliminates config drift (0 vs 6.5 rule gap) | Simulated |

## Quick Start

```bash
git clone https://github.com/andrebrov/agent-factory-lab.git
cd agent-factory-lab
pip install tiktoken pytest    # recommended
bash run_all.sh
```

Each experiment writes `results.json` and prints a human-readable summary. See the [full report](https://andrebrov.github.io/agent-factory-lab/report.html) or `REPORT.md` for consolidated analysis.

## Structure

```
findings/                          17 research findings (markdown, sourced from X)
experiments/
  sample_codebase/                 10-bug Python library + test suite
  01_writer_reviewer/              Monte Carlo: single-agent vs pipeline
  02_model_routing/                Cost model: all-frontier vs two-tier
  03_batched_tool_calls/           Token count: per-call vs batched script
  04_prompt_caching/               Cost model: cached vs uncached sessions
  05_session_layer/                tmux pane manager + session checkpoint
  06_superplane/                   Backlog-to-ship state machine
  07_review_round_cap/             Capped review rounds + findings log
  08_bug_priority_gate/            Bug priority scoring and gating
  09_reviewer_scoring/             Reviewer catch/false-alarm rate
  10_stop_hook/                    Pytest-based stop hook (real execution)
  11_mutation_check/               Mutation testing (real execution)
  12_handoff_context/              HANDOFF.md vs full transcript tokens
  13_correction_to_skill/          Correction→skill extraction + pruning
  14_agents_md_pattern/            Single-source config vs duplicated
  15_stop_on_verification/         Terse vs verbose completion tokens
  16_agent_races/                  Best-of-N model racing
  17_remote_vm_sessions/           tmux session durability (real execution)
docs/                              Static site for GitHub Pages (SEO + GEO)
run_all.sh                         Run all 17 experiments end-to-end
REPORT.md                          Full experiment report with conclusions
```

## Website

The lab has a static site at **<https://andrebrov.github.io/agent-factory-lab/>** with:
- SEO meta tags, Open Graph / Twitter cards
- JSON-LD structured data (TechArticle, Dataset, FAQPage)
- FAQ page with answer-target blocks for AI search
- `sitemap.xml`, `robots.txt` (AI crawlers welcome), `llms.txt` / `llms-full.txt`

## Suggested GitHub Topics

```
ai-coding-agents  llm-optimization  token-reduction  prompt-caching
multi-agent-pipeline  coding-agent-research  herdr  gwaihir  landroval
agent-benchmarks  developer-tools
```

## Dependencies

- Python 3.10+
- `tiktoken` — accurate token counting (experiments 03, 04, 12, 15)
- `pytest` — sample codebase verification and stop hook/mutation tests (10, 11)
- `tmux` — pane management and session durability (experiments 05, 17; falls back to simulation)

## Running with Real Models

Experiments 01 and 03 include hooks to replace simulations with real LLM API calls. Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` and follow each experiment's docstring.

## License

MIT
