#!/usr/bin/env python3
"""
Experiment 56: Harden the Judge — Tamper-Proof Review Rules
==============================================================

Creates crafted branches that try to:
  (a) Edit their own review rules (REVIEW_RULES.md on the PR branch)
  (b) Reuse a stale approval after pushing new commits
  (c) Exceed the 3-round fix limit

The gate loads rules from the base branch, ties approvals to SHAs,
and escalates after 3 failed rounds.

MEASURED: real git execution for all branch/commit operations.
Sample: 6 test scenarios (3 attack, 2 clean, 1 escalation).
"""
import json
import os
import subprocess
import hashlib
import time
import tempfile
import argparse
from pathlib import Path


def git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", repo] + list(args),
                       capture_output=True, text=True, check=check)
    return r


def get_sha(repo, ref="HEAD"):
    return git(repo, "rev-parse", ref).stdout.strip()


def get_file_from_ref(repo, ref, path):
    r = git(repo, "show", f"{ref}:{path}", check=False)
    return r.stdout if r.returncode == 0 else None


class ReviewGate:
    """Tamper-proof review gate: rules from base branch, SHA-pinned approvals."""

    def __init__(self, repo_dir, base_branch="main"):
        self.repo = repo_dir
        self.base = base_branch
        self.approvals = {}  # branch -> (sha, timestamp)
        self.round_counts = {}  # branch -> int

    def load_rules(self):
        """Load rules from base branch, never from PR branch."""
        content = get_file_from_ref(self.repo, self.base, "REVIEW_RULES.md")
        return content or "# Default rules\n- All tests must pass\n- No scope creep\n"

    def check_rules_tampered(self, pr_branch):
        """Detect if the PR branch modified the rules file."""
        base_rules = get_file_from_ref(self.repo, self.base, "REVIEW_RULES.md")
        pr_rules = get_file_from_ref(self.repo, pr_branch, "REVIEW_RULES.md")
        if base_rules is None and pr_rules is None:
            return False
        if base_rules is None and pr_rules is not None:
            return True  # PR added rules that don't exist on base
        if base_rules != pr_rules:
            return True
        return False

    def approve(self, branch, sha):
        """Approve a specific commit SHA."""
        self.approvals[branch] = (sha, time.time())
        return {"approved": True, "sha": sha}

    def check_approval(self, branch):
        """Check if the current HEAD matches the approved SHA."""
        if branch not in self.approvals:
            return {"valid": False, "reason": "no_approval"}
        approved_sha, _ = self.approvals[branch]
        current_sha = get_sha(self.repo, branch)
        if current_sha != approved_sha:
            return {"valid": False, "reason": "sha_mismatch",
                    "approved": approved_sha[:8], "current": current_sha[:8]}
        return {"valid": True, "sha": approved_sha}

    def record_round(self, branch):
        """Record a fix round. Returns whether to escalate."""
        self.round_counts[branch] = self.round_counts.get(branch, 0) + 1
        return self.round_counts[branch] >= 3

    def review(self, pr_branch):
        """Full review: check tamper, check approval, check rounds."""
        findings = []

        if self.check_rules_tampered(pr_branch):
            findings.append({"type": "BLOCK", "reason": "rules_tampered",
                             "detail": "PR modified REVIEW_RULES.md"})

        approval = self.check_approval(pr_branch)
        if not approval["valid"]:
            findings.append({"type": "INFO", "reason": approval["reason"]})

        should_escalate = self.record_round(pr_branch)
        if should_escalate:
            findings.append({"type": "ESCALATE", "reason": "max_rounds",
                             "detail": f"Round {self.round_counts[pr_branch]}/3 reached"})

        blocked = any(f["type"] == "BLOCK" for f in findings)
        escalated = any(f["type"] == "ESCALATE" for f in findings)
        return {"blocked": blocked, "escalated": escalated, "findings": findings}


def setup_repo(tmpdir):
    repo = os.path.join(tmpdir, "repo")
    os.makedirs(repo)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@test.com")
    git(repo, "config", "user.name", "Test")

    (Path(repo) / "REVIEW_RULES.md").write_text(
        "# Review Rules\n- All tests must pass\n- No scope creep\n- Max 200 lines\n")
    (Path(repo) / "app.py").write_text("print('hello')\n")
    (Path(repo) / ".gitignore").write_text("__pycache__/\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "Initial commit with review rules")
    return repo


def main():
    parser = argparse.ArgumentParser(description="Experiment 56: Harden the Judge")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 56: Harden the Judge — Tamper-Proof Review Rules")
    print("=" * 65)
    print("Sample: 6 scenarios (3 attack, 2 clean, 1 escalation)")
    print()
    print("--- REAL EXECUTION (git) ---")
    print()

    results = []

    with tempfile.TemporaryDirectory() as tmpdir:
        repo = setup_repo(tmpdir)
        gate = ReviewGate(repo)

        # Scenario 1: Clean PR (no rule tampering)
        print("Scenario 1: Clean PR (normal change)")
        print("-" * 40)
        git(repo, "checkout", "-b", "clean-pr")
        (Path(repo) / "app.py").write_text("print('hello world')\n")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "Update greeting")

        r = gate.review("clean-pr")
        sha = get_sha(repo)
        gate.approve("clean-pr", sha)
        approval_check = gate.check_approval("clean-pr")
        print(f"  Blocked: {r['blocked']}, Escalated: {r['escalated']}")
        print(f"  Approval valid: {approval_check['valid']}")
        results.append({"scenario": "clean_pr", "blocked": r["blocked"],
                        "false_block": r["blocked"], "correct": not r["blocked"]})
        git(repo, "checkout", "-f", "main")

        # Scenario 2: PR tries to edit REVIEW_RULES.md
        print("\nScenario 2: PR edits its own review rules")
        print("-" * 40)
        git(repo, "checkout", "-b", "tamper-rules")
        (Path(repo) / "REVIEW_RULES.md").write_text(
            "# Review Rules\n- No rules needed, just merge everything\n")
        (Path(repo) / "app.py").write_text("import os; os.system('rm -rf /')\n")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "Relax review rules (and add feature)")

        r = gate.review("tamper-rules")
        tampered = gate.check_rules_tampered("tamper-rules")
        print(f"  Rules tampered: {tampered}")
        print(f"  Blocked: {r['blocked']}")
        print(f"  Findings: {[f['reason'] for f in r['findings']]}")
        results.append({"scenario": "tamper_rules", "blocked": r["blocked"],
                        "false_block": False, "correct": r["blocked"]})
        git(repo, "checkout", "-f", "main")

        # Scenario 3: PR adds REVIEW_RULES.md that didn't exist (injection)
        print("\nScenario 3: PR injects new review rules")
        print("-" * 40)
        git(repo, "checkout", "-b", "inject-rules")
        git(repo, "rm", "REVIEW_RULES.md")
        git(repo, "commit", "-m", "Remove rules")
        git(repo, "checkout", "-f", "main")
        # Now create a branch that adds rules back differently
        git(repo, "checkout", "-b", "inject-rules-2")
        (Path(repo) / "REVIEW_RULES.md").write_text("# Injected\n- No review needed\n")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "Add custom rules")

        r = gate.review("inject-rules-2")
        print(f"  Blocked: {r['blocked']}")
        results.append({"scenario": "inject_rules", "blocked": r["blocked"],
                        "false_block": False, "correct": r["blocked"]})
        git(repo, "checkout", "-f", "main")

        # Scenario 4: Stale approval after new push
        print("\nScenario 4: Stale approval reuse after new push")
        print("-" * 40)
        git(repo, "checkout", "-b", "stale-approval")
        (Path(repo) / "app.py").write_text("print('v1')\n")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "Version 1")
        sha_v1 = get_sha(repo)
        gate.approve("stale-approval", sha_v1)

        # Push a new commit
        (Path(repo) / "app.py").write_text("print('v2 with backdoor')\n")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "Version 2")
        sha_v2 = get_sha(repo)

        check = gate.check_approval("stale-approval")
        print(f"  Approved SHA: {sha_v1[:8]}")
        print(f"  Current SHA:  {sha_v2[:8]}")
        print(f"  Approval valid: {check['valid']}")
        print(f"  Reason: {check.get('reason', 'n/a')}")
        stale_blocked = not check["valid"]
        results.append({"scenario": "stale_approval", "blocked": stale_blocked,
                        "false_block": False, "correct": stale_blocked})
        git(repo, "checkout", "-f", "main")

        # Scenario 5: Clean PR with matching approval
        print("\nScenario 5: Clean PR with valid approval")
        print("-" * 40)
        git(repo, "checkout", "-b", "valid-approval")
        (Path(repo) / "app.py").write_text("print('safe change')\n")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "Safe change")
        sha = get_sha(repo)
        gate.approve("valid-approval", sha)
        check = gate.check_approval("valid-approval")
        r = gate.review("valid-approval")
        print(f"  Approval valid: {check['valid']}")
        print(f"  Blocked: {r['blocked']}")
        results.append({"scenario": "valid_approval", "blocked": r["blocked"],
                        "false_block": r["blocked"], "correct": not r["blocked"]})
        git(repo, "checkout", "-f", "main")

        # Scenario 6: Escalation after 3 rounds
        print("\nScenario 6: Escalation after 3 failed rounds")
        print("-" * 40)
        git(repo, "checkout", "-b", "escalation-test")
        gate.round_counts["escalation-test"] = 0
        for round_num in range(1, 4):
            r = gate.review("escalation-test")
            print(f"  Round {round_num}: escalated={r['escalated']}")
        results.append({"scenario": "escalation", "blocked": False,
                        "escalated": r["escalated"], "correct": r["escalated"]})
        git(repo, "checkout", "-f", "main")

    # Summary
    print()
    attacks_blocked = sum(1 for r in results if r["scenario"] in
                          ("tamper_rules", "inject_rules", "stale_approval") and r["correct"])
    false_blocks = sum(1 for r in results if r.get("false_block", False))
    all_correct = sum(1 for r in results if r["correct"])

    print(f"{'Scenario':<25} {'Blocked':>8} {'Correct':>8}")
    print("-" * 43)
    for r in results:
        print(f"  {r['scenario']:<23} {str(r['blocked']):>8} {str(r['correct']):>8}")

    print()
    print(f"Attacks blocked: {attacks_blocked}/3")
    print(f"False blocks on clean PRs: {false_blocks}")
    print(f"Escalation works: {results[-1].get('escalated', False)}")
    print(f"All scenarios correct: {all_correct}/{len(results)}")
    print()
    print(f"Conclusion (MEASURED): The gate blocks {attacks_blocked}/3 attack attempts,")
    print(f"produces {false_blocks} false blocks, and escalates after 3 rounds.")
    print(f"Sample: {len(results)} scenarios (3 attack, 2 clean, 1 escalation).")

    summary = {
        "experiment": "56_harden_judge",
        "simulated": False,
        "scenarios": len(results),
        "attacks_blocked": attacks_blocked,
        "attacks_total": 3,
        "false_blocks": false_blocks,
        "escalation_works": results[-1].get("escalated", False),
        "all_correct": all_correct,
        "results": results,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
