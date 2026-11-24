#!/usr/bin/env python3
"""
Experiment 79: Harness A/B — Rex vs herdr + Claude Code
==========================================================

STATUS: COULD NOT RUN.

Neither Rex nor herdr is installed on this VM. No Claude CLI. No API keys.
Building a toy stand-in and reporting its numbers as evidence about real
Rex vs herdr would be dishonest. This experiment documents what would be
needed and reports NO results.

Requirements to run this experiment:
- Rex installed and running (superlogical.com/rex)
- herdr installed and running (herdr.dev)
- Claude Code CLI installed (claude.ai)
- Anthropic API key with sufficient quota
- A set of 10+ coding tasks on a real codebase
- Same model (e.g., Claude Opus) configured in both harnesses

Metrics to collect:
- Pass rate (tests passing after agent work)
- Total tokens (input + output, including retries)
- Wall-clock time per task
- Cost per task at the same model pricing
"""
import json
import os
import argparse


def main():
    parser = argparse.ArgumentParser(description="Experiment 79: Harness A/B")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 79: Harness A/B — Rex vs herdr + Claude Code")
    print("=" * 65)
    print()
    print("STATUS: COULD NOT RUN.")
    print()
    print("Neither Rex nor herdr is installed on this VM.")
    print("No Claude CLI. No API keys.")
    print()
    print("Building a toy stand-in and reporting its numbers as evidence")
    print("about real Rex vs herdr would be dishonest.")
    print()
    print("This experiment documents the design and reports NO results.")
    print()
    print("Requirements to run:")
    print("  - Rex installed and running")
    print("  - herdr installed and running")
    print("  - Claude Code CLI installed")
    print("  - Anthropic API key with sufficient quota")
    print("  - 10+ coding tasks on a real codebase")
    print("  - Same model configured in both harnesses")
    print()
    print("The claimed 5x harness cost gap (Artificial Analysis) is")
    print("NEITHER CONFIRMED NOR REFUTED by this experiment.")

    summary = {
        "experiment": "79_harness_ab",
        "could_not_run": True,
        "reason": "Rex, herdr, Claude CLI not available; no API keys",
        "results": None,
        "claimed_5x_gap_verified": False,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
