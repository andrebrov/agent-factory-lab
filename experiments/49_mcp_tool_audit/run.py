#!/usr/bin/env python3
"""
Experiment 49: MCP Tool-Loading Audit — Upfront vs Deferred vs Pruned
=======================================================================

Measures tokens that tool definitions from sample MCP servers add to the
system prompt. Compares: all upfront, frequently-used only, deferred via
search/describe, and pruning unused servers entirely.

MEASURED: real tiktoken token counting on representative tool definitions.
Tool definitions are based on real MCP server schemas (filesystem, git,
web search, database, Docker, etc.) but are not live MCP connections.
"""
import json
import os
import argparse

MCP_SERVERS = {
    "filesystem": {
        "description": "File system operations",
        "tools": [
            {"name": "read_file", "description": "Read the contents of a file at the given path", "parameters": {"path": {"type": "string", "description": "Absolute path to the file"}}},
            {"name": "write_file", "description": "Write content to a file, creating it if needed", "parameters": {"path": {"type": "string"}, "content": {"type": "string"}}},
            {"name": "list_directory", "description": "List files and directories at the given path", "parameters": {"path": {"type": "string"}}},
            {"name": "search_files", "description": "Search for files matching a glob pattern", "parameters": {"pattern": {"type": "string"}, "path": {"type": "string"}}},
            {"name": "move_file", "description": "Move or rename a file", "parameters": {"source": {"type": "string"}, "destination": {"type": "string"}}},
            {"name": "get_file_info", "description": "Get metadata about a file (size, modified, permissions)", "parameters": {"path": {"type": "string"}}},
        ],
        "usage_frequency": "high",
    },
    "git": {
        "description": "Git version control operations",
        "tools": [
            {"name": "git_status", "description": "Show the working tree status", "parameters": {}},
            {"name": "git_diff", "description": "Show changes between commits, working tree, etc.", "parameters": {"ref": {"type": "string"}}},
            {"name": "git_log", "description": "Show commit logs", "parameters": {"n": {"type": "integer"}, "oneline": {"type": "boolean"}}},
            {"name": "git_commit", "description": "Record changes to the repository", "parameters": {"message": {"type": "string"}, "all": {"type": "boolean"}}},
            {"name": "git_branch", "description": "List, create, or delete branches", "parameters": {"name": {"type": "string"}, "delete": {"type": "boolean"}}},
            {"name": "git_checkout", "description": "Switch branches or restore working tree files", "parameters": {"ref": {"type": "string"}, "create": {"type": "boolean"}}},
            {"name": "git_stash", "description": "Stash changes in a dirty working directory", "parameters": {"pop": {"type": "boolean"}}},
        ],
        "usage_frequency": "high",
    },
    "web_search": {
        "description": "Web search and browsing",
        "tools": [
            {"name": "search", "description": "Search the web for information", "parameters": {"query": {"type": "string"}, "num_results": {"type": "integer"}}},
            {"name": "fetch_url", "description": "Fetch and extract content from a URL", "parameters": {"url": {"type": "string"}, "selector": {"type": "string"}}},
            {"name": "screenshot", "description": "Take a screenshot of a web page", "parameters": {"url": {"type": "string"}, "width": {"type": "integer"}}},
        ],
        "usage_frequency": "low",
    },
    "database": {
        "description": "Database operations (PostgreSQL)",
        "tools": [
            {"name": "query", "description": "Execute a SQL query and return results", "parameters": {"sql": {"type": "string"}, "params": {"type": "array"}}},
            {"name": "describe_table", "description": "Get column names and types for a table", "parameters": {"table": {"type": "string"}}},
            {"name": "list_tables", "description": "List all tables in the database", "parameters": {}},
            {"name": "explain", "description": "Show the execution plan for a query", "parameters": {"sql": {"type": "string"}}},
        ],
        "usage_frequency": "never",
    },
    "docker": {
        "description": "Docker container management",
        "tools": [
            {"name": "docker_ps", "description": "List running containers", "parameters": {"all": {"type": "boolean"}}},
            {"name": "docker_build", "description": "Build an image from a Dockerfile", "parameters": {"path": {"type": "string"}, "tag": {"type": "string"}}},
            {"name": "docker_run", "description": "Run a command in a new container", "parameters": {"image": {"type": "string"}, "command": {"type": "string"}, "ports": {"type": "array"}}},
            {"name": "docker_logs", "description": "Fetch the logs of a container", "parameters": {"container": {"type": "string"}, "tail": {"type": "integer"}}},
            {"name": "docker_exec", "description": "Execute a command in a running container", "parameters": {"container": {"type": "string"}, "command": {"type": "string"}}},
        ],
        "usage_frequency": "never",
    },
    "slack": {
        "description": "Slack messaging",
        "tools": [
            {"name": "send_message", "description": "Send a message to a Slack channel", "parameters": {"channel": {"type": "string"}, "text": {"type": "string"}}},
            {"name": "list_channels", "description": "List all channels in the workspace", "parameters": {}},
            {"name": "search_messages", "description": "Search for messages matching a query", "parameters": {"query": {"type": "string"}}},
        ],
        "usage_frequency": "never",
    },
}

SEARCH_DESCRIBE_OVERHEAD = 50  # tokens for a search-then-describe flow


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def tool_definition_text(server_name: str, server: dict) -> str:
    """Generate the tool definition text that would appear in the prompt."""
    lines = [f"## {server_name}: {server['description']}"]
    for tool in server["tools"]:
        params = ", ".join(f"{k}: {v['type']}" for k, v in tool["parameters"].items())
        lines.append(f"- {tool['name']}({params}): {tool['description']}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Experiment 49: MCP Tool Audit")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken
        has_tiktoken = True
    except ImportError:
        pass
    token_label = "MEASURED (tiktoken)" if has_tiktoken else "ESTIMATED"

    print("=" * 65)
    print("EXPERIMENT 49: MCP Tool-Loading Audit")
    print("=" * 65)
    print(f"Token counting: {token_label}")
    print(f"MCP servers: {len(MCP_SERVERS)}, Total tools: "
          f"{sum(len(s['tools']) for s in MCP_SERVERS.values())}")
    print()
    print("--- REAL TOKEN COUNTS (representative tool definitions) ---")
    print()

    # Measure per-server tokens
    server_tokens = {}
    total_tools = 0
    print(f"{'Server':<15} {'Tools':>5} {'Tokens':>8} {'Usage':>10}")
    print("-" * 42)
    for name, server in MCP_SERVERS.items():
        text = tool_definition_text(name, server)
        tokens = count_tokens(text)
        server_tokens[name] = {
            "tokens": tokens,
            "tools": len(server["tools"]),
            "usage": server["usage_frequency"],
        }
        total_tools += len(server["tools"])
        print(f"  {name:<13} {len(server['tools']):>5} {tokens:>8} {server['usage_frequency']:>10}")

    total_upfront = sum(s["tokens"] for s in server_tokens.values())
    print(f"  {'TOTAL':<13} {total_tools:>5} {total_upfront:>8}")
    print()

    # Strategy comparison
    high_only = sum(s["tokens"] for n, s in server_tokens.items()
                    if MCP_SERVERS[n]["usage_frequency"] == "high")
    low_servers = sum(1 for s in MCP_SERVERS.values() if s["usage_frequency"] == "low")
    never_servers = sum(1 for s in MCP_SERVERS.values() if s["usage_frequency"] == "never")
    deferred = high_only + low_servers * SEARCH_DESCRIBE_OVERHEAD
    pruned = high_only

    savings_deferred = (total_upfront - deferred) / total_upfront * 100
    savings_pruned = (total_upfront - pruned) / total_upfront * 100

    print(f"{'Strategy':<40} {'Tokens':>8} {'Savings':>10}")
    print("-" * 60)
    print(f"{'All upfront (6 servers, 28 tools)':<40} {total_upfront:>8} {'baseline':>10}")
    print(f"{'High-use only + deferred search (2+1)':<40} {deferred:>8} {savings_deferred:>9.1f}%")
    print(f"{'High-use only, prune unused (2 servers)':<40} {pruned:>8} {savings_pruned:>9.1f}%")
    print()

    # Per-request impact over a session
    turns = 20
    upfront_session = total_upfront * turns  # sent every turn (no caching)
    pruned_session = pruned * turns
    # With caching: first turn full, rest cached at 10% cost
    cached_session = total_upfront + total_upfront * 0.1 * (turns - 1)
    pruned_cached = pruned + pruned * 0.1 * (turns - 1)

    print(f"Session impact ({turns} turns):")
    print(f"  {'Mode':<35} {'Total Tokens':>12}")
    print(f"  {'-' * 49}")
    print(f"  {'All upfront, no cache':<35} {upfront_session:>12,}")
    print(f"  {'All upfront, with cache':<35} {cached_session:>12,.0f}")
    print(f"  {'Pruned, no cache':<35} {pruned_session:>12,}")
    print(f"  {'Pruned + cached':<35} {pruned_cached:>12,.0f}")
    pruned_cached_savings = (upfront_session - pruned_cached) / upfront_session * 100
    print(f"  {'Pruned+cached vs all uncached':<35} {'':>12} {pruned_cached_savings:.1f}%")
    print()

    print(f"Conclusion ({token_label}): Loading all 6 MCP servers costs")
    print(f"{total_upfront} tokens before the first turn. Pruning unused servers")
    print(f"({never_servers} never-used) saves {savings_pruned:.0f}%. Combined with prompt")
    print(f"caching over {turns} turns, the savings reach {pruned_cached_savings:.0f}%.")
    print(f"Sample: {len(MCP_SERVERS)} representative servers, {total_tools} tools.")

    summary = {
        "experiment": "49_mcp_tool_audit",
        "simulated": False,
        "token_method": "tiktoken" if has_tiktoken else "word_estimate",
        "servers": len(MCP_SERVERS),
        "total_tools": total_tools,
        "total_upfront_tokens": total_upfront,
        "high_use_only_tokens": pruned,
        "deferred_tokens": deferred,
        "savings_pruned_pct": round(savings_pruned, 2),
        "savings_deferred_pct": round(savings_deferred, 2),
        "session_savings_pruned_cached_pct": round(pruned_cached_savings, 2),
        "per_server": server_tokens,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
