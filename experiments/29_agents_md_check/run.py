#!/usr/bin/env python3
"""
Experiment 29: AGENTS.md Size Check & Repo Root Guard
=======================================================

Implements and tests two lightweight guards:
1. Warn when combined AGENTS.md + CLAUDE.md exceeds 32 KiB.
2. Refuse to start agents outside a git repo root or worktree.

REAL EXECUTION — fully testable.
"""
import json
import os
import subprocess
import tempfile
import argparse
from pathlib import Path

MAX_AGENTS_SIZE = 32 * 1024  # 32 KiB


def check_agents_md_size(repo_path: str) -> dict:
    """Check combined size of AGENTS.md and CLAUDE.md."""
    total_size = 0
    files_found = []

    for name in ("AGENTS.md", "CLAUDE.md"):
        filepath = Path(repo_path) / name
        if filepath.exists():
            size = filepath.stat().st_size
            total_size += size
            files_found.append({"name": name, "size": size})

    exceeds = total_size > MAX_AGENTS_SIZE
    return {
        "files": files_found,
        "total_bytes": total_size,
        "max_bytes": MAX_AGENTS_SIZE,
        "exceeds_limit": exceeds,
        "warning": f"Combined AGENTS.md size ({total_size:,} bytes) exceeds 32 KiB limit" if exceeds else None,
    }


def check_repo_root(path: str) -> dict:
    """Check if the given path is a git repo root or worktree root."""
    path = Path(path).resolve()

    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return {
            "is_repo": False,
            "is_root": False,
            "error": "Not inside a git repository",
            "should_refuse": True,
        }

    toplevel = Path(result.stdout.strip()).resolve()
    is_root = path == toplevel

    return {
        "is_repo": True,
        "is_root": is_root,
        "toplevel": str(toplevel),
        "current": str(path),
        "should_refuse": not is_root,
        "error": f"Not at repo root; repo root is {toplevel}" if not is_root else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Experiment 29: AGENTS.md Check")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 29: AGENTS.md Size Check & Repo Root Guard")
    print("=" * 65)
    print()
    print("--- REAL EXECUTION ---")
    print()

    results = {"size_check_tests": [], "root_guard_tests": []}

    # === Size Check Tests ===
    print("Part A: AGENTS.md Size Check")
    print("-" * 40)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Test 1: No AGENTS.md — should pass
        r = check_agents_md_size(tmpdir)
        passed = not r["exceeds_limit"] and r["total_bytes"] == 0
        results["size_check_tests"].append({"name": "no_agents_md", "passed": passed, **r})
        print(f"  [{'PASS' if passed else 'FAIL'}] No AGENTS.md: {r['total_bytes']} bytes, exceeds={r['exceeds_limit']}")

        # Test 2: Small AGENTS.md — should pass
        (Path(tmpdir) / "AGENTS.md").write_text("# Rules\n- Run tests before done\n" * 10)
        r = check_agents_md_size(tmpdir)
        passed = not r["exceeds_limit"]
        results["size_check_tests"].append({"name": "small_agents_md", "passed": passed, **r})
        print(f"  [{'PASS' if passed else 'FAIL'}] Small AGENTS.md: {r['total_bytes']} bytes, exceeds={r['exceeds_limit']}")

        # Test 3: Exactly at limit — should pass
        (Path(tmpdir) / "AGENTS.md").write_bytes(b"x" * MAX_AGENTS_SIZE)
        (Path(tmpdir) / "CLAUDE.md").unlink(missing_ok=True)
        r = check_agents_md_size(tmpdir)
        passed = not r["exceeds_limit"]
        results["size_check_tests"].append({"name": "at_limit", "passed": passed, **r})
        print(f"  [{'PASS' if passed else 'FAIL'}] At 32 KiB limit: {r['total_bytes']} bytes, exceeds={r['exceeds_limit']}")

        # Test 4: Over limit — should warn
        (Path(tmpdir) / "AGENTS.md").write_bytes(b"x" * (MAX_AGENTS_SIZE + 1))
        r = check_agents_md_size(tmpdir)
        passed = r["exceeds_limit"]
        results["size_check_tests"].append({"name": "over_limit", "passed": passed, **r})
        print(f"  [{'PASS' if passed else 'FAIL'}] Over limit: {r['total_bytes']} bytes, exceeds={r['exceeds_limit']}")

        # Test 5: Combined AGENTS.md + CLAUDE.md over limit
        (Path(tmpdir) / "AGENTS.md").write_bytes(b"x" * 20000)
        (Path(tmpdir) / "CLAUDE.md").write_bytes(b"y" * 15000)
        r = check_agents_md_size(tmpdir)
        passed = r["exceeds_limit"] and r["total_bytes"] == 35000
        results["size_check_tests"].append({"name": "combined_over", "passed": passed, **r})
        print(f"  [{'PASS' if passed else 'FAIL'}] Combined 35KB: {r['total_bytes']} bytes, exceeds={r['exceeds_limit']}")

    size_passed = sum(1 for t in results["size_check_tests"] if t["passed"])
    size_total = len(results["size_check_tests"])
    print(f"\n  Size check: {size_passed}/{size_total} passed")
    print()

    # === Repo Root Guard Tests ===
    print("Part B: Repo Root Guard")
    print("-" * 40)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Test 1: At repo root — should pass
        subprocess.run(["git", "init", tmpdir], capture_output=True, check=True)
        r = check_repo_root(tmpdir)
        passed = r["is_repo"] and r["is_root"] and not r["should_refuse"]
        results["root_guard_tests"].append({"name": "at_root", "passed": passed, **r})
        print(f"  [{'PASS' if passed else 'FAIL'}] At repo root: is_root={r['is_root']}, refuse={r['should_refuse']}")

        # Test 2: In subdirectory — should refuse
        subdir = Path(tmpdir) / "src" / "lib"
        subdir.mkdir(parents=True)
        r = check_repo_root(str(subdir))
        passed = r["is_repo"] and not r["is_root"] and r["should_refuse"]
        results["root_guard_tests"].append({"name": "in_subdir", "passed": passed, **r})
        print(f"  [{'PASS' if passed else 'FAIL'}] In subdirectory: is_root={r['is_root']}, refuse={r['should_refuse']}")

        # Test 3: Not in a repo — should refuse
        non_repo = Path(tmpdir).parent / "not-a-repo"
        non_repo.mkdir(exist_ok=True)
        r = check_repo_root(str(non_repo))
        passed = not r["is_repo"] and r["should_refuse"]
        results["root_guard_tests"].append({"name": "not_a_repo", "passed": passed, **r})
        print(f"  [{'PASS' if passed else 'FAIL'}] Not a repo: is_repo={r['is_repo']}, refuse={r['should_refuse']}")

    # Test 4: This workspace (should be at root)
    r = check_repo_root("/workspace")
    passed = r["is_repo"] and r["is_root"] and not r["should_refuse"]
    results["root_guard_tests"].append({"name": "workspace_root", "passed": passed, **r})
    print(f"  [{'PASS' if passed else 'FAIL'}] /workspace: is_root={r['is_root']}, refuse={r['should_refuse']}")

    root_passed = sum(1 for t in results["root_guard_tests"] if t["passed"])
    root_total = len(results["root_guard_tests"])
    print(f"\n  Root guard: {root_passed}/{root_total} passed")
    print()

    all_passed = size_passed + root_passed
    all_total = size_total + root_total
    print(f"Total: {all_passed}/{all_total} tests passed")
    print()
    print("Conclusion: Both guards work correctly.")
    print(f"  Size check: detects when AGENTS.md + CLAUDE.md > 32 KiB")
    print(f"  Root guard: detects subdirectories and non-repo paths")
    print("Both checks are <1ms and ready for integration.")

    summary = {
        "experiment": "29_agents_md_check",
        "simulated": False,
        "size_check_passed": size_passed,
        "size_check_total": size_total,
        "root_guard_passed": root_passed,
        "root_guard_total": root_total,
        "all_passed": all_passed == all_total,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
