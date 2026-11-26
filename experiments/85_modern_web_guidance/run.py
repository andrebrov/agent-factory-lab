#!/usr/bin/env python3
"""
Experiment 85: Load Modern Web Guidance for Web Tasks
========================================================

STATUS: COULD NOT RUN (eval).

No Claude Code CLI, no API keys, no Playwright test infrastructure.
Running the actual eval (229 tasks, Playwright graders) requires a real
coding agent. We cannot run a fair A/B.

WHAT WAS DONE: fetched the repo, measured the guidance content's token
footprint, documented loading conditions. The 54%→94% claim is Google's
own published result, NOT verified by this lab.

This experiment reports token footprint only. It does NOT claim any quality
improvement and does NOT restate the 54%→94% figure as our own result.
"""
import json, os, subprocess, tempfile, argparse


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


def main():
    parser = argparse.ArgumentParser(description="Experiment 85: Modern Web Guidance")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    has_tiktoken = False
    try:
        import tiktoken; has_tiktoken = True
    except ImportError: pass
    token_label = "MEASURED (tiktoken)" if has_tiktoken else "ESTIMATED"

    print("=" * 65)
    print("EXPERIMENT 85: Modern Web Guidance for Web Tasks")
    print("=" * 65)
    print("STATUS: COULD NOT RUN (eval).")
    print("No Claude Code CLI, no API keys, no Playwright.")
    print()

    # Try to fetch the guidance repo and measure content
    repo_dir = "/tmp/modern-web-guidance"
    fetched = False
    guide_tokens = 0
    guide_count = 0
    guide_files = []

    if not os.path.isdir(repo_dir):
        print("Fetching GoogleChrome/modern-web-guidance...")
        r = subprocess.run(
            ["git", "clone", "--depth", "1",
             "https://github.com/GoogleChrome/modern-web-guidance.git", repo_dir],
            capture_output=True, text=True, timeout=30)
        fetched = r.returncode == 0
        if fetched:
            print(f"  Cloned successfully.")
        else:
            print(f"  Clone failed: {r.stderr[:100]}")
    else:
        fetched = True
        print(f"  Using existing clone at {repo_dir}")
    print()

    if fetched:
        # Find guide/skill files — the repo uses skills/, not guides/
        for search_dir in ["skills", "guides"]:
            sdir = os.path.join(repo_dir, search_dir)
            if not os.path.isdir(sdir):
                continue
            for root, _, files in os.walk(sdir):
                for f in files:
                    if f.endswith(".md"):
                        path = os.path.join(root, f)
                        try:
                            content = open(path).read()
                            tokens = count_tokens(content)
                            guide_tokens += tokens
                            guide_count += 1
                            guide_files.append({"file": os.path.relpath(path, repo_dir),
                                                "tokens": tokens})
                        except (OSError, UnicodeDecodeError):
                            pass

        print(f"Token Footprint ({token_label}):")
        print(f"  Guide files found: {guide_count}")
        print(f"  Total guide tokens: {guide_tokens:,}")
        if guide_count > 0:
            print(f"  Avg tokens per guide: {guide_tokens // guide_count}")
        print()

        # Top 5 largest guides
        if guide_files:
            guide_files.sort(key=lambda x: -x["tokens"])
            print(f"  Top-5 largest guides:")
            for gf in guide_files[:5]:
                print(f"    {gf['file']:<50} {gf['tokens']:>6} tokens")
        print()

        # Loading conditions
        print("Loading conditions (proposal, not tested):")
        print("  Load guidance only when task touches front-end code")
        print("  (HTML, CSS, JS/TS in src/components/, src/pages/, etc.)")
        print("  Skip for backend-only tasks (API, DB, CLI)")
        print()

    # Published results (NOT our measurement)
    print("Published eval results (Google's, NOT verified by this lab):")
    print("  Agent: Claude Code (Opus 5.5)")
    print("  Tasks: 229, Checks: 1961")
    print("  Unguided: 54% → Guided: 94% (+40pp)")
    print("  Eval method: Playwright graders on real browser behavior")
    print("  Source: GoogleChrome/modern-web-guidance README")
    print()
    print("  We did NOT run this eval. We cannot confirm or deny these numbers.")
    print("  Running it requires: Claude Code CLI, API key, Playwright, Node.js,")
    print("  and the eval harness from GoogleChrome/modern-web-guidance-src.")
    print()

    print(f"Conclusion:")
    print(f"  Token footprint: {guide_tokens:,} tokens for {guide_count} guides ({token_label}).")
    print(f"  The eval (54%→94%) is Google's published result, not ours.")
    print(f"  We could not run the eval: no Claude Code CLI, no API key, no Playwright.")
    print(f"  The guidance is Apache-2.0 licensed and installable via npx or Claude plugin.")

    summary = {
        "experiment": "85_modern_web_guidance",
        "could_not_run_eval": True,
        "token_footprint_measured": fetched and has_tiktoken,
        "guide_count": guide_count,
        "guide_tokens": guide_tokens,
        "published_result_not_ours": {
            "agent": "Claude Code (Opus 5.5)",
            "tasks": 229,
            "checks": 1961,
            "unguided": "54%",
            "guided": "94%",
            "uplift": "+40pp",
            "source": "GoogleChrome/modern-web-guidance README, Nov 20 2026",
        },
        "eval_requirements": ["Claude Code CLI", "Anthropic API key", "Playwright", "Node.js",
                              "GoogleChrome/modern-web-guidance-src eval harness"],
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
