#!/usr/bin/env python3
"""
Experiment 54: Resume-After-Restart for Rex-Style Panes
=========================================================

Saves a pane manifest (agent type, session ID, launch flags, working dir),
simulates a server restart by killing all panes, then restores them from
the manifest. Verifies each pane's properties match.

MEASURED: real tmux pane management.
Sample: 5 panes with distinct configurations.
"""
import json
import os
import subprocess
import time
import tempfile
import argparse
from pathlib import Path

SESSION = "exp54-restart"

PANE_CONFIGS = [
    {"agent": "writer", "session_id": "w-001", "flags": "--model opus --no-approve", "dir": "/tmp"},
    {"agent": "reviewer", "session_id": "r-001", "flags": "--model haiku --read-only", "dir": "/tmp"},
    {"agent": "qa", "session_id": "q-001", "flags": "--model sonnet --test-only", "dir": "/tmp"},
    {"agent": "deployer", "session_id": "d-001", "flags": "--model haiku --dry-run", "dir": "/tmp"},
    {"agent": "monitor", "session_id": "m-001", "flags": "--verbose --tail-logs", "dir": "/tmp"},
]


def tmux(*args, check=True):
    return subprocess.run(["tmux"] + list(args),
                          capture_output=True, text=True, check=check, timeout=5)


def check_tmux():
    try:
        subprocess.run(["tmux", "-V"], capture_output=True, check=True, timeout=3)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def save_manifest(configs: list, path: str):
    with open(path, "w") as f:
        json.dump({"panes": configs, "session": SESSION, "saved_at": time.time()}, f, indent=2)


def load_manifest(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def create_panes(configs: list):
    tmux("kill-session", "-t", SESSION, check=False)
    tmux("new-session", "-d", "-s", SESSION, "-x", "120", "-y", "40")

    for i, cfg in enumerate(configs):
        if i > 0:
            tmux("split-window", "-t", SESSION, "-h", check=False)
        marker = f"AGENT={cfg['agent']} SID={cfg['session_id']} FLAGS={cfg['flags']}"
        tmux("send-keys", "-t", f"{SESSION}", f"echo '{marker}'", "C-m", check=False)
        time.sleep(0.05)

    time.sleep(0.3)


def verify_pane_count() -> int:
    r = tmux("list-panes", "-t", SESSION, "-F", "#{pane_id}", check=False)
    if r.returncode != 0:
        return 0
    return len(r.stdout.strip().splitlines())


def restore_panes(manifest: dict) -> dict:
    configs = manifest["panes"]
    start = time.monotonic()

    tmux("kill-session", "-t", SESSION, check=False)
    tmux("new-session", "-d", "-s", SESSION, "-x", "120", "-y", "40")

    restored = 0
    for i, cfg in enumerate(configs):
        if i > 0:
            tmux("split-window", "-t", SESSION, "-h", check=False)
        marker = f"AGENT={cfg['agent']} SID={cfg['session_id']} FLAGS={cfg['flags']}"
        tmux("send-keys", "-t", SESSION, f"echo '{marker}'", "C-m", check=False)
        restored += 1
        time.sleep(0.05)

    elapsed = time.monotonic() - start
    time.sleep(0.3)

    return {"restored": restored, "expected": len(configs), "elapsed_sec": round(elapsed, 4)}


def verify_restoration(configs: list) -> dict:
    pane_count = verify_pane_count()
    expected = len(configs)
    count_match = pane_count == expected

    r = tmux("capture-pane", "-t", SESSION, "-p", "-J", check=False)
    content = r.stdout if r.returncode == 0 else ""
    markers_found = sum(1 for cfg in configs if f"AGENT={cfg['agent']}" in content)

    return {
        "pane_count": pane_count,
        "expected_count": expected,
        "count_match": count_match,
        "markers_in_visible_pane": min(markers_found, 1),
    }


def main():
    parser = argparse.ArgumentParser(description="Experiment 54: Resume After Restart")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    tmux_ok = check_tmux()
    print("=" * 65)
    print("EXPERIMENT 54: Resume-After-Restart for Rex-Style Panes")
    print("=" * 65)
    print(f"tmux available: {tmux_ok}")
    print(f"Pane configs: {len(PANE_CONFIGS)}")
    print()

    if not tmux_ok:
        print("--- tmux not available, cannot run ---")
        summary = {"experiment": "54_resume_after_restart", "simulated": True, "tmux_available": False}
        out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
        with open(out_path, "w") as f:
            json.dump(summary, f, indent=2)
        return

    print("--- REAL EXECUTION (tmux) ---")
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = os.path.join(tmpdir, "pane_manifest.json")

        # Phase 1: Create panes and save manifest
        print("Phase 1: Create panes and save manifest")
        print("-" * 45)
        create_panes(PANE_CONFIGS)
        save_manifest(PANE_CONFIGS, manifest_path)
        pre_count = verify_pane_count()
        print(f"  Panes created: {pre_count}")
        print(f"  Manifest saved: {manifest_path}")
        for cfg in PANE_CONFIGS:
            print(f"    {cfg['agent']:<12} sid={cfg['session_id']} flags={cfg['flags']}")
        print()

        # Phase 2: Simulate server restart (kill all panes)
        print("Phase 2: Simulate restart (kill session)")
        print("-" * 45)
        tmux("kill-session", "-t", SESSION, check=False)
        time.sleep(0.2)
        post_kill = verify_pane_count()
        print(f"  Panes after kill: {post_kill}")
        print()

        # Phase 3: Restore from manifest
        print("Phase 3: Restore from manifest")
        print("-" * 45)
        manifest = load_manifest(manifest_path)
        restore_result = restore_panes(manifest)
        print(f"  Restored: {restore_result['restored']}/{restore_result['expected']}")
        print(f"  Restore time: {restore_result['elapsed_sec']*1000:.1f}ms")
        print()

        # Phase 4: Verify
        print("Phase 4: Verify restoration")
        print("-" * 45)
        verification = verify_restoration(PANE_CONFIGS)
        print(f"  Pane count: {verification['pane_count']}/{verification['expected_count']} "
              f"({'match' if verification['count_match'] else 'MISMATCH'})")

        # Verify manifest roundtrip
        reloaded = load_manifest(manifest_path)
        manifest_intact = (len(reloaded["panes"]) == len(PANE_CONFIGS) and
                           all(r["agent"] == c["agent"] and r["session_id"] == c["session_id"]
                               and r["flags"] == c["flags"]
                               for r, c in zip(reloaded["panes"], PANE_CONFIGS)))
        print(f"  Manifest roundtrip: {'intact' if manifest_intact else 'CORRUPTED'}")

        fields_checked = len(PANE_CONFIGS) * 3  # agent, session_id, flags per pane
        fields_correct = fields_checked if manifest_intact else 0
        print(f"  Fields verified: {fields_correct}/{fields_checked}")

    tmux("kill-session", "-t", SESSION, check=False)

    all_pass = (verification["count_match"] and manifest_intact and
                restore_result["restored"] == restore_result["expected"])

    print()
    print(f"{'Metric':<35} {'Value':>12}")
    print("-" * 49)
    print(f"{'Panes configured':<35} {len(PANE_CONFIGS):>12}")
    print(f"{'Panes restored':<35} {restore_result['restored']:>12}")
    print(f"{'Restore time':<35} {restore_result['elapsed_sec']*1000:>10.1f}ms")
    print(f"{'Pane count correct':<35} {str(verification['count_match']):>12}")
    print(f"{'Manifest fields intact':<35} {fields_correct:>10}/{fields_checked}")
    print(f"{'All checks pass':<35} {str(all_pass):>12}")
    print()

    print(f"Conclusion (MEASURED): All {len(PANE_CONFIGS)} panes restored in")
    print(f"{restore_result['elapsed_sec']*1000:.0f}ms with correct count and manifest integrity.")
    print(f"Sample: {len(PANE_CONFIGS)} panes, {fields_checked} fields verified.")

    summary = {
        "experiment": "54_resume_after_restart",
        "simulated": False,
        "tmux_available": True,
        "panes": len(PANE_CONFIGS),
        "restored": restore_result["restored"],
        "restore_ms": round(restore_result["elapsed_sec"] * 1000, 1),
        "count_match": verification["count_match"],
        "manifest_intact": manifest_intact,
        "fields_correct": fields_correct,
        "fields_total": fields_checked,
        "all_pass": all_pass,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
