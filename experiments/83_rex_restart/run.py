#!/usr/bin/env python3
"""
Experiment 83: Rex Restart-Resume Drill
==========================================

STATUS: COULD NOT RUN.

Rex is not installed on this VM. herdr is not installed. No Claude CLI.
No API keys. Same situation as experiment 79.

Building a toy process manager and presenting its behavior as evidence
about Rex's OSC 7577 restart-resume protocol would be dishonest.

Requirements to actually run this experiment:
- Rex installed and running (superlogical.com/rex)
- Agent panes with active tasks (Claude Code or similar)
- Ability to restart Rex server mid-task
- Verification that tracked jobs reattach via OSC 7577
- herdr with OSC 7577 support (when available)
"""
import json, os, argparse


def main():
    parser = argparse.ArgumentParser(description="Experiment 83: Rex Restart")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 83: Rex Restart-Resume Drill")
    print("=" * 65)
    print()
    print("STATUS: COULD NOT RUN.")
    print()
    print("Rex is not installed on this VM.")
    print("herdr is not installed.")
    print("No Claude CLI. No API keys.")
    print()
    print("This is the same situation as experiment 79.")
    print("No stand-in was built. No results to report.")
    print()
    print("Requirements:")
    print("  - Rex installed and running")
    print("  - Agent panes with active tasks")
    print("  - Restart Rex server mid-task")
    print("  - Verify job reattachment via OSC 7577")

    summary = {
        "experiment": "83_rex_restart",
        "could_not_run": True,
        "reason": "Rex, herdr, Claude CLI not available; no API keys",
        "results": None,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
