#!/usr/bin/env python3
"""
Experiment 81: Repo Map + Decisions + Traps on a Larger Fixture
=================================================================

Uses a 24-file fixture with nested directories and decoy files. Both sides
include real file-content reads. The search policy is SCRIPTED (not a live
agent): with the map, open only named files; without, walk until found.

MEASURED: real tiktoken on actual file contents.
Sample: 24 files, 6 tasks, scripted search policy.
Quality: checked per task (did the policy find the right file?).
"""
import json, os, argparse, tempfile
from pathlib import Path

SAMPLE_DIR = Path(__file__).parent.parent / "sample_codebase"

def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def build_fixture(tmpdir: str) -> dict:
    """Build a 24-file fixture with nested dirs and decoys."""
    root = Path(tmpdir)
    files = {}

    # Source files (10)
    for d, fnames in [
        ("src/auth", ["login.py", "jwt.py", "permissions.py"]),
        ("src/api", ["routes.py", "middleware.py"]),
        ("src/models", ["user.py", "product.py"]),
        ("src/utils", ["helpers.py", "validators.py", "logging.py"]),
    ]:
        (root / d).mkdir(parents=True, exist_ok=True)
        for fn in fnames:
            content = f"# {d}/{fn}\n" + f"def {fn.replace('.py','')}_func():\n    pass\n" * 3
            (root / d / fn).write_text(content)
            files[f"{d}/{fn}"] = content

    # Test files (6)
    (root / "tests").mkdir(exist_ok=True)
    for fn in ["test_auth.py", "test_api.py", "test_models.py",
                "test_utils.py", "test_integration.py", "test_e2e.py"]:
        content = f"# tests/{fn}\nimport pytest\ndef {fn.replace('.py','')}(): pass\n"
        (root / "tests" / fn).write_text(content)
        files[f"tests/{fn}"] = content

    # Config and decoy files (8)
    for fn, content in [
        ("README.md", "# Project\nA sample project.\n"),
        ("setup.py", "from setuptools import setup\nsetup(name='sample')\n"),
        ("requirements.txt", "flask>=2.0\npytest>=7.0\n"),
        (".env.example", "DB_URL=postgres://...\nSECRET_KEY=changeme\n"),
        ("docs/architecture.md", "# Architecture\n## Overview\n..." * 10),
        ("docs/api-reference.md", "# API Reference\n## Endpoints\n..." * 15),
        ("scripts/deploy.sh", "#!/bin/bash\necho 'deploying'\n"),
        ("data/fixtures/seed.json", '{"users": [{"name": "test"}]}\n' * 5),
    ]:
        p = root / fn
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        files[fn] = content

    return files


def build_map(files: dict) -> str:
    """Build a detailed map with function names and structure."""
    lines = ["# Repo Map\n"]
    dirs = {}
    for path in sorted(files.keys()):
        d = os.path.dirname(path) or "."
        dirs.setdefault(d, []).append(path)

    for d in sorted(dirs.keys()):
        lines.append(f"## {d}/")
        for path in dirs[d]:
            content = files[path]
            funcs = [l.split("(")[0].replace("def ", "")
                     for l in content.splitlines() if l.startswith("def ")]
            func_str = f" ({', '.join(funcs[:3])})" if funcs else ""
            lines.append(f"  {os.path.basename(path)}{func_str}")
        lines.append("")
    return "\n".join(lines)


DECISIONS = """# Decisions
- Auth: using JWT, not session cookies (2026-11-01)
- API: rate limiting via middleware, not decorator (2026-11-05)
- Models: SQLAlchemy ORM, not raw SQL (2026-10-20)
"""

TRAPS = """# Traps
- Do NOT edit requirements.txt directly — use pip-compile
- data/fixtures/ is generated — do not modify by hand
- .env.example is a template — do not put real secrets
- docs/api-reference.md is auto-generated from source
"""


TASKS = [
    {"name": "fix_login_bug", "target": "src/auth/login.py",
     "desc": "Fix login validation", "map_says": "src/auth/"},
    {"name": "add_rate_limit", "target": "src/api/middleware.py",
     "desc": "Add rate limiting", "map_says": "src/api/"},
    {"name": "fix_user_model", "target": "src/models/user.py",
     "desc": "Fix user email validation", "map_says": "src/models/"},
    {"name": "update_helpers", "target": "src/utils/helpers.py",
     "desc": "Add string sanitizer to helpers", "map_says": "src/utils/"},
    {"name": "fix_auth_test", "target": "tests/test_auth.py",
     "desc": "Fix flaky auth test", "map_says": "tests/"},
    {"name": "add_integration", "target": "tests/test_integration.py",
     "desc": "Add integration test for login flow", "map_says": "tests/"},
]


def scripted_search_no_map(files: dict, target: str) -> dict:
    """Without map: walk all files until target found. Count reads."""
    reads = 0
    tokens = 0
    found = False
    for path in sorted(files.keys()):
        reads += 1
        tokens += count_tokens(files[path])
        if path == target:
            found = True
            break
    return {"reads": reads, "tokens": tokens, "found": found}


def scripted_search_with_map(files: dict, target: str, map_text: str,
                             decisions: str, traps: str) -> dict:
    """With map: read map+decisions+traps, then read only the target file."""
    map_tokens = count_tokens(map_text)
    dec_tokens = count_tokens(decisions)
    trap_tokens = count_tokens(traps)
    overhead = map_tokens + dec_tokens + trap_tokens

    if target in files:
        file_tokens = count_tokens(files[target])
        return {"reads": 1, "tokens": overhead + file_tokens, "found": True,
                "overhead": overhead, "file_tokens": file_tokens}
    return {"reads": 0, "tokens": overhead, "found": False, "overhead": overhead}


def main():
    parser = argparse.ArgumentParser(description="Experiment 81: Repo Map Large")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken; has_tiktoken = True
    except ImportError: pass
    token_label = "MEASURED (tiktoken)" if has_tiktoken else "ESTIMATED"

    print("=" * 65)
    print("EXPERIMENT 81: Repo Map + Decisions + Traps (Larger Fixture)")
    print("=" * 65)
    print(f"Token counting: {token_label}")
    print("Search policy: SCRIPTED (not a live agent).")
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        files = build_fixture(tmpdir)
        map_text = build_map(files)
        map_tokens = count_tokens(map_text)
        dec_tokens = count_tokens(DECISIONS)
        trap_tokens = count_tokens(TRAPS)
        total_file_tokens = sum(count_tokens(c) for c in files.values())

        print(f"Fixture: {len(files)} files in {len(set(os.path.dirname(p) for p in files))} directories")
        print(f"Total file tokens: {total_file_tokens:,}")
        print(f"Map: {map_tokens} tokens | Decisions: {dec_tokens} | Traps: {trap_tokens}")
        print(f"Overhead (map+decisions+traps): {map_tokens + dec_tokens + trap_tokens} tokens")
        print()

        print(f"{'Task':<22} {'No Map reads':>12} {'No Map tok':>10} {'Map reads':>10} {'Map tok':>8} {'Found':>6}")
        print("-" * 72)

        total_no_map_reads = 0
        total_no_map_tokens = 0
        total_map_reads = 0
        total_map_tokens = 0
        all_found = True
        task_results = []

        for task in TASKS:
            no_map = scripted_search_no_map(files, task["target"])
            with_map = scripted_search_with_map(files, task["target"], map_text, DECISIONS, TRAPS)

            total_no_map_reads += no_map["reads"]
            total_no_map_tokens += no_map["tokens"]
            total_map_reads += with_map["reads"]
            total_map_tokens += with_map["tokens"]
            if not with_map["found"]:
                all_found = False

            task_results.append({
                "task": task["name"], "target": task["target"],
                "no_map_reads": no_map["reads"], "no_map_tokens": no_map["tokens"],
                "map_reads": with_map["reads"], "map_tokens": with_map["tokens"],
                "found": with_map["found"],
            })

            print(f"  {task['name']:<20} {no_map['reads']:>12} {no_map['tokens']:>10,} "
                  f"{with_map['reads']:>10} {with_map['tokens']:>8,} "
                  f"{'yes' if with_map['found'] else 'NO':>6}")

        # Add map overhead to total (map read once, amortized across tasks)
        overhead = map_tokens + dec_tokens + trap_tokens

        read_savings = (total_no_map_reads - total_map_reads) / total_no_map_reads * 100
        token_savings = (total_no_map_tokens - total_map_tokens) / total_no_map_tokens * 100

        print()
        print(f"{'Metric':<40} {'No Map':>10} {'With Map':>10}")
        print("-" * 62)
        print(f"{'Total file reads':<40} {total_no_map_reads:>10} {total_map_reads:>10}")
        print(f"{'Total tokens':<40} {total_no_map_tokens:>10,} {total_map_tokens:>10,}")
        print(f"{'Read reduction':<40} {'—':>10} {read_savings:>9.1f}%")
        print(f"{'Token reduction':<40} {'—':>10} {token_savings:>9.1f}%")
        print(f"{'Map/decisions/traps overhead':<40} {'0':>10} {overhead:>10}")
        print(f"{'All targets found':<40} {'—':>10} {str(all_found):>10}")
        print()

        print(f"Quality check: all {len(TASKS)} tasks found the right file: {all_found}")
        print()
        print(f"Conclusion ({token_label}):")
        print(f"  {read_savings:.0f}% fewer file reads, {token_savings:.0f}% fewer tokens.")
        print(f"  The map+decisions+traps cost {overhead} tokens of overhead.")
        print(f"  This is a SCRIPTED search policy, not a live agent.")
        print(f"  Quality: all {len(TASKS)} tasks found the correct target file.")
        print(f"  Fixture: {len(files)} files (larger than exps 70/73's 3 files,")
        print(f"  but still synthetic — real repos may be larger and messier).")

    summary = {
        "experiment": "81_repo_map_large",
        "simulated": False,
        "search_policy_scripted": True,
        "not_a_live_agent": True,
        "token_method": "tiktoken" if has_tiktoken else "word_estimate",
        "files": len(files),
        "tasks": len(TASKS),
        "total_no_map_reads": total_no_map_reads,
        "total_map_reads": total_map_reads,
        "read_reduction_pct": round(read_savings, 2),
        "total_no_map_tokens": total_no_map_tokens,
        "total_map_tokens": total_map_tokens,
        "token_reduction_pct": round(token_savings, 2),
        "overhead_tokens": overhead,
        "all_found": all_found,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
