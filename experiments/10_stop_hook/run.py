#!/usr/bin/env python3
"""
Experiment 10: Stop Hook — Block "Done" Until Checks Pass
===========================================================

Runs the sample codebase test suite as a stop hook to gate agent completion.
Observes gating of two finite fixtures; reopening frequency is not measured.

REAL EXECUTION — actually runs pytest against buggy and fixed code.
"""
import json
import os
import sys
import subprocess
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

SAMPLE_DIR = Path(__file__).parent.parent / "sample_codebase"


def run_checks(codebase_file: str) -> dict:
    """Run pytest against a version of mathlib and capture results."""
    import shutil
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copy(SAMPLE_DIR / "test_mathlib.py", tmpdir)
        shutil.copy(SAMPLE_DIR / codebase_file, os.path.join(tmpdir, "mathlib.py"))

        result = subprocess.run(
            [sys.executable, "-m", "pytest", "test_mathlib.py", "-v", "--tb=no",
             "--junitxml=report.xml"],
            capture_output=True, text=True, cwd=tmpdir,
        )
        output = result.stdout + result.stderr
        if result.returncode not in (0, 1):
            raise RuntimeError(f"pytest infrastructure failure (exit {result.returncode}): {output[-200:]}")
        try:
            root = ET.parse(Path(tmpdir) / "report.xml").getroot()
        except (OSError, ET.ParseError) as exc:
            raise RuntimeError(f"Invalid pytest report: {exc}; {output[-200:]}") from exc
        if root.tag not in ("testsuites", "testsuite"):
            raise RuntimeError("Invalid pytest report root")
        counts = dict(passed=0, failed=0, errors=0, skipped=0)
        for case in root.iter("testcase"):
            outcomes = [child.tag for child in case if child.tag in ("failure", "error", "skipped")]
            if len(outcomes) > 1:
                raise RuntimeError("Conflicting testcase outcomes")
            # JUnit failures are executed test failures; errors cover setup/collection.
            status = {"failure": "failed", "error": "errors", "skipped": "skipped"}.get(
                outcomes[0], "passed") if outcomes else "passed"
            counts[status] += 1
        if (counts["errors"] or counts["skipped"] or not sum(counts.values())
                or (result.returncode == 0) != (counts["failed"] == 0)):
            raise RuntimeError(f"Invalid pytest run: {counts}, exit {result.returncode}")
        return {"exit_code": result.returncode, **counts,
                "all_pass": result.returncode == 0, "output_snippet": output.strip()[-200:]}



def main():
    parser = argparse.ArgumentParser(description="Experiment 10: Stop Hook")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 10: Stop Hook — Block Done Until Checks Pass")
    print("=" * 65)
    print()

    print("Scenario A: Agent claims 'done' with BUGGY code")
    print("-" * 50)
    buggy_result = run_checks("mathlib.py")
    hook_blocked_a = not buggy_result["all_pass"]
    print(f"  Tests passed: {buggy_result['passed']}, failed: {buggy_result['failed']}")
    print(f"  Stop hook verdict: {'BLOCKED — not done' if hook_blocked_a else 'PASSED'}")
    print()

    print("Scenario B: Agent claims 'done' with FIXED code")
    print("-" * 50)
    fixed_result = run_checks("mathlib_fixed.py")
    expected = [(buggy_result, (0, 10, 0, 0, 1)), (fixed_result, (10, 0, 0, 0, 0))]
    for result, control in expected:
        actual = tuple(result[key] for key in ("passed", "failed", "errors", "skipped", "exit_code"))
        if actual != control:
            raise RuntimeError(f"Fixture control mismatch: expected {control}, got {actual}")
    hook_blocked_b = not fixed_result["all_pass"]
    print(f"  Tests passed: {fixed_result['passed']}, failed: {fixed_result['failed']}")
    print(f"  Stop hook verdict: {'BLOCKED — not done' if hook_blocked_b else 'PASSED'}")
    print()

    # Simulate partially-fixed scenarios
    print("Scenario C: Simulated partial-fix scenarios")
    print("-" * 50)
    partial_scenarios = [
        {"name": "3/10 bugs fixed", "pass_rate": 0.3},
        {"name": "7/10 bugs fixed", "pass_rate": 0.7},
        {"name": "9/10 bugs fixed", "pass_rate": 0.9},
    ]
    for scenario in partial_scenarios:
        blocked = scenario["pass_rate"] < 1.0
        print(f"  {scenario['name']}: {'BLOCKED' if blocked else 'PASSED'}")

    print()
    print("--- Scenarios A and B are REAL (pytest execution) ---")
    print("--- Scenario C is SIMULATED ---")
    print()

    print("Conclusion: The hook blocked the buggy fixture and passed the fixed fixture.")
    print("Reopening frequency was not measured; these fixtures do not establish general completion reliability.")

    summary = {
        "experiment": "10_stop_hook",
        "simulated": False,
        "buggy_scenario": {
            "tests_passed": buggy_result["passed"],
            "tests_failed": buggy_result["failed"],
            "hook_blocked": hook_blocked_a,
        },
        "fixed_scenario": {
            "tests_passed": fixed_result["passed"],
            "tests_failed": fixed_result["failed"],
            "hook_blocked": hook_blocked_b,
        },
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError) as exc:
        print(f"Experiment 10 failed: {exc}", file=sys.stderr)
        sys.exit(1)
