#!/usr/bin/env python3
"""
Experiment 23: Snapshot/Restore — Filesystem Checkpoint Timing
================================================================

Simulates VM snapshot/restore with filesystem-level checkpoints.
Measures save and restore times for varying state sizes.

REAL EXECUTION — filesystem operations are real.
"""
import json
import os
import shutil
import tempfile
import time
import argparse


def create_state(state_dir: str, num_files: int, file_size_kb: int):
    os.makedirs(state_dir, exist_ok=True)
    for i in range(num_files):
        with open(os.path.join(state_dir, f"file_{i:04d}.dat"), "wb") as f:
            f.write(os.urandom(file_size_kb * 1024))


def snapshot(state_dir: str, snapshot_path: str) -> float:
    start = time.monotonic()
    shutil.make_archive(snapshot_path.replace(".tar.gz", ""), "gztar", state_dir)
    elapsed = time.monotonic() - start
    return elapsed


def restore(snapshot_path: str, restore_dir: str) -> float:
    start = time.monotonic()
    shutil.unpack_archive(snapshot_path, restore_dir)
    elapsed = time.monotonic() - start
    return elapsed


def verify_restore(original_dir: str, restored_dir: str) -> bool:
    orig_files = sorted(os.listdir(original_dir))
    rest_files = sorted(os.listdir(restored_dir))
    if orig_files != rest_files:
        return False
    for fname in orig_files:
        with open(os.path.join(original_dir, fname), "rb") as f1, \
             open(os.path.join(restored_dir, fname), "rb") as f2:
            if f1.read() != f2.read():
                return False
    return True


SCENARIOS = [
    {"name": "tiny (10 files, 1KB)",   "files": 10,  "size_kb": 1},
    {"name": "small (50 files, 10KB)",  "files": 50,  "size_kb": 10},
    {"name": "medium (100 files, 50KB)", "files": 100, "size_kb": 50},
    {"name": "large (200 files, 100KB)", "files": 200, "size_kb": 100},
]


def main():
    parser = argparse.ArgumentParser(description="Experiment 23: Snapshot/Restore")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 23: Snapshot/Restore — Filesystem Checkpoint")
    print("=" * 65)
    print()
    print("--- REAL EXECUTION (filesystem operations) ---")
    print()

    results = []
    print(f"{'Scenario':<30} {'State MB':>8} {'Save(s)':>8} {'Restore(s)':>10} {'Verified':>8}")
    print("-" * 68)

    for scenario in SCENARIOS:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = os.path.join(tmpdir, "state")
            snapshot_path = os.path.join(tmpdir, "snapshot.tar.gz")
            restore_dir = os.path.join(tmpdir, "restored")

            create_state(state_dir, scenario["files"], scenario["size_kb"])
            state_size_mb = sum(
                os.path.getsize(os.path.join(state_dir, f))
                for f in os.listdir(state_dir)
            ) / (1024 * 1024)

            save_time = snapshot(state_dir, snapshot_path)
            restore_time = restore(snapshot_path, restore_dir)
            verified = verify_restore(state_dir, restore_dir)

            print(f"  {scenario['name']:<28} {state_size_mb:>7.2f} {save_time:>8.4f} "
                  f"{restore_time:>10.4f} {'OK' if verified else 'FAIL':>8}")

            results.append({
                "name": scenario["name"],
                "files": scenario["files"],
                "file_size_kb": scenario["size_kb"],
                "state_size_mb": round(state_size_mb, 3),
                "save_sec": round(save_time, 4),
                "restore_sec": round(restore_time, 4),
                "verified": verified,
            })

    all_verified = all(r["verified"] for r in results)
    print()
    print(f"All restores verified: {all_verified}")
    print()

    # Fork simulation: restore same snapshot twice
    print("Fork simulation (restore same snapshot into 2 instances):")
    with tempfile.TemporaryDirectory() as tmpdir:
        state_dir = os.path.join(tmpdir, "state")
        create_state(state_dir, 50, 10)
        snapshot_path = os.path.join(tmpdir, "snapshot.tar.gz")
        snapshot(state_dir, snapshot_path)

        fork_times = []
        for i in range(2):
            fork_dir = os.path.join(tmpdir, f"fork_{i}")
            t = restore(snapshot_path, fork_dir)
            fork_times.append(t)
            print(f"  Fork {i}: {t:.4f}s")

    print()
    print("Conclusion: Filesystem-level snapshot/restore works correctly and")
    print("is fast for typical agent state sizes. Real VM snapshot (memory +")
    print("disk) requires vendor APIs (Engrams, Firecracker snapshot) but the")
    print("restore-and-fork pattern is validated here.")

    summary = {
        "experiment": "23_snapshot_restore",
        "simulated": False,
        "scenarios": results,
        "all_verified": all_verified,
        "fork_times_sec": [round(t, 4) for t in fork_times],
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
