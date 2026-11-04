#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=============================================="
echo "Agent Factory Lab — Running All Experiments"
echo "=============================================="
echo ""

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

echo "=============================================="
echo "All experiments complete. See results.json in"
echo "each experiment directory and REPORT.md for"
echo "the summary."
echo "=============================================="
