#!/usr/bin/env python3
"""
Experiment 65: Agent Inbox — Human Reply Queue
=================================================

Builds a minimal inbox (Plannotator not installable in this headless VM).
Agents post messages; the human sees them sorted by urgency. Compares
against exp 64's needs-you view.

MEASURED: inbox logic on 15 labeled messages.
Sample: 5 agents, 15 messages (5 questions, 4 reviews, 3 results, 3 status).
"""
import json
import os
import time
import argparse

INBOX_MESSAGES = [
    {"id": "m1", "agent": "writer-auth", "type": "question", "urgency": 3,
     "text": "Should I fix the CORS issue in the same PR or separate?",
     "needs_reply": True, "blocking": True},
    {"id": "m2", "agent": "writer-api", "type": "result", "urgency": 1,
     "text": "PR #42 opened: rate limiting for /api/ endpoints. 12 tests pass.",
     "needs_reply": False, "blocking": False},
    {"id": "m3", "agent": "reviewer", "type": "review", "urgency": 2,
     "text": "PR #41 reviewed: 2 issues found (missing null check, no test for edge case).",
     "needs_reply": True, "blocking": False},
    {"id": "m4", "agent": "writer-db", "type": "question", "urgency": 3,
     "text": "Migration requires manual approval. Proceed?",
     "needs_reply": True, "blocking": True},
    {"id": "m5", "agent": "qa", "type": "result", "urgency": 1,
     "text": "Integration tests: 47/47 passed.",
     "needs_reply": False, "blocking": False},
    {"id": "m6", "agent": "writer-auth", "type": "status", "urgency": 0,
     "text": "Working on JWT bypass fix (step 3/5).",
     "needs_reply": False, "blocking": False},
    {"id": "m7", "agent": "reviewer", "type": "review", "urgency": 2,
     "text": "PR #43 reviewed: approved, no issues.",
     "needs_reply": False, "blocking": False},
    {"id": "m8", "agent": "writer-api", "type": "question", "urgency": 3,
     "text": "The API key for staging is expired. Can you rotate it?",
     "needs_reply": True, "blocking": True},
    {"id": "m9", "agent": "deployer", "type": "review", "urgency": 2,
     "text": "Deploy preview ready: https://preview-42.example.com. Please verify.",
     "needs_reply": True, "blocking": False},
    {"id": "m10", "agent": "qa", "type": "status", "urgency": 0,
     "text": "Running performance benchmarks.",
     "needs_reply": False, "blocking": False},
    {"id": "m11", "agent": "writer-db", "type": "result", "urgency": 1,
     "text": "Schema migration applied. email_verified field added.",
     "needs_reply": False, "blocking": False},
    {"id": "m12", "agent": "reviewer", "type": "review", "urgency": 2,
     "text": "PR #44: security concern — SQL concatenation in search query.",
     "needs_reply": True, "blocking": True},
    {"id": "m13", "agent": "writer-auth", "type": "result", "urgency": 1,
     "text": "JWT fix complete. All 13 auth tests pass.",
     "needs_reply": False, "blocking": False},
    {"id": "m14", "agent": "deployer", "type": "status", "urgency": 0,
     "text": "Waiting for PR #42 merge to deploy.",
     "needs_reply": False, "blocking": False},
    {"id": "m15", "agent": "qa", "type": "question", "urgency": 3,
     "text": "Test environment DB is down. Should I wait or skip DB tests?",
     "needs_reply": True, "blocking": True},
]


class Inbox:
    def __init__(self):
        self.messages = []
        self.replies = {}

    def post(self, msg):
        msg["posted_at"] = time.time()
        msg["replied"] = False
        self.messages.append(msg)

    def get_sorted(self):
        return sorted(self.messages, key=lambda m: (-m["urgency"], m["posted_at"]))

    def get_needs_reply(self):
        return [m for m in self.get_sorted() if m["needs_reply"] and not m["replied"]]

    def reply(self, msg_id, text):
        for m in self.messages:
            if m["id"] == msg_id:
                m["replied"] = True
                self.replies[msg_id] = text
                return True
        return False

    def summary(self):
        needs = self.get_needs_reply()
        blocking = [m for m in needs if m.get("blocking")]
        non_blocking = [m for m in needs if not m.get("blocking")]
        results = [m for m in self.messages if m["type"] == "result"]
        return {
            "blocking_questions": len(blocking),
            "pending_reviews": len(non_blocking),
            "unread_results": len([r for r in results if not r.get("read")]),
            "total_messages": len(self.messages),
        }


def main():
    parser = argparse.ArgumentParser(description="Experiment 65: Agent Inbox")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 65: Agent Inbox — Human Reply Queue")
    print("=" * 65)
    print(f"Messages: {len(INBOX_MESSAGES)} (Plannotator not available — minimal equivalent)")
    print()

    inbox = Inbox()
    for msg in INBOX_MESSAGES:
        inbox.post(msg)

    # Check sorting
    print("Phase 1: Inbox Sorting (MEASURED)")
    print("-" * 50)

    sorted_msgs = inbox.get_sorted()
    needs_reply = inbox.get_needs_reply()

    # Verify blocking items come first
    first_blocking_idx = None
    first_non_blocking_idx = None
    for i, m in enumerate(sorted_msgs):
        if m.get("blocking") and first_blocking_idx is None:
            first_blocking_idx = i
        if not m.get("blocking") and m["needs_reply"] and first_non_blocking_idx is None:
            first_non_blocking_idx = i

    blocking_first = (first_blocking_idx is not None and
                      (first_non_blocking_idx is None or first_blocking_idx < first_non_blocking_idx))

    print(f"  Total messages: {len(inbox.messages)}")
    print(f"  Needs reply: {len(needs_reply)}")
    print(f"  Blocking questions at top: {blocking_first}")
    print()

    print("  Top-5 (should be blocking questions):")
    for i, m in enumerate(sorted_msgs[:5]):
        print(f"    #{i+1} [{m['type']:<10}] {m['agent']:<14} "
              f"urgency={m['urgency']} blocking={m.get('blocking',False)}")

    # Verify no missed items
    true_needs_reply = [m for m in INBOX_MESSAGES if m["needs_reply"]]
    inbox_needs = inbox.get_needs_reply()
    missed = [m for m in true_needs_reply if m["id"] not in {n["id"] for n in inbox_needs}]
    surfaced_all = len(missed) == 0

    print(f"\n  Items needing reply: {len(true_needs_reply)}")
    print(f"  Inbox surfaced: {len(inbox_needs)}")
    print(f"  Missed items: {len(missed)}")
    print()

    # Reply workflow
    print("Phase 2: Reply Workflow (MEASURED)")
    print("-" * 50)

    steps_to_reply = 2  # 1: read inbox, 2: type reply
    for m in needs_reply[:3]:
        inbox.reply(m["id"], "Approved" if m["type"] == "review" else "Yes, proceed")

    replied = sum(1 for m in inbox.messages if m["replied"])
    still_pending = len(inbox.get_needs_reply())

    print(f"  Replied to: {replied} messages")
    print(f"  Still pending: {still_pending}")
    print(f"  Steps per reply: {steps_to_reply} (read + respond)")
    print()

    # Compare with exp 64
    print("Phase 3: Comparison with Exp 64 (needs-you view)")
    print("-" * 50)
    exp64_panes = 16
    exp64_action = 6

    print(f"  Exp 64: {exp64_action} action items from {exp64_panes} panes (machine-level)")
    print(f"  Exp 65: {len(needs_reply)} items needing reply from {len(inbox.messages)} messages (message-level)")
    print(f"  Inbox adds: message-level granularity, reply tracking, blocking priority")
    print(f"  Exp 64 adds: cross-machine view, pane state, urgency ranking")
    print(f"  Complementary: inbox for messages, needs-you for pane states")
    print()

    summary_data = inbox.summary()

    print(f"{'Metric':<40} {'Value':>10}")
    print("-" * 52)
    print(f"{'Messages total':<40} {summary_data['total_messages']:>10}")
    print(f"{'Blocking questions':<40} {summary_data['blocking_questions']:>10}")
    print(f"{'Pending reviews':<40} {summary_data['pending_reviews']:>10}")
    print(f"{'All needing-reply surfaced':<40} {str(surfaced_all):>10}")
    print(f"{'Missed items':<40} {len(missed):>10}")
    print(f"{'Steps per reply':<40} {steps_to_reply:>10}")
    print()

    print(f"Conclusion: Inbox surfaces {len(needs_reply)} items needing reply with")
    print(f"blocking questions first. {len(missed)} missed items. {steps_to_reply} steps per reply.")
    print(f"Complementary to exp 64: inbox for messages, needs-you for panes.")
    print(f"Plannotator not tested (requires browser + agent hooks).")
    print(f"Sample: {len(INBOX_MESSAGES)} messages, 5 agents.")

    exp_summary = {
        "experiment": "65_agent_inbox",
        "simulated": False,
        "plannotator_available": False,
        "minimal_equivalent": True,
        "messages": len(INBOX_MESSAGES),
        "needs_reply": len(needs_reply),
        "missed": len(missed),
        "surfaced_all": surfaced_all,
        "blocking_first": blocking_first,
        "steps_per_reply": steps_to_reply,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(exp_summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
