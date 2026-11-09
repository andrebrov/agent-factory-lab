#!/usr/bin/env python3
"""
Experiment 39: Fold-and-Restore Compaction vs Hard Compaction
===============================================================

Implements a minimal fold-and-restore prototype: keeps the recent window
raw, folds finished subtasks into restorable summaries, and compares
against hard compaction (summarize and discard).

MEASURED: token counting (tiktoken). The fold/restore mechanism and
information-retention checks are real. Cache-hit rates and production
performance are billion-context's claims, not verified by us.

billion-context repo status: real, 775+ files, TypeScript. npm test hangs
(needs running proxy/mock). The paper's claims are the authors' own.
"""
import json
import os
import hashlib
import argparse

RECENT_WINDOW = 5  # keep last N subtasks raw

SUBTASKS = [
    {"id": "st1", "name": "Fix factorial bug", "content": "Changed range(0,n+1) to range(1,n+1). The factorial function was multiplying by zero because the range started at 0. Tests now pass for factorial(0)=1, factorial(1)=1, factorial(5)=120.", "tokens_est": 800},
    {"id": "st2", "name": "Fix fibonacci base case", "content": "Changed return 0 to return 1 for fib(1). The base case was wrong, causing all fibonacci numbers to be off by 1. Verified fib(0)=0, fib(1)=1, fib(10)=55.", "tokens_est": 750},
    {"id": "st3", "name": "Fix is_prime operator", "content": "Changed n//i==0 to n%i==0. Floor division always returns 0 for small i, making all numbers appear prime. Now correctly identifies 7 as prime and 4 as composite.", "tokens_est": 700},
    {"id": "st4", "name": "Fix binary_search return", "content": "Changed return mid to return -1 when element not found. The old code returned the last mid index which was meaningless. search([1,3,5,7],4) now returns -1.", "tokens_est": 650},
    {"id": "st5", "name": "Fix mean empty guard", "content": "Added if not numbers: raise ValueError before division. Empty list was causing ZeroDivisionError. Now raises ValueError('cannot compute mean of empty list').", "tokens_est": 600},
    {"id": "st6", "name": "Fix flatten isinstance", "content": "Changed isinstance(item, tuple) to isinstance(item, (list, tuple)). Nested lists were not being flattened, only tuples. flatten([1,[2,3]]) now correctly returns [1,2,3].", "tokens_est": 700},
    {"id": "st7", "name": "Fix merge_sorted init", "content": "Changed j=1 to j=0. Starting the second array index at 1 was skipping its first element. merge_sorted([1,3,5],[2,4,6]) now returns [1,2,3,4,5,6].", "tokens_est": 650},
    {"id": "st8", "name": "Fix caesar_cipher alpha", "content": "Added isalpha() check before shifting. Spaces, punctuation, and digits were being shifted, corrupting non-letter characters. 'Hi!' with shift 3 now correctly gives 'Kl!'.", "tokens_est": 750},
    {"id": "st9", "name": "Fix unique order", "content": "Replaced set() with seen-set pattern preserving insertion order. set() was losing the original order of elements. unique([3,1,2,1,3]) now returns [3,1,2].", "tokens_est": 700},
    {"id": "st10", "name": "Fix clamp swap", "content": "Swapped return values: was returning hi when value<lo and lo when value>hi. clamp(-5,0,10) now correctly returns 0 and clamp(15,0,10) returns 10.", "tokens_est": 650},
]


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except ImportError:
        return max(1, int(len(text.split()) * 1.33))


class FoldStore:
    """Minimal fold-and-restore: fold old subtasks, keep recent raw."""

    def __init__(self):
        self.folds = {}  # id -> {summary, original_hash, original_content}
        self.raw = []    # recent subtasks kept in full

    def add_subtask(self, subtask: dict):
        self.raw.append(subtask)
        if len(self.raw) > RECENT_WINDOW:
            oldest = self.raw.pop(0)
            summary = f"[FOLDED] {oldest['name']}: completed successfully."
            self.folds[oldest["id"]] = {
                "summary": summary,
                "original_hash": hashlib.md5(oldest["content"].encode()).hexdigest(),
                "original_content": oldest["content"],
            }

    def restore(self, subtask_id: str) -> str:
        """Restore a folded subtask to its original content."""
        if subtask_id in self.folds:
            return self.folds[subtask_id]["original_content"]
        return None

    def get_context(self) -> str:
        """Get the current context: fold summaries + raw recent."""
        parts = []
        for fid, fold in self.folds.items():
            parts.append(fold["summary"])
        for st in self.raw:
            parts.append(f"[RAW] {st['name']}: {st['content']}")
        return "\n".join(parts)

    def verify_restore(self, subtask_id: str) -> bool:
        """Verify restored content matches original."""
        if subtask_id not in self.folds:
            return False
        restored = self.restore(subtask_id)
        original_hash = self.folds[subtask_id]["original_hash"]
        return hashlib.md5(restored.encode()).hexdigest() == original_hash


class HardCompactor:
    """Hard compaction: summarize and discard."""

    def __init__(self):
        self.summary = ""
        self.raw = []

    def add_subtask(self, subtask: dict):
        self.raw.append(subtask)
        if len(self.raw) > RECENT_WINDOW:
            oldest = self.raw.pop(0)
            self.summary += f" {oldest['name']}: done."

    def get_context(self) -> str:
        parts = []
        if self.summary:
            parts.append(f"[SUMMARY] {self.summary.strip()}")
        for st in self.raw:
            parts.append(f"[RAW] {st['name']}: {st['content']}")
        return "\n".join(parts)

    def restore(self, subtask_id: str) -> str:
        return None  # hard compaction is irreversible


def main():
    parser = argparse.ArgumentParser(description="Experiment 39: Fold-and-Restore")
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
    print("EXPERIMENT 39: Fold-and-Restore vs Hard Compaction")
    print("=" * 65)
    print(f"Token counting: {token_label}")
    print(f"Subtasks: {len(SUBTASKS)}, Recent window: {RECENT_WINDOW}")
    print()

    # billion-context repo status
    print("billion-context repo status:")
    print("  Repo: https://github.com/ranxianglei/billion-context (real, 775+ files)")
    print("  npm test: hangs (needs running proxy or mock server)")
    print("  Paper claims: 94.2% cache hit, 70x fold ratio — authors' own, NOT verified")
    print()

    fold_store = FoldStore()
    hard_compactor = HardCompactor()
    no_compaction_parts = []

    token_trajectory = []

    for st in SUBTASKS:
        fold_store.add_subtask(st)
        hard_compactor.add_subtask(st)
        no_compaction_parts.append(f"[RAW] {st['name']}: {st['content']}")

        fold_ctx = fold_store.get_context()
        hard_ctx = hard_compactor.get_context()
        no_compact_ctx = "\n".join(no_compaction_parts)

        fold_tokens = count_tokens(fold_ctx)
        hard_tokens = count_tokens(hard_ctx)
        no_compact_tokens = count_tokens(no_compact_ctx)

        token_trajectory.append({
            "subtask": st["id"],
            "no_compaction": no_compact_tokens,
            "hard_compaction": hard_tokens,
            "fold_restore": fold_tokens,
        })

    print("Token trajectory:")
    print(f"  {'Task':<6} {'No Compact':>12} {'Hard':>12} {'Fold':>12}")
    print("  " + "-" * 44)
    for t in token_trajectory:
        print(f"  {t['subtask']:<6} {t['no_compaction']:>12,} "
              f"{t['hard_compaction']:>12,} {t['fold_restore']:>12,}")

    final = token_trajectory[-1]
    fold_vs_none = (final["no_compaction"] - final["fold_restore"]) / final["no_compaction"] * 100
    hard_vs_none = (final["no_compaction"] - final["hard_compaction"]) / final["no_compaction"] * 100
    fold_vs_hard = (final["hard_compaction"] - final["fold_restore"]) / final["hard_compaction"] * 100

    print()
    print(f"Final context tokens after {len(SUBTASKS)} subtasks:")
    print(f"  No compaction:    {final['no_compaction']:>8,} tokens")
    print(f"  Hard compaction:  {final['hard_compaction']:>8,} tokens ({hard_vs_none:.1f}% reduction)")
    print(f"  Fold-and-restore: {final['fold_restore']:>8,} tokens ({fold_vs_none:.1f}% reduction)")
    print()

    # Restore test
    print("Restore test:")
    print("-" * 40)
    restorable = 0
    restore_results = []
    for st in SUBTASKS[:5]:  # first 5 should be folded
        fold_ok = fold_store.verify_restore(st["id"])
        hard_ok = hard_compactor.restore(st["id"]) is not None
        if fold_ok:
            restorable += 1
        restore_results.append({
            "id": st["id"],
            "fold_restorable": fold_ok,
            "hard_restorable": hard_ok,
        })
        print(f"  {st['id']}: fold={'OK' if fold_ok else 'N/A'}, "
              f"hard={'OK' if hard_ok else 'LOST'}")

    print(f"\n  Fold restorable: {restorable}/{len(restore_results)}")
    print(f"  Hard restorable: 0/{len(restore_results)} (irreversible)")
    print()

    # Cache-friendliness analysis
    print("Cache-friendliness (structural analysis, not measured):")
    print("  Fold: summaries placed at head → prefix stable → cache-friendly")
    print("  Hard: full rewrite each time → prefix invalidated → cache-unfriendly")
    print()

    print(f"Conclusion ({token_label}): Fold-and-restore reduces context by")
    print(f"{fold_vs_none:.0f}% (vs {hard_vs_none:.0f}% for hard compaction) while")
    print(f"keeping {restorable}/{len(restore_results)} subtasks restorable. Hard compaction")
    print("loses all detail permanently. billion-context's production claims")
    print("(94.2% cache hit, 70x fold) are plausible but unverified by us.")

    summary = {
        "experiment": "39_fold_restore",
        "simulated": False,
        "token_method": "tiktoken" if has_tiktoken else "word_estimate",
        "subtasks": len(SUBTASKS),
        "recent_window": RECENT_WINDOW,
        "final_tokens": {
            "no_compaction": final["no_compaction"],
            "hard_compaction": final["hard_compaction"],
            "fold_restore": final["fold_restore"],
        },
        "fold_vs_none_pct": round(fold_vs_none, 2),
        "hard_vs_none_pct": round(hard_vs_none, 2),
        "fold_restorable": restorable,
        "hard_restorable": 0,
        "token_trajectory": token_trajectory,
        "billion_context_repo": "real, 775+ files, npm test hangs",
        "billion_context_claims_verified": False,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
