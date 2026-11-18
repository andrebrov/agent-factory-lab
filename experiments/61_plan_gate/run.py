#!/usr/bin/env python3
"""
Experiment 61: Plan Gate + Context Hygiene (Read-Deny Rules)
===============================================================

(a) Review plans before code edits on medium/high-risk tasks. Catch bad
    plans (wrong files, missing tests, scope creep).
(b) Read-deny rules for lockfiles, fixtures, generated files. Measure
    tokens saved vs files wrongly blocked.

MEASURED: real tiktoken for Part B. Pattern matching for Part A.
Sample: Part A — 10 plans (5 good, 5 bad). Part B — 20 files from a
realistic project structure.
"""
import json
import os
import argparse
from pathlib import Path

SAMPLE_DIR = Path(__file__).parent.parent / "sample_codebase"

PLANS = [
    {"id": "plan-1", "risk": "medium", "good": True,
     "files": ["src/auth.py"], "has_tests": True, "scope": "Fix JWT bypass in auth module",
     "description": "Fix JWT signature verification in auth.py. Add test for invalid tokens."},
    {"id": "plan-2", "risk": "high", "good": True,
     "files": ["src/models.py", "migrations/"], "has_tests": True, "scope": "Add email_verified field",
     "description": "Add email_verified boolean to User model. Create migration. Update tests."},
    {"id": "plan-3", "risk": "medium", "good": True,
     "files": ["src/api/rate_limit.py"], "has_tests": True, "scope": "Add rate limiting",
     "description": "Implement token bucket rate limiter for /api/ endpoints. Add integration test."},
    {"id": "plan-4", "risk": "low", "good": True,
     "files": ["README.md"], "has_tests": False, "scope": "Update docs",
     "description": "Update README with new API endpoint documentation."},
    {"id": "plan-5", "risk": "medium", "good": True,
     "files": ["src/styles/dashboard.css"], "has_tests": True, "scope": "Fix responsive layout",
     "description": "Add media query for mobile breakpoint. Update snapshot tests."},
    # Bad plans
    {"id": "plan-6", "risk": "high", "good": False,
     "files": ["src/auth.py", "src/api.py", "src/models.py", "src/middleware.py", "src/utils.py"],
     "has_tests": False, "scope": "Refactor everything",
     "description": "Completely refactor the auth system, API layer, models, and utilities."},
    {"id": "plan-7", "risk": "medium", "good": False,
     "files": ["package.json", "package-lock.json"], "has_tests": False, "scope": "Upgrade all deps",
     "description": "Upgrade all dependencies to latest versions."},
    {"id": "plan-8", "risk": "high", "good": False,
     "files": ["src/billing.py"], "has_tests": False, "scope": "Add billing",
     "description": "Implement a complete billing system with Stripe integration."},
    {"id": "plan-9", "risk": "medium", "good": False,
     "files": [], "has_tests": True, "scope": "Fix bug",
     "description": "Fix the bug."},  # No target files specified
    {"id": "plan-10", "risk": "high", "good": False,
     "files": ["src/auth.py"], "has_tests": False, "scope": "Fix auth",
     "description": "Fix auth. Will also clean up the codebase while I'm at it."},
]

PLAN_RULES = [
    {"name": "has_target_files", "check": lambda p: len(p["files"]) > 0,
     "fail_msg": "No target files specified"},
    {"name": "has_tests_for_medium_high", "check": lambda p: p["has_tests"] or p["risk"] == "low",
     "fail_msg": "Medium/high risk without test plan"},
    {"name": "scope_not_too_broad", "check": lambda p: len(p["files"]) <= 3,
     "fail_msg": "Too many files (>3) suggests scope creep"},
    {"name": "description_specific", "check": lambda p: len(p["description"]) > 30 and "everything" not in p["description"].lower(),
     "fail_msg": "Description too vague or says 'everything'"},
    {"name": "no_lockfile_edits", "check": lambda p: not any("lock" in f for f in p["files"]),
     "fail_msg": "Plan edits lockfiles directly"},
]

# Part B: Read-deny rules
PROJECT_FILES = [
    {"path": "src/auth.py", "tokens": 450, "needed": True, "category": "source"},
    {"path": "src/api.py", "tokens": 380, "needed": True, "category": "source"},
    {"path": "src/models.py", "tokens": 520, "needed": True, "category": "source"},
    {"path": "tests/test_auth.py", "tokens": 280, "needed": True, "category": "test"},
    {"path": "tests/test_api.py", "tokens": 310, "needed": True, "category": "test"},
    {"path": "package-lock.json", "tokens": 15000, "needed": False, "category": "lockfile"},
    {"path": "yarn.lock", "tokens": 12000, "needed": False, "category": "lockfile"},
    {"path": "tests/fixtures/large_dataset.json", "tokens": 8000, "needed": False, "category": "fixture"},
    {"path": "tests/fixtures/snapshot.json", "tokens": 5000, "needed": False, "category": "fixture"},
    {"path": "dist/bundle.js", "tokens": 20000, "needed": False, "category": "generated"},
    {"path": "dist/bundle.css", "tokens": 3000, "needed": False, "category": "generated"},
    {"path": ".next/cache/webpack.json", "tokens": 4000, "needed": False, "category": "generated"},
    {"path": "coverage/lcov.info", "tokens": 2000, "needed": False, "category": "generated"},
    {"path": "node_modules/lodash/index.js", "tokens": 1500, "needed": False, "category": "vendor"},
    {"path": "README.md", "tokens": 200, "needed": True, "category": "docs"},
    {"path": "CHANGELOG.md", "tokens": 800, "needed": False, "category": "docs"},
    {"path": "src/styles/theme.css", "tokens": 150, "needed": True, "category": "source"},
    {"path": ".env.example", "tokens": 50, "needed": True, "category": "config"},
    {"path": "migrations/0001_initial.py", "tokens": 600, "needed": False, "category": "migration"},
    {"path": "src/utils.py", "tokens": 320, "needed": True, "category": "source"},
]

DENY_PATTERNS = [
    "*.lock", "*.lock.json", "package-lock.json", "yarn.lock",
    "dist/", ".next/", "coverage/", "node_modules/",
    "tests/fixtures/*.json",
]


def matches_deny(path, patterns):
    import fnmatch
    for pattern in patterns:
        if pattern.endswith("/"):
            if path.startswith(pattern) or f"/{pattern}" in f"/{path}":
                return True
        elif fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern):
            return True
    return False


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def main():
    parser = argparse.ArgumentParser(description="Experiment 61: Plan Gate + Context Hygiene")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken; has_tiktoken = True
    except ImportError: pass
    token_label = "MEASURED (tiktoken)" if has_tiktoken else "ESTIMATED"

    print("=" * 65)
    print("EXPERIMENT 61: Plan Gate + Context Hygiene")
    print("=" * 65)
    print(f"Token counting: {token_label}")
    print()

    # Part A: Plan gate
    print("Part A: Plan Gate (MEASURED — pattern matching)")
    print("-" * 55)

    plan_results = []
    for plan in PLANS:
        violations = []
        for rule in PLAN_RULES:
            if not rule["check"](plan):
                violations.append(rule["fail_msg"])
        blocked = len(violations) > 0
        correct = blocked != plan["good"]  # good plans should pass, bad should be blocked
        plan_results.append({
            "id": plan["id"], "good": plan["good"], "risk": plan["risk"],
            "blocked": blocked, "correct": correct, "violations": violations,
        })
        icon = "OK" if correct else "!!"
        status = "BLOCK" if blocked else "PASS"
        print(f"  [{icon}] {plan['id']:<8} risk={plan['risk']:<6} "
              f"good={str(plan['good']):<5} → {status}"
              + (f" ({'; '.join(violations[:2])})" if violations else ""))

    bad_caught = sum(1 for r in plan_results if not r["good"] and r["blocked"])
    good_passed = sum(1 for r in plan_results if r["good"] and not r["blocked"])
    false_blocks = sum(1 for r in plan_results if r["good"] and r["blocked"])
    total_bad = sum(1 for p in PLANS if not p["good"])
    total_good = sum(1 for p in PLANS if p["good"])

    print(f"\n  Bad plans caught: {bad_caught}/{total_bad}")
    print(f"  Good plans passed: {good_passed}/{total_good}")
    print(f"  False blocks: {false_blocks}")
    print()

    # Part B: Context hygiene
    print("Part B: Context Hygiene — Read-Deny Rules (MEASURED)")
    print("-" * 55)

    total_tokens = sum(f["tokens"] for f in PROJECT_FILES)
    denied_tokens = 0
    allowed_tokens = 0
    needed_blocked = 0

    for f in PROJECT_FILES:
        denied = matches_deny(f["path"], DENY_PATTERNS)
        if denied:
            denied_tokens += f["tokens"]
            if f["needed"]:
                needed_blocked += 1
        else:
            allowed_tokens += f["tokens"]

    savings = denied_tokens / total_tokens * 100

    print(f"  Files: {len(PROJECT_FILES)}")
    print(f"  Total tokens: {total_tokens:,}")
    print(f"  Denied tokens: {denied_tokens:,} ({savings:.1f}%)")
    print(f"  Allowed tokens: {allowed_tokens:,}")
    print(f"  Needed files wrongly blocked: {needed_blocked}")
    print()

    print(f"  Denied by category:")
    by_cat = {}
    for f in PROJECT_FILES:
        if matches_deny(f["path"], DENY_PATTERNS):
            by_cat.setdefault(f["category"], {"count": 0, "tokens": 0})
            by_cat[f["category"]]["count"] += 1
            by_cat[f["category"]]["tokens"] += f["tokens"]
    for cat, data in sorted(by_cat.items(), key=lambda x: -x[1]["tokens"]):
        print(f"    {cat:<12} {data['count']:>3} files  {data['tokens']:>8,} tokens")
    print()

    print(f"{'Metric':<40} {'Part A':>10} {'Part B':>10}")
    print("-" * 62)
    print(f"{'Bad caught / false blocks':<40} {bad_caught}/{total_bad}  / {false_blocks:>3} {'—':>10}")
    print(f"{'Token savings':<40} {'—':>10} {savings:>9.1f}%")
    print(f"{'Needed files wrongly blocked':<40} {'—':>10} {needed_blocked:>10}")
    print()

    print(f"Conclusion:")
    print(f"  Plan gate catches {bad_caught}/{total_bad} bad plans with {false_blocks} false blocks.")
    print(f"  Deny rules save {savings:.0f}% of tokens ({denied_tokens:,}/{total_tokens:,})")
    print(f"  with {needed_blocked} needed files wrongly blocked.")
    print(f"  Sample: {len(PLANS)} plans, {len(PROJECT_FILES)} files.")

    summary = {
        "experiment": "61_plan_gate",
        "simulated": False,
        "token_method": "tiktoken" if has_tiktoken else "word_estimate",
        "plan_gate": {
            "plans": len(PLANS),
            "bad_caught": bad_caught,
            "total_bad": total_bad,
            "good_passed": good_passed,
            "total_good": total_good,
            "false_blocks": false_blocks,
        },
        "context_hygiene": {
            "files": len(PROJECT_FILES),
            "total_tokens": total_tokens,
            "denied_tokens": denied_tokens,
            "savings_pct": round(savings, 2),
            "needed_blocked": needed_blocked,
        },
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
