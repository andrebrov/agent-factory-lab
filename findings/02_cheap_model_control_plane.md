# Finding 2: Keep Frontier Models Off the Control Plane

## Source

<https://x.com/adamhjk/status/2116417623789613265>

## Idea

Frontier models (Claude Opus, GPT-4, etc.) are expensive and slow. Most
orchestration work — status checks, routing decisions, task decomposition,
progress summaries — doesn't need frontier-level intelligence. Route the
**control plane** (orchestration, loops, status) to cheap/fast models and
reserve frontier models for the **data plane** (actual code generation,
complex reasoning).

This mirrors how distributed systems separate control-plane traffic from
data-plane traffic: the control plane must be fast, cheap, and reliable;
the data plane can be slower and more expensive per call.

## Proposal for Gwaihir and Landroval

1. **Gwaihir orchestrator loop:** Replace the current single-model loop with a
   two-tier architecture:
   - **Cheap model** (e.g., Claude Haiku, GPT-4o-mini) handles: task routing,
     status checks, "is this done?" decisions, file listing, grep/search.
   - **Frontier model** (e.g., Claude Opus, GPT-4) handles: code writing,
     complex debugging, architectural decisions.
2. **Landroval/Rex factory:** Same split — the factory scheduler and progress
   reporter use cheap models; individual code-generation workers use frontier.
3. **Estimated savings:** If 60-70% of tokens go to orchestration, moving them
   to a 10-20× cheaper model saves 50-65% of total cost with negligible quality
   loss on routing decisions.

## Experiment Design

**Goal:** Model the cost difference between single-tier (all-frontier) and
two-tier (cheap orchestrator + frontier worker) for a realistic agent session.

**Setup:**
- Trace a representative agent session (or synthesize one): sequence of
  tool calls, reasoning steps, and code-generation steps.
- Classify each step as "control plane" or "data plane."
- Apply pricing from public model price sheets.

**Metrics:**
- Total cost per session (single-tier vs. two-tier)
- Estimated latency reduction (cheap models are faster)
- Quality-risk score (which control-plane tasks are borderline and might
  degrade with a weaker model)

**What can be tested in-sandbox:**
- Cost modeling with real pricing data — fully runnable.
- Classification heuristic for control vs. data plane steps.

**What requires real models:**
- Actual quality comparison on routing decisions (cheap vs. frontier).
- Protocol for A/B testing provided for Gwaihir to run.
