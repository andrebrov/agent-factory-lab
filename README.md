# Agent Factory Lab

[![GitHub Pages](https://img.shields.io/badge/docs-live-blue?logo=github)](https://andrebrov.github.io/agent-factory-lab/)

**Open research lab testing techniques to make AI coding agents faster, cheaper, and more reliable.**

Agent Factory Lab collects research findings on coding-agent optimization from X, turns each into a runnable experiment, and reports honest results — real measurements where possible, clearly labeled simulations where not. The lab targets two agents: **Gwaihir** (orchestrator for the [herdr](https://herdr.dev) multi-agent coding tool) and **Landroval** (orchestrator for the Rex coding factory).

## Headline Results (79 experiments)

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
| **Combined-changes gate** | **2 integration breaks** caught (0 per-branch), 0.25s overhead | Measured (git+pytest) |
| **Stale-instruction checker** | **100% precision/recall** on 6 planted cases | Measured (checker) + simulated (compliance) |
| **MCP tool pruning** | **53% savings** upfront, **93%** with caching over 20 turns | Measured (tiktoken) |
| **Needs-human queue** | **50% fewer messages**, 100% precision/recall on needs-human | Measured (detection) + simulated (volume) |
| **Compact dashboard** | **88% fewer tokens** vs raw scrollback for 5-agent review | Measured (tiktoken) |
| **Proof-of-done gate** | **4/4 false claims caught**, 0 false flags, 160ms overhead | Measured (pytest) |
| Cross-agent review gate | 5/5 adversarial caught, 2 false findings, +60% tokens | Measured (pytest) + modeled |
| **Resume-after-restart** | **5/5 panes, 15/15 fields**, 312ms | Measured (tmux) |
| Instruction diet | **74% token savings**, quality unknown without LLM | Measured (tiktoken) |
| **Harden the judge** | **3/3 attacks blocked**, 0 false blocks, 6/6 scenarios | Measured (git) |
| **Per-repo token controller** | **18% savings** (facts+pruning), 40% loop guard | Measured (tiktoken) |
| **Ownership gate** | **4 conflicts blocked**, 0 false blocks, 100% accuracy | Measured |
| **Status cards** | **93.3% state accuracy** (14/15), 26-line summary | Measured |
| **Handoff vs compact** | **35% savings** vs keep-going, 2pp better than compact | Measured sizes + simulated exec |
| **Watcher done-gate** | **100% accuracy** (20/20), 8/8 errors, 0 false pos, 7/7 tricky | Measured |
| **Plan gate** | **5/5 bad caught**, 5/5 good passed, 0 false blocks | Measured |
| **Read-deny rules** | **95% token savings** (70.5K/74.6K denied), 0 needed blocked | Measured (tiktoken) |
| **Untrusted repo gate** | **6/6 injections caught**, 0 false holds, 8/8 creds blocked | Measured (scanning) |
| Stable-first prompt ordering | **91% cache rate**, 82% cost savings (modeled) | Modeled (tiktoken sizes) |
| **Needs-you view** | **100% ranking** (16/16), 1 vs 16 scan for first action | Measured |
| **Agent inbox** | **7/7 surfaced**, 0 missed, blocking-first | Measured (minimal equiv) |
| Token budget per worker | **90% savings** with shared summary (5/5 facts kept) | Measured sizes + modeled |
| Branch review | **2/2 bugs, 0 false flags**, 160 tokens avg | Measured git+pytest, rule-based reviewer |
| Token policy (session+model+scouts) | 59% input, **79% cost** reduction (quality unknown) | Modeled (no LLM calls) |
| **Done-needs-test-count gate** | **8/8 incomplete caught**, 1 false reject | Measured (16 reports) |
| **Shared repo map (real reads)** | **33% savings**, lanes still read needed files | Measured (tiktoken) |
| **Idle-leak flag** | **100% accuracy** (20 turns), 69% token waste in leaks | Measured flag + modeled waste |
| Per-role tool budget | **23% fair savings** including on-demand overhead | Measured tokens, estimated overhead |
| Map + who's-working pane | **23% savings** (real reads), 3/3 overlap detection | Measured (tiktoken) |
| **Regression gate** | **12/12** (regression+file-read+escalation rules) | Measured pytest + deterministic rules |
| Compact 400K vs 967K | **52% input savings** (modeled), quality untested | Modeled |
| **Lane safety** | **12/12** (locks+credentials+status), stale detected | Measured filesystem + labeled states |
| Lead-helper plan | **17/17** rules pass, git fixture did NOT conflict | Rule-based + real git |
| **PR cost logger** | **34/34 calls** counted including 8 retries, 10 scouts | Measured on synthetic traces |
| Scout routing | **12.6% savings** (scouts→Haiku), quality untested | Modeled (public pricing) |
| Harness A/B | **COULD NOT RUN** (no Rex/herdr/Claude on VM) | Not run |

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
findings/                          79 research findings (markdown, sourced from X + GitHub)
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
  47_combined_changes/             Combined-changes gate for parallel worktrees (measured)
  48_stale_instruction/            Stale-instruction guard + checker (mixed)
  49_mcp_tool_audit/               MCP tool-loading token audit (measured)
  50_needs_human/                  Needs-human queue filter (measured + simulated)
  51_compact_dashboard/            Compact status dashboard + diff (measured)
  52_proof_of_done/                Proof-of-done gate + skill budget (measured)
  53_cross_agent_review/           Cross-agent review gate (measured + modeled)
  54_resume_after_restart/         Resume-after-restart for panes (measured)
  55_mistake_to_rule/              Mistake-to-rule + instruction diet (mixed)
  56_harden_judge/                 Tamper-proof review rules (measured)
  57_token_controller/             Per-repo facts + tool pruning (measured)
  58_ownership_cards/              Agent ownership + status cards (measured)
  59_handoff_vs_compact/           Handoff vs compact vs keep-going (measured + simulated)
  60_watcher_gate/                 Watcher pane done-gate + tab resume (measured)
  61_plan_gate/                    Plan gate + read-deny context hygiene (measured)
  62_untrusted_repo_gate/          Injection scanner + credential block (measured)
  63_cache_hit_tracking/           Cache-hit tracking + prompt ordering (modeled)
  64_needs_you_view/               Cross-machine urgency ranking (measured)
  65_agent_inbox/                  Agent inbox for human replies (measured)
  66_token_budget/                 Token budget per worker (measured + modeled)
  67_branch_review/                Whole-branch review before done (measured, rule-based)
  68_token_policy/                 Token policy for workers (modeled, no LLM)
  69_done_test_count/              Done-needs-test-count gate (measured)
  70_shared_repo_map/              Shared repo map with real file reads (measured)
  71_no_nested_waits/              Idle-leak flag + nested-bg detection (measured)
  72_role_tool_budget/             Per-role tool loading with on-demand cost (measured)
  73_map_whos_working/             Repo map + overlap detection pane (measured)
  74_regression_gate/              Regression + file-read + escalation rules (measured)
  75_cache_hygiene/                Prefix stability + compaction cost (measured + modeled)
  76_lane_safety/                  Worktree locks + credentials + status (measured)
  77_lead_helpers/                 Lead-owned helpers with file plan (rule-based + git)
  78_cost_per_pr/                  PR cost logger + scout routing (measured + modeled)
  79_harness_ab/                   Harness A/B: COULD NOT RUN (no Rex/herdr)
docs/                              Static site for GitHub Pages (SEO + GEO)
run_all.sh                         Run all 79 experiments end-to-end
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
