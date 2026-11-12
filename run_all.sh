#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=============================================="
echo "Agent Factory Lab — Running All Experiments"
echo "=============================================="
echo ""

# Refuse before any experiment or installation if this interpreter lacks pytest.
python3 -c "import pytest" 2>/dev/null || {
    echo "pytest is required. Install it with: python3 -m pip install pytest" >&2
    exit 1
}

# Install tiktoken if not already available
python3 -c "import tiktoken" 2>/dev/null || {
    echo "Installing tiktoken..."
    pip3 install --quiet tiktoken
}

# Verify sample codebase tests fail (they should — bugs are seeded)
echo "── Verifying sample codebase (expect 10 failures) ──"
cd experiments/sample_codebase
python3 -m pytest test_mathlib.py -v --tb=line 2>&1 | tail -15 || true
echo ""

# Verify fixed version passes
echo "── Verifying fixed codebase (expect 10 passes) ──"
cp mathlib_fixed.py mathlib_fixed_check.py
python3 -c "
import importlib.util, sys
spec = importlib.util.spec_from_file_location('mathlib', 'mathlib_fixed.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
assert mod.factorial(5) == 120
assert mod.fibonacci(10) == 55
assert mod.is_prime(7) == True
assert mod.clamp(-5, 0, 10) == 0
print('All spot-checks pass on fixed version.')
"
rm -f mathlib_fixed_check.py
cd ../..
echo ""

echo "── Experiment 1: Writer/Reviewer Pipeline ──"
python3 experiments/01_writer_reviewer/run.py
echo ""

echo "── Experiment 2: Model Routing Cost ──"
python3 experiments/02_model_routing/run.py
echo ""

echo "── Experiment 3: Batched Tool Calls ──"
python3 experiments/03_batched_tool_calls/run.py
echo ""

echo "── Experiment 4: Prompt Caching ──"
python3 experiments/04_prompt_caching/run.py
echo ""

echo "── Experiment 5: Session Layer & Pane Control ──"
python3 experiments/05_session_layer/run.py
echo ""

echo "── Experiment 6: SuperPlane State Machine ──"
python3 experiments/06_superplane/run.py
echo ""

echo "── Experiment 7: Review Round Cap ──"
python3 experiments/07_review_round_cap/run.py
echo ""

echo "── Experiment 8: Bug Priority Gate ──"
python3 experiments/08_bug_priority_gate/run.py
echo ""

echo "── Experiment 9: Reviewer Scoring ──"
python3 experiments/09_reviewer_scoring/run.py
echo ""

echo "── Experiment 10: Stop Hook ──"
python3 experiments/10_stop_hook/run.py
echo ""

echo "── Experiment 11: Mutation Check ──"
python3 experiments/11_mutation_check/run.py
echo ""

echo "── Experiment 12: HANDOFF.md Context ──"
python3 experiments/12_handoff_context/run.py
echo ""

echo "── Experiment 13: Correction → Skill ──"
python3 experiments/13_correction_to_skill/run.py
echo ""

echo "── Experiment 14: AGENTS.md Pattern ──"
python3 experiments/14_agents_md_pattern/run.py
echo ""

echo "── Experiment 15: Stop on Verification ──"
python3 experiments/15_stop_on_verification/run.py
echo ""

echo "── Experiment 16: Agent Races ──"
python3 experiments/16_agent_races/run.py
echo ""

echo "── Experiment 17: Remote VM Sessions ──"
python3 experiments/17_remote_vm_sessions/run.py
echo ""

echo "── Experiment 18: Firecracker microVM Cost ──"
python3 experiments/18_firecracker_microvm/run.py
echo ""

echo "── Experiment 19: Host-Held Secrets ──"
python3 experiments/19_agents_sandbox/run.py
echo ""

echo "── Experiment 20: Isolation Tiers (Bubblewrap) ──"
python3 experiments/20_isolation_tiers/run.py
echo ""

echo "── Experiment 21: Booby-Trap Scanner ──"
python3 experiments/21_booby_trap_scanner/run.py
echo ""

echo "── Experiment 22: Lizard microVM Cost ──"
python3 experiments/22_lizard_microvm/run.py
echo ""

echo "── Experiment 23: Snapshot/Restore ──"
python3 experiments/23_snapshot_restore/run.py
echo ""

echo "── Experiment 24: forgerun Architecture ──"
python3 experiments/24_forgerun_local/run.py
echo ""

echo "── Experiment 25: Durable Harness ──"
python3 experiments/25_durable_harness/run.py
echo ""

echo "── Experiment 26: Risk-Routed Sandbox ──"
python3 experiments/26_risk_routed_sandbox/run.py
echo ""

echo "── Experiment 27: TokenEconomizer ──"
python3 experiments/27_token_economizer/run.py
echo ""

echo "── Experiment 28: Message Threads ──"
python3 experiments/28_message_threads/run.py
echo ""

echo "── Experiment 29: AGENTS.md Check ──"
python3 experiments/29_agents_md_check/run.py
echo ""

echo "── Experiment 30: Verifier-Only Lane ──"
python3 experiments/30_verifier_only_lane/run.py
echo ""

echo "── Experiment 31: Repo Map ──"
python3 experiments/31_repo_map/run.py
echo ""

echo "── Experiment 32: Handoff Accept ──"
python3 experiments/32_handoff_accept/run.py
echo ""

echo "── Experiment 33: Write/Review Router ──"
python3 experiments/33_write_review_router/run.py
echo ""

echo "── Experiment 34: Cache-Monotonic Prefix ──"
python3 experiments/34_cache_monotonic/run.py
echo ""

echo "── Experiment 35: Status Notes ──"
python3 experiments/35_status_notes/run.py
echo ""

echo "── Experiment 36: Session Migrate ──"
python3 experiments/36_session_migrate/run.py
echo ""

echo "── Experiment 37: Fresh Reviewer ──"
python3 experiments/37_fresh_reviewer/run.py
echo ""

echo "── Experiment 38: Generated Handoff ──"
python3 experiments/38_generated_handoff/run.py
echo ""

echo "── Experiment 39: Fold-and-Restore ──"
python3 experiments/39_fold_restore/run.py
echo ""

echo "── Experiment 40: Superagent Eval Gate ──"
python3 experiments/40_superagent_eval_gate/run.py
echo ""

echo "── Experiment 41: Subagent Spawn ──"
python3 experiments/41_subagent_spawn/run.py
echo ""

echo "── Experiment 42: Tokens per Task ──"
python3 experiments/42_tokens_per_task/run.py
echo ""

echo "── Experiment 43: Mailbox Review ──"
python3 experiments/43_mailbox_review/run.py
echo ""

echo "── Experiment 44: Pane Guard ──"
python3 experiments/44_pane_guard/run.py
echo ""

echo "── Experiment 45: Blocking Reviewer ──"
python3 experiments/45_blocking_reviewer/run.py
echo ""

echo "── Experiment 46: Discovery Tokens ──"
python3 experiments/46_discovery_tokens/run.py
echo ""

echo "── Experiment 47: Combined Changes Gate ──"
python3 experiments/47_combined_changes/run.py
echo ""

echo "── Experiment 48: Stale Instruction Guard ──"
python3 experiments/48_stale_instruction/run.py
echo ""

echo "── Experiment 49: MCP Tool Audit ──"
python3 experiments/49_mcp_tool_audit/run.py
echo ""

echo "=============================================="
echo "All 49 experiments complete. See results.json"
echo "in each experiment directory and REPORT.md"
echo "for the summary."
echo "=============================================="
