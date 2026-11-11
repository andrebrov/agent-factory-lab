# Agent Factory Lab

[![GitHub Pages](https://img.shields.io/badge/docs-live-blue?logo=github)](https://andrebrov.github.io/agent-factory-lab/)

**Open research lab testing techniques to make AI coding agents faster, cheaper, and more reliable.**

Agent Factory Lab collects research findings on coding-agent optimization from X, turns each into a runnable experiment, and reports honest results — real measurements where possible, clearly labeled simulations where not. The lab targets two agents: **Gwaihir** (orchestrator for the [herdr](https://herdr.dev) multi-agent coding tool) and **Landroval** (orchestrator for the Rex coding factory).

## Headline Results (46 experiments)

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
| **Bubblewrap sandbox** | **6/6 tests pass**, 3.4ms overhead | Real (bwrap) |
| **Booby-trap scanner** | **8/8 threats detected**, all critical neutralized | Real (git) |
| **Secret placeholders** | **No leaks detected in synthetic examples** to sandbox | Real |
| **Step-log resume** | **58% of fresh-run tokens represent completed steps skipped on resume**, not total crash+resume savings; retries may replay effects, requiring idempotency or deduplication | Local log, simulated crash |
| **Snapshot/restore** | Sub-50ms restore for 20MB state | Real (filesystem) |
| Per-second VM billing | 94% savings vs hourly | Estimated |
| Risk-routed sandbox | independent narrow checks only; no integrated routing or security validation | Mixed |
| **TokenEconomizer offline tests** | **643/644 pass**, claims 18-31% savings | Real tests, unverified claims |
| **Message threads payload** | **82.7% payload reduction** (latency, not cost) | Real (tiktoken) |
| **AGENTS.md check + root guard** | **9/9 tests pass** | Real |
| **Verifier-only lane** | **7/10 real accuracy**, 96% fewer bad merges | Real + simulated |
| **Repo map before reads** | **57% fewer tokens**, 0 wrong-file opens | Real (tiktoken) |
| Handoff accept gate | Eliminates silent discards, 100% wasted tokens saved | Simulated |
| Write/review router | 20-40% review cost savings | Estimated |
| **Cache-monotonic prefix linter** | **87% cost savings** (clean vs dirty prefix) | Real (tiktoken) |
| **Status notes vs re-reads** | **93% token reduction** for status polling | Real (tiktoken) |
| **Pegboard config sync** | **3 harnesses**, 0 drift, all MCP consistent | Real |
| **Session dump/restore** | State intact, 14ms restore | Real (tmux) |
| **Fresh reviewer** | 3/5 correct, **4/4 adversarial caught** | Measured (pytest) |
| **Generated handoff** | **38.7% token savings**, zero LLM calls | Measured (tiktoken) |
| **Fold-and-restore** | 38% reduction, **5/5 restorable** vs 0/5 hard | Measured (tiktoken) |
| **Eval gate (dsh-superagent)** | **96% triggers filtered** before LLM call | Measured (reimpl) |
| **Structured reports** | **70% fewer status tokens**, no LLM parsing | Measured (tiktoken) |
| **Subagent task-file spawn** | **92% fewer tokens** vs cloned history | Measured (tiktoken) |
| **Tokens/completed-task stack** | **73% savings** under failures (cache+checkpoint) | Measured (tiktoken) |
| **Mailbox review** | **5/5 adversarial caught**, 92% fewer tokens than self-review | Measured (pytest+tiktoken) |
| **Pane input guard** | **100% → 0% clobber rate**, 4.7ms overhead | Measured (tmux) |
| **Blocking-only reviewer** | **5/5 adversarial, 78% fewer comments**, 0 style nits | Measured (pytest) |
| **Discovery token levers** | **89% savings** (quiet+trim+summary), diff guard catches injection | Measured (tiktoken+git) |

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
findings/                          46 research findings (markdown, sourced from X + GitHub)
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
  18_firecracker_microvm/          microVM cost model (estimated)
  19_agents_sandbox/               Host-held secret placeholders (real)
  20_isolation_tiers/              Bubblewrap OS sandbox (real)
  21_booby_trap_scanner/           Repo threat scanner + neutralizer (real)
  22_lizard_microvm/               Per-second billing model (estimated)
  23_snapshot_restore/             Filesystem checkpoint timing (real)
  24_forgerun_local/               Local microVM architecture (protocol)
  25_durable_harness/              Local step-log resume (simulated crash and costs)
  26_risk_routed_sandbox/          Independent sandbox component checks (mixed)
  27_token_economizer/             Offline test suite + cost model (mixed)
  28_message_threads/              Payload reduction model (real tiktoken)
  29_agents_md_check/              Size check + repo root guard (real)
  30_verifier_only_lane/           Builder+verifier separation (real + simulated)
  31_repo_map/                     Repo map token savings (real tiktoken)
  32_handoff_accept/               Handoff accept gate (simulated)
  33_write_review_router/          Review routing cost model (estimated)
  34_cache_monotonic/              Prefix linter + cache impact (real)
  35_status_notes/                 Status notes vs transcript re-reads (real)
  36_session_migrate/              tmux dump/restore + Pegboard config (real)
  37_fresh_reviewer/               Spec-based review with bug reproduction (measured)
  38_generated_handoff/            Git-log handoff + stale-TODO scanner (measured)
  39_fold_restore/                 Fold-and-restore vs hard compaction (measured)
  40_superagent_eval_gate/         Eval gate + structured reports (measured)
  41_subagent_spawn/               Task-file spawn vs cloned history (measured)
  42_tokens_per_task/              Efficiency stack with cache + checkpoint (measured)
  43_mailbox_review/               Implementer/reviewer mailbox protocol (measured)
  44_pane_guard/                   Pane input guard — don't clobber human (measured)
  45_blocking_reviewer/            Blocking-only reviewer + eval-first (measured)
  46_discovery_tokens/             Quiet flags + trim + summaries + diff guard (measured)
docs/                              Static site for GitHub Pages (SEO + GEO)
run_all.sh                         Run all 46 experiments end-to-end
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
