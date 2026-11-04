# Agent Factory Lab

[![GitHub Pages](https://img.shields.io/badge/docs-live-blue?logo=github)](https://andrebrov.github.io/agent-factory-lab/)

**Open research lab testing techniques to make AI coding agents faster, cheaper, and more reliable.**

Agent Factory Lab collects research findings on coding-agent optimization from X, turns each into a runnable experiment, and reports honest results — real measurements where possible, clearly labeled simulations where not. The lab targets two agents: **Gwaihir** (orchestrator for the [herdr](https://herdr.dev) multi-agent coding tool) and **Landroval** (orchestrator for the Rex coding factory).

## Headline Results

| Technique | Result | Measurement |
|---|---|---|
| **Batched tool calls** | **94.5% fewer tokens**, 90% fewer API requests | Real (tiktoken) |
| **Prompt caching** | **72.3% cost savings**, break-even at turn 2 | Real token counts |
| **Parallel pane execution** | **1.83x speedup**, zero-state-loss recovery | Real (tmux) |
| Writer/reviewer pipeline | +15pp fix rate, -42% defect escapes | Simulated (Monte Carlo) |
| Cheap model routing | 20.9% cost savings | Estimated (real prices) |
| SuperPlane backlog-to-ship | 4/5 auto-shipped, risk-gated | Simulated |

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
findings/                          Six research findings (markdown, sourced from X)
experiments/
  sample_codebase/                 10-bug Python library + test suite
  01_writer_reviewer/run.py        Monte Carlo: single-agent vs pipeline
  02_model_routing/run.py          Cost model: all-frontier vs two-tier
  03_batched_tool_calls/run.py     Token count: per-call vs batched script
  04_prompt_caching/run.py         Cost model: cached vs uncached sessions
  05_session_layer/run.py          tmux pane manager + session checkpoint
  06_superplane/run.py             Backlog-to-ship state machine
docs/                              Static site for GitHub Pages (SEO + GEO)
run_all.sh                         Run every experiment end-to-end
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
- `tiktoken` — accurate token counting (experiments 03, 04)
- `pytest` — sample codebase verification
- `tmux` — pane management (experiment 05; falls back to simulation)

## Running with Real Models

Experiments 01 and 03 include hooks to replace simulations with real LLM API calls. Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` and follow each experiment's docstring.

## License

MIT
