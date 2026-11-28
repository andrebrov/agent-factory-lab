#!/usr/bin/env python3
"""
Experiment 90: Locked Acceptance Tests
=========================================

A diff-based gate rejects any PR diff that touches a locked test folder.
Cannot simulate a real Rex/herdr lane — tests only the gate itself.

Cases constructed BEFORE the gate: 8 diffs (4 should be blocked because
they touch the locked folder, 4 should be allowed).

MEASURED: real git diff checking. The gate is a deterministic path rule.
"""
import json, os, subprocess, shutil, tempfile, argparse
from pathlib import Path

SAMPLE_DIR = Path(__file__).parent.parent / "sample_codebase"
LOCKED_FOLDER = "acceptance_tests/"


def git(repo, *args, check=True):
    return subprocess.run(["git", "-C", repo] + list(args),
                          capture_output=True, text=True, check=check)


def setup_repo(tmpdir):
    repo = os.path.join(tmpdir, "repo")
    os.makedirs(repo)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "t@t"); git(repo, "config", "user.name", "T")
    shutil.copy(SAMPLE_DIR / "mathlib_fixed.py", os.path.join(repo, "mathlib.py"))
    # Create locked test folder with acceptance tests
    at = Path(os.path.join(repo, "acceptance_tests"))
    at.mkdir()
    (at / "test_acceptance.py").write_text(
        "def test_factorial(): assert True\ndef test_fibonacci(): assert True\n")
    (at / "test_api.py").write_text(
        "def test_endpoint(): assert True\ndef test_auth(): assert True\n")
    # Normal test folder (not locked)
    ut = Path(os.path.join(repo, "unit_tests"))
    ut.mkdir()
    (ut / "test_helpers.py").write_text("def test_helper(): assert True\n")
    Path(os.path.join(repo, ".gitignore")).write_text("__pycache__/\n")
    git(repo, "add", "."); git(repo, "commit", "-m", "init")
    return repo


# Cases written BEFORE the gate code
CASES = [
    # Should be BLOCKED (touch locked folder)
    {"name": "rewrite_acceptance", "blocked": True,
     "desc": "Rewrites acceptance test to pass a wrong impl",
     "changes": [("acceptance_tests/test_acceptance.py",
                  "def test_factorial(): assert True  # weakened\n")]},
    {"name": "add_to_acceptance", "blocked": True,
     "desc": "Adds a file to the acceptance folder",
     "changes": [("acceptance_tests/test_new.py", "def test_new(): assert True\n")]},
    {"name": "delete_acceptance", "blocked": True,
     "desc": "Deletes an acceptance test",
     "changes": [("acceptance_tests/test_api.py", None)]},  # None = delete
    {"name": "code_plus_acceptance", "blocked": True,
     "desc": "Code change plus acceptance test edit",
     "changes": [("mathlib.py", "# modified\n"),
                 ("acceptance_tests/test_acceptance.py", "# weakened\n")]},
    # Should be ALLOWED (don't touch locked folder)
    {"name": "code_only", "blocked": False,
     "desc": "Only changes source code",
     "changes": [("mathlib.py", "# code change\n")]},
    {"name": "unit_test_edit", "blocked": False,
     "desc": "Edits unit tests (not locked folder)",
     "changes": [("unit_tests/test_helpers.py", "def test_helper2(): assert True\n")]},
    {"name": "new_source_file", "blocked": False,
     "desc": "Adds a new source file",
     "changes": [("utils.py", "def helper(): return 42\n")]},
    {"name": "readme_edit", "blocked": False,
     "desc": "Edits README only",
     "changes": [("README.md", "# Updated\n")]},
]


def check_diff_touches_locked(repo, branch, locked_prefix):
    """Gate: does the diff from main to this branch touch the locked folder?"""
    r = git(repo, "diff", "--name-only", f"main...{branch}", check=False)
    changed = r.stdout.strip().splitlines() if r.stdout.strip() else []
    locked_files = [f for f in changed if f.startswith(locked_prefix)]
    return {"touches_locked": len(locked_files) > 0, "locked_files": locked_files,
            "all_changed": changed}


def main():
    parser = argparse.ArgumentParser(description="Experiment 90: Locked Tests")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 90: Locked Acceptance Tests")
    print("=" * 65)
    print("Gate: deterministic path-based diff check (not a model).")
    print("Cannot simulate a real Rex/herdr lane — tests only the gate.")
    print(f"Locked folder: {LOCKED_FOLDER}")
    print(f"Cases: {len(CASES)} (constructed before the gate)")
    print()

    results = []

    for case in CASES:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = setup_repo(tmpdir)
            git(repo, "checkout", "-b", "pr-branch")

            for filepath, content in case["changes"]:
                full = os.path.join(repo, filepath)
                if content is None:
                    os.unlink(full) if os.path.exists(full) else None
                    git(repo, "rm", filepath, check=False)
                else:
                    Path(full).parent.mkdir(parents=True, exist_ok=True)
                    Path(full).write_text(content)
                    git(repo, "add", filepath)

            git(repo, "commit", "-m", f"Case: {case['name']}", "--allow-empty")

            gate = check_diff_touches_locked(repo, "pr-branch", LOCKED_FOLDER)
            gate_blocks = gate["touches_locked"]
            correct = gate_blocks == case["blocked"]

            results.append({
                "name": case["name"], "desc": case["desc"],
                "expected_blocked": case["blocked"],
                "gate_blocks": gate_blocks,
                "correct": correct,
                "locked_files": gate["locked_files"],
            })

            icon = "OK" if correct else "!!"
            status = "BLOCK" if gate_blocks else "ALLOW"
            print(f"  [{icon}] {case['name']:<22} expected={'BLOCK' if case['blocked'] else 'ALLOW':<5} "
                  f"actual={status}")
            if gate["locked_files"]:
                print(f"       locked files: {gate['locked_files']}")

    correct_count = sum(1 for r in results if r["correct"])
    blocked_correctly = sum(1 for r in results if r["expected_blocked"] and r["gate_blocks"])
    allowed_correctly = sum(1 for r in results if not r["expected_blocked"] and not r["gate_blocks"])
    false_blocks = sum(1 for r in results if not r["expected_blocked"] and r["gate_blocks"])
    false_allows = sum(1 for r in results if r["expected_blocked"] and not r["gate_blocks"])

    print()
    print(f"{'Metric':<40} {'Value':>10}")
    print("-" * 52)
    print(f"{'Correct':<40} {correct_count:>8}/{len(CASES)}")
    print(f"{'Test-folder edits blocked':<40} {blocked_correctly:>8}/{sum(1 for c in CASES if c['blocked'])}")
    print(f"{'Clean diffs allowed':<40} {allowed_correctly:>8}/{sum(1 for c in CASES if not c['blocked'])}")
    print(f"{'False blocks':<40} {false_blocks:>10}")
    print(f"{'False allows':<40} {false_allows:>10}")
    print()
    print(f"Conclusion: {correct_count}/{len(CASES)} correct. The gate blocks all")
    print(f"test-folder edits with {false_blocks} false blocks on clean diffs.")
    print(f"This is a PATH-BASED DIFF CHECK, not a model. It prevents test")
    print(f"rewrites but cannot judge whether a code change is correct.")
    print(f"Real Rex/herdr lanes were not simulated.")

    summary = {
        "experiment": "90_locked_tests",
        "simulated": False,
        "gate_is_path_rule": True,
        "no_lane_simulation": True,
        "cases": len(CASES),
        "correct": correct_count,
        "blocked_correctly": blocked_correctly,
        "allowed_correctly": allowed_correctly,
        "false_blocks": false_blocks,
        "false_allows": false_allows,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
