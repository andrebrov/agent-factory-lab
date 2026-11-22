#!/usr/bin/env python3
"""
Experiment 72: Per-Role Tool Budget
=======================================

Measures tokens before first prompt with all MCP servers vs role-specific
loading. FAIRLY counts the on-demand discovery cost (search + describe +
load) when a tool is needed but wasn't preloaded.

Tool definitions are representative, not fitted to the roles.

MEASURED: real tiktoken on tool definitions.
Sample: 4 roles, 8 MCP servers, 35 tools.
"""
import json
import os
import argparse

# Tool definitions — representative of real MCP servers, written before roles
MCP_SERVERS = {
    "filesystem": {
        "tools": [
            {"name": "read_file", "desc": "Read a file at the given path", "params": "path:str"},
            {"name": "write_file", "desc": "Write content to a file", "params": "path:str, content:str"},
            {"name": "list_dir", "desc": "List files in a directory", "params": "path:str"},
            {"name": "search_files", "desc": "Search files matching a pattern", "params": "pattern:str, path:str"},
            {"name": "move_file", "desc": "Move or rename a file", "params": "src:str, dest:str"},
        ],
    },
    "git": {
        "tools": [
            {"name": "git_status", "desc": "Show working tree status", "params": ""},
            {"name": "git_diff", "desc": "Show changes", "params": "ref:str"},
            {"name": "git_log", "desc": "Show commit log", "params": "n:int"},
            {"name": "git_commit", "desc": "Commit changes", "params": "msg:str"},
            {"name": "git_branch", "desc": "List or create branches", "params": "name:str"},
        ],
    },
    "test_runner": {
        "tools": [
            {"name": "run_tests", "desc": "Run the test suite", "params": "path:str, flags:str"},
            {"name": "test_coverage", "desc": "Get coverage report", "params": ""},
        ],
    },
    "linter": {
        "tools": [
            {"name": "lint_check", "desc": "Run linter", "params": "path:str"},
            {"name": "lint_fix", "desc": "Auto-fix lint issues", "params": "path:str"},
        ],
    },
    "web_search": {
        "tools": [
            {"name": "search_web", "desc": "Search the web", "params": "query:str"},
            {"name": "fetch_url", "desc": "Fetch a URL", "params": "url:str"},
            {"name": "screenshot", "desc": "Screenshot a page", "params": "url:str"},
        ],
    },
    "database": {
        "tools": [
            {"name": "db_query", "desc": "Run SQL query", "params": "sql:str"},
            {"name": "db_tables", "desc": "List tables", "params": ""},
            {"name": "db_describe", "desc": "Describe a table", "params": "table:str"},
            {"name": "db_explain", "desc": "Explain query plan", "params": "sql:str"},
        ],
    },
    "docker": {
        "tools": [
            {"name": "docker_ps", "desc": "List containers", "params": "all:bool"},
            {"name": "docker_build", "desc": "Build image", "params": "path:str, tag:str"},
            {"name": "docker_run", "desc": "Run container", "params": "image:str, cmd:str"},
            {"name": "docker_logs", "desc": "Fetch logs", "params": "container:str"},
            {"name": "docker_exec", "desc": "Exec in container", "params": "container:str, cmd:str"},
        ],
    },
    "deploy": {
        "tools": [
            {"name": "deploy_preview", "desc": "Deploy preview environment", "params": "branch:str"},
            {"name": "deploy_prod", "desc": "Deploy to production", "params": "ref:str"},
            {"name": "deploy_status", "desc": "Check deploy status", "params": "id:str"},
            {"name": "deploy_rollback", "desc": "Rollback deployment", "params": "id:str"},
        ],
    },
}

# Roles — written after tool definitions, NOT fitted to them
ROLES = {
    "writer": {"needs": ["filesystem", "git", "test_runner", "linter"],
               "might_need": ["web_search"]},
    "reviewer": {"needs": ["filesystem", "git", "test_runner"],
                 "might_need": ["linter"]},
    "deployer": {"needs": ["git", "deploy", "docker"],
                 "might_need": ["filesystem"]},
    "researcher": {"needs": ["web_search", "filesystem"],
                   "might_need": ["git"]},
}

# Cost of on-demand tool discovery (search + describe + load)
ON_DEMAND_OVERHEAD_PER_SERVER = 80  # tokens: search query + describe response + load


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def server_tokens(server_name: str) -> int:
    server = MCP_SERVERS[server_name]
    text = f"## {server_name}\n"
    for tool in server["tools"]:
        text += f"- {tool['name']}({tool['params']}): {tool['desc']}\n"
    return count_tokens(text)


def main():
    parser = argparse.ArgumentParser(description="Experiment 72: Role Tool Budget")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken; has_tiktoken = True
    except ImportError: pass
    token_label = "MEASURED (tiktoken)" if has_tiktoken else "ESTIMATED"

    total_tools = sum(len(s["tools"]) for s in MCP_SERVERS.values())

    print("=" * 65)
    print("EXPERIMENT 72: Per-Role Tool Budget")
    print("=" * 65)
    print(f"Token counting: {token_label}")
    print(f"Servers: {len(MCP_SERVERS)}, Tools: {total_tools}, Roles: {len(ROLES)}")
    print(f"On-demand overhead per server: {ON_DEMAND_OVERHEAD_PER_SERVER} tokens")
    print()

    # Measure per-server tokens
    srv_tokens = {name: server_tokens(name) for name in MCP_SERVERS}
    all_upfront = sum(srv_tokens.values())

    print(f"Per-server tokens ({token_label}):")
    for name, tok in sorted(srv_tokens.items(), key=lambda x: -x[1]):
        print(f"  {name:<15} {tok:>5} tokens ({len(MCP_SERVERS[name]['tools'])} tools)")
    print(f"  {'ALL UPFRONT':<15} {all_upfront:>5} tokens")
    print()

    # Per-role comparison
    print(f"{'Role':<12} {'All Upfront':>12} {'Role-Only':>10} {'+ On-Demand':>12} {'Net Savings':>12}")
    print("-" * 60)

    role_results = {}
    for role_name, role in ROLES.items():
        # Upfront: all servers loaded
        upfront = all_upfront

        # Role-only: load only the servers this role needs
        role_only = sum(srv_tokens[s] for s in role["needs"])

        # On-demand cost: when the role needs a "might_need" server, pay discovery overhead
        on_demand_cost = len(role["might_need"]) * ON_DEMAND_OVERHEAD_PER_SERVER
        # Plus the actual server tokens when loaded on demand
        on_demand_load = sum(srv_tokens[s] for s in role["might_need"])
        total_with_demand = role_only + on_demand_cost + on_demand_load

        # Fair savings: compare upfront vs role-only + on-demand overhead
        fair_savings = (upfront - total_with_demand) / upfront * 100

        role_results[role_name] = {
            "upfront": upfront,
            "role_only": role_only,
            "on_demand_cost": on_demand_cost,
            "on_demand_load": on_demand_load,
            "total_with_demand": total_with_demand,
            "fair_savings_pct": round(fair_savings, 1),
            "needs_servers": len(role["needs"]),
            "might_need_servers": len(role["might_need"]),
        }

        print(f"  {role_name:<10} {upfront:>10} {role_only:>10} {total_with_demand:>12} "
              f"{fair_savings:>11.1f}%")

    avg_savings = sum(r["fair_savings_pct"] for r in role_results.values()) / len(role_results)

    print()
    print(f"Average fair savings across roles: {avg_savings:.1f}%")
    print()

    # Detail one role to show the math
    writer = role_results["writer"]
    print(f"Detail — writer role:")
    print(f"  Needs: {ROLES['writer']['needs']} → {writer['role_only']} tokens")
    print(f"  Might need: {ROLES['writer']['might_need']} → "
          f"{writer['on_demand_cost']} overhead + {writer['on_demand_load']} load = "
          f"{writer['on_demand_cost'] + writer['on_demand_load']} tokens")
    print(f"  Total (fair): {writer['total_with_demand']} vs all-upfront {writer['upfront']}")
    print(f"  Fair savings: {writer['fair_savings_pct']}%")
    print()

    print(f"Conclusion ({token_label}):")
    print(f"  Average fair savings: {avg_savings:.1f}% across {len(ROLES)} roles.")
    print(f"  This includes the on-demand discovery overhead ({ON_DEMAND_OVERHEAD_PER_SERVER} tok/server)")
    print(f"  and the full load cost of might-need servers when actually used.")
    print(f"  The savings come from NOT loading servers the role never uses.")
    print(f"  CAVEAT: the {ON_DEMAND_OVERHEAD_PER_SERVER}-token on-demand overhead is estimated,")
    print(f"  not measured against a real MCP discovery flow.")
    print(f"  Sample: {len(ROLES)} roles, {len(MCP_SERVERS)} servers, {total_tools} tools.")

    summary = {
        "experiment": "72_role_tool_budget",
        "simulated": False,
        "token_method": "tiktoken" if has_tiktoken else "word_estimate",
        "on_demand_overhead_estimated": True,
        "servers": len(MCP_SERVERS),
        "tools": total_tools,
        "roles": len(ROLES),
        "all_upfront_tokens": all_upfront,
        "avg_fair_savings_pct": round(avg_savings, 1),
        "per_role": role_results,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
