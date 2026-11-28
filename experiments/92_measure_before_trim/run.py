#!/usr/bin/env python3
"""
Experiment 92: Measure Before Trimming Tokens
================================================

No API keys — cannot measure real billed tokens or cache hits.

What IS tested:
(a) A token logger that records per-call input/output/cached tokens.
(b) MCP/tool schema overhead: all-enabled vs role-trimmed, measured with
    tiktoken on fixture descriptors.

What COULD NOT RUN:
- Real billed token measurement from Claude/Codex/Gemini sessions.
- Real cache-hit tracking from Anthropic API responses.
- The 27–38% savings claim (EngineerHMS) is UNVERIFIED.

MEASURED: logger unit tests, tiktoken on fixture tool schemas.
COULD NOT RUN: real billed tokens, real cache hits.
"""
import json, os, argparse

# ── Part A: Token Logger (unit test) ──────────────────────────────────

class TokenLogger:
    """Logs per-call token usage. Unit-testable without an API key."""

    def __init__(self):
        self.calls = []

    def log_call(self, role: str, model: str, input_tokens: int,
                 output_tokens: int, cached_tokens: int = 0):
        self.calls.append({
            "role": role, "model": model,
            "input": input_tokens, "output": output_tokens,
            "cached": cached_tokens,
            "billed_input": input_tokens - cached_tokens,
        })

    def summary(self) -> dict:
        total_input = sum(c["input"] for c in self.calls)
        total_output = sum(c["output"] for c in self.calls)
        total_cached = sum(c["cached"] for c in self.calls)
        total_billed_input = sum(c["billed_input"] for c in self.calls)
        return {
            "calls": len(self.calls),
            "total_input": total_input,
            "total_output": total_output,
            "total_cached": total_cached,
            "total_billed_input": total_billed_input,
            "cache_hit_rate": round(total_cached / total_input * 100, 1) if total_input > 0 else 0,
        }

    def by_role(self) -> dict:
        roles = {}
        for c in self.calls:
            r = c["role"]
            if r not in roles:
                roles[r] = {"calls": 0, "input": 0, "output": 0, "cached": 0}
            roles[r]["calls"] += 1
            roles[r]["input"] += c["input"]
            roles[r]["output"] += c["output"]
            roles[r]["cached"] += c["cached"]
        return roles


def test_logger() -> dict:
    """Unit test the logger with known values."""
    logger = TokenLogger()
    logger.log_call("planner", "opus", 3000, 1500, 2000)
    logger.log_call("writer", "haiku", 5000, 2500, 4000)
    logger.log_call("scout", "haiku", 1000, 300, 800)
    logger.log_call("reviewer", "opus", 4000, 1000, 3000)

    s = logger.summary()
    tests = {
        "total_calls": s["calls"] == 4,
        "total_input": s["total_input"] == 13000,
        "total_output": s["total_output"] == 5300,
        "total_cached": s["total_cached"] == 9800,
        "billed_input": s["total_billed_input"] == 3200,
        "cache_rate": s["cache_hit_rate"] == 75.4,
        "by_role_count": len(logger.by_role()) == 4,  # planner, writer, scout, reviewer
    }
    return {"all_pass": all(tests.values()), "tests": tests, "summary": s}


# ── Part B: MCP/Tool Schema Overhead (tiktoken) ──────────────────────

def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


MCP_SERVERS = {
    "filesystem": {
        "tools": ["read_file(path:str): Read file", "write_file(path:str,content:str): Write file",
                   "list_dir(path:str): List directory", "search(pattern:str,path:str): Search files",
                   "move_file(src:str,dst:str): Move file"],
        "used_by": ["writer", "reviewer", "planner"],
    },
    "git": {
        "tools": ["git_status(): Working tree status", "git_diff(ref:str): Show changes",
                   "git_log(n:int): Commit log", "git_commit(msg:str): Commit",
                   "git_branch(name:str): Branch ops"],
        "used_by": ["writer", "reviewer"],
    },
    "test_runner": {
        "tools": ["run_tests(path:str,flags:str): Run tests", "coverage(): Coverage report"],
        "used_by": ["writer", "reviewer", "scout"],
    },
    "web_search": {
        "tools": ["search_web(query:str): Web search", "fetch_url(url:str): Fetch URL"],
        "used_by": ["researcher"],
    },
    "database": {
        "tools": ["query(sql:str): SQL query", "tables(): List tables",
                   "describe(table:str): Describe table"],
        "used_by": ["db_admin"],
    },
    "deploy": {
        "tools": ["deploy_preview(branch:str): Preview deploy",
                   "deploy_prod(ref:str): Production deploy",
                   "rollback(id:str): Rollback"],
        "used_by": ["deployer"],
    },
}

ROLES = ["writer", "reviewer", "planner", "scout", "researcher", "deployer", "db_admin"]


def measure_overhead(role: str) -> dict:
    """Measure tokens for all-enabled vs role-trimmed."""
    all_text = ""
    role_text = ""
    for name, server in MCP_SERVERS.items():
        server_text = f"## {name}\n" + "\n".join(f"- {t}" for t in server["tools"]) + "\n"
        all_text += server_text
        if role in server["used_by"]:
            role_text += server_text

    all_tokens = count_tokens(all_text)
    role_tokens = count_tokens(role_text)
    return {"all_tokens": all_tokens, "role_tokens": role_tokens,
            "saved": all_tokens - role_tokens,
            "saved_pct": round((all_tokens - role_tokens) / all_tokens * 100, 1) if all_tokens > 0 else 0}


def main():
    parser = argparse.ArgumentParser(description="Experiment 92: Measure Before Trim")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken; has_tiktoken = True
    except ImportError: pass
    token_label = "MEASURED (tiktoken)" if has_tiktoken else "ESTIMATED"

    print("=" * 65)
    print("EXPERIMENT 92: Measure Before Trimming Tokens")
    print("=" * 65)
    print("No API keys. Cannot measure real billed tokens or cache hits.")
    print("The 27–38% savings claim (EngineerHMS) is UNVERIFIED.")
    print()

    # Part A: Logger
    print("Part A: Token Logger Unit Test (MEASURED)")
    print("-" * 55)

    logger_result = test_logger()
    for name, passed in logger_result["tests"].items():
        icon = "OK" if passed else "!!"
        print(f"  [{icon}] {name}: {passed}")

    s = logger_result["summary"]
    print(f"\n  Summary: {s['calls']} calls, {s['total_input']:,} in, "
          f"{s['total_output']:,} out, {s['total_cached']:,} cached, "
          f"cache rate {s['cache_hit_rate']}%")
    print(f"  All tests pass: {logger_result['all_pass']}")
    print()

    # Part B: MCP overhead
    print(f"Part B: MCP/Tool Schema Overhead ({token_label})")
    print("-" * 55)

    all_text = ""
    for name, server in MCP_SERVERS.items():
        all_text += f"## {name}\n" + "\n".join(f"- {t}" for t in server["tools"]) + "\n"
    all_tokens = count_tokens(all_text)
    total_tools = sum(len(s["tools"]) for s in MCP_SERVERS.values())

    print(f"  Servers: {len(MCP_SERVERS)}, Tools: {total_tools}")
    print(f"  All-enabled overhead: {all_tokens} tokens")
    print()

    print(f"  {'Role':<15} {'All':>6} {'Trimmed':>8} {'Saved':>6} {'%':>6}")
    print(f"  {'-' * 43}")

    role_results = {}
    for role in ROLES:
        r = measure_overhead(role)
        role_results[role] = r
        print(f"  {role:<15} {r['all_tokens']:>6} {r['role_tokens']:>8} "
              f"{r['saved']:>6} {r['saved_pct']:>5.1f}%")

    avg_savings = sum(r["saved_pct"] for r in role_results.values()) / len(role_results)
    print(f"\n  Average savings across {len(ROLES)} roles: {avg_savings:.1f}%")
    print()

    # Part C: What could not run
    print("Part C: What COULD NOT RUN")
    print("-" * 55)
    print("  - Real billed token measurement (no API keys)")
    print("  - Real cache-hit tracking (no Anthropic API)")
    print("  - The 27–38% savings claim (unverified)")
    print("  - Live session logging (no Claude/Codex/Gemini)")
    print()

    print(f"Conclusion:")
    print(f"  Logger: all {len(logger_result['tests'])} unit tests pass (MEASURED).")
    print(f"  MCP overhead: role-trimming saves {avg_savings:.0f}% on average ({token_label}).")
    print(f"  Real billed tokens and cache hits: COULD NOT RUN (no API keys).")
    print(f"  The EngineerHMS 27–38% claim is UNVERIFIED by this lab.")

    summary = {
        "experiment": "92_measure_before_trim",
        "logger_measured": True,
        "mcp_overhead_measured": has_tiktoken,
        "real_billing_could_not_run": True,
        "real_cache_could_not_run": True,
        "savings_claim_unverified": True,
        "logger_all_pass": logger_result["all_pass"],
        "logger_tests": len(logger_result["tests"]),
        "mcp_servers": len(MCP_SERVERS),
        "mcp_tools": total_tools,
        "all_enabled_tokens": all_tokens,
        "avg_role_savings_pct": round(avg_savings, 1),
        "role_results": role_results,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
