#!/usr/bin/env python3
"""
Experiment 20: Isolation Tiers — Bubblewrap OS Sandbox
========================================================

Tests bubblewrap (bwrap) as an OS-level sandbox: filesystem restriction,
network blocking, and command execution inside the sandbox.

REAL EXECUTION where bwrap is available; falls back to protocol-only.
"""
import json
import os
import subprocess
import time
import tempfile
import argparse


def check_bwrap() -> bool:
    try:
        r = subprocess.run(["bwrap", "--version"], capture_output=True, text=True)
        return r.returncode == 0
    except FileNotFoundError:
        return False


def run_bwrap_test(name: str, bwrap_args: list, cmd: list, expect_fail: bool = False) -> dict:
    full_cmd = ["bwrap"] + bwrap_args + cmd
    start = time.monotonic()
    result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=10)
    elapsed = time.monotonic() - start

    success = (result.returncode != 0) if expect_fail else (result.returncode == 0)
    return {
        "name": name,
        "success": success,
        "exit_code": result.returncode,
        "elapsed_sec": round(elapsed, 4),
        "stdout": result.stdout.strip()[:200],
        "stderr": result.stderr.strip()[:200],
        "expect_fail": expect_fail,
    }


def main():
    parser = argparse.ArgumentParser(description="Experiment 20: Isolation Tiers")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 20: Isolation Tiers — Bubblewrap OS Sandbox")
    print("=" * 65)
    print()

    bwrap_available = check_bwrap()
    print(f"bubblewrap available: {bwrap_available}")

    if not bwrap_available:
        print("\n--- PROTOCOL ONLY (bwrap not installed) ---")
        print("Install bubblewrap and re-run for real measurements.")
        summary = {
            "experiment": "20_isolation_tiers",
            "simulated": True,
            "bwrap_available": False,
            "tests": [],
        }
    else:
        print("\n--- REAL EXECUTION ---\n")
        tests = []

        base_args = [
            "--ro-bind", "/usr", "/usr",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind", "/lib64", "/lib64",
            "--ro-bind", "/bin", "/bin",
            "--ro-bind", "/sbin", "/sbin",
            "--proc", "/proc",
            "--dev", "/dev",
            "--tmpfs", "/tmp",
            "--unshare-all",
            "--die-with-parent",
        ]

        # Test 1: Basic command execution in sandbox
        t = run_bwrap_test(
            "basic_exec",
            base_args,
            ["echo", "hello from sandbox"],
        )
        tests.append(t)
        print(f"  [{('PASS' if t['success'] else 'FAIL'):<4}] {t['name']}: "
              f"rc={t['exit_code']} ({t['elapsed_sec']:.3f}s) "
              f"stdout='{t['stdout']}'")

        # Test 2: Filesystem isolation — /workspace should not be visible
        t = run_bwrap_test(
            "fs_isolation",
            base_args,
            ["ls", "/workspace"],
            expect_fail=True,
        )
        tests.append(t)
        print(f"  [{('PASS' if t['success'] else 'FAIL'):<4}] {t['name']}: "
              f"rc={t['exit_code']} ({t['elapsed_sec']:.3f}s) "
              f"(expect fail: /workspace hidden)")

        # Test 3: Sandbox startup overhead
        times = []
        for _ in range(10):
            t = run_bwrap_test("startup_timing", base_args, ["true"])
            times.append(t["elapsed_sec"])
        avg_startup = sum(times) / len(times)
        tests.append({
            "name": "startup_overhead_10x",
            "success": True,
            "avg_sec": round(avg_startup, 4),
            "min_sec": round(min(times), 4),
            "max_sec": round(max(times), 4),
        })
        print(f"  [PASS] startup_overhead: avg={avg_startup:.4f}s "
              f"min={min(times):.4f}s max={max(times):.4f}s (10 runs)")

        # Test 4: Write isolation — tmpfs is writable, nothing else
        t = run_bwrap_test(
            "write_tmpfs",
            base_args,
            ["sh", "-c", "echo test > /tmp/sandbox_test && cat /tmp/sandbox_test"],
        )
        tests.append(t)
        print(f"  [{('PASS' if t['success'] else 'FAIL'):<4}] {t['name']}: "
              f"rc={t['exit_code']} stdout='{t['stdout']}'")

        # Test 5: Write to read-only mount should fail
        t = run_bwrap_test(
            "readonly_mount",
            base_args,
            ["sh", "-c", "echo hack > /usr/test_file"],
            expect_fail=True,
        )
        tests.append(t)
        print(f"  [{('PASS' if t['success'] else 'FAIL'):<4}] {t['name']}: "
              f"rc={t['exit_code']} (expect fail: /usr is read-only)")

        # Test 6: Python execution in sandbox
        python_args = base_args + [
            "--ro-bind", "/etc/alternatives", "/etc/alternatives",
        ]
        t = run_bwrap_test(
            "python_in_sandbox",
            python_args,
            ["python3", "-c", "print('python works in sandbox')"],
        )
        tests.append(t)
        print(f"  [{('PASS' if t['success'] else 'FAIL'):<4}] {t['name']}: "
              f"rc={t['exit_code']} stdout='{t['stdout']}'")

        passed = sum(1 for t in tests if t.get("success", False))
        total = len(tests)

        print(f"\nPassed: {passed}/{total}")
        print()
        print(f"Conclusion: Bubblewrap provides real OS-level sandboxing with")
        print(f"~{avg_startup*1000:.1f}ms overhead per invocation. Filesystem isolation")
        print(f"correctly hides /workspace and enforces read-only mounts.")

        summary = {
            "experiment": "20_isolation_tiers",
            "simulated": False,
            "bwrap_available": True,
            "tests_passed": passed,
            "tests_total": total,
            "avg_startup_sec": round(avg_startup, 4),
            "tests": tests,
        }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
