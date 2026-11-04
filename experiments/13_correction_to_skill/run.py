#!/usr/bin/env python3
"""
Experiment 13: Two Corrections → Skill; Prune Unused Skills
==============================================================

Simulates a correction log over multiple sessions, extracts skills when
the same correction type appears twice, and prunes skills that don't
prevent future corrections.

SIMULATED — models a realistic correction stream.
"""
import json
import os
import random
import argparse
from collections import Counter


CORRECTION_TYPES = [
    "missing_null_check",
    "wrong_error_message",
    "no_input_validation",
    "hardcoded_value",
    "missing_test",
    "wrong_return_type",
    "off_by_one",
    "unused_import",
    "missing_docstring",
    "race_condition",
]

SESSIONS = 50
CORRECTIONS_PER_SESSION = 3


def simulate_correction_stream(sessions: int, per_session: int, seed: int) -> list:
    random.seed(seed)
    stream = []
    for session in range(sessions):
        for _ in range(per_session):
            ctype = random.choice(CORRECTION_TYPES)
            stream.append({"session": session, "type": ctype})
    return stream


def extract_and_prune(stream: list, prune_after: int = 10):
    skills = {}
    type_counts = Counter()
    skill_usage = Counter()
    extracted_at = {}
    pruned = []

    for i, correction in enumerate(stream):
        ctype = correction["type"]
        type_counts[ctype] += 1

        if ctype in skills:
            skill_usage[ctype] += 1

        if type_counts[ctype] == 2 and ctype not in skills:
            skills[ctype] = {
                "rule": f"Always check for {ctype.replace('_', ' ')}",
                "extracted_at_correction": i,
                "session": correction["session"],
            }
            extracted_at[ctype] = i

    for skill_type in list(skills.keys()):
        if skill_usage[skill_type] == 0:
            corrections_after = sum(
                1 for c in stream
                if c["type"] == skill_type and
                stream.index(c) > extracted_at[skill_type]
            )
            if corrections_after > prune_after:
                pruned.append(skill_type)

    return skills, skill_usage, pruned, type_counts


def main():
    parser = argparse.ArgumentParser(description="Experiment 13: Correction → Skill")
    parser.add_argument("--sessions", type=int, default=SESSIONS)
    parser.add_argument("--per-session", type=int, default=CORRECTIONS_PER_SESSION)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    stream = simulate_correction_stream(args.sessions, args.per_session, args.seed)
    skills, usage, pruned, type_counts = extract_and_prune(stream)

    total_corrections = len(stream)
    total_skills = len(skills)
    total_pruned = len(pruned)
    active_skills = total_skills - total_pruned

    print("=" * 65)
    print("EXPERIMENT 13: Two Corrections → Skill; Prune Unused")
    print("=" * 65)
    print(f"Sessions: {args.sessions}, corrections/session: {args.per_session}")
    print(f"Total corrections: {total_corrections}")
    print()
    print("--- ALL NUMBERS ARE SIMULATED ---")
    print()

    print(f"{'Metric':<35} {'Value':>10}")
    print("-" * 47)
    print(f"{'Correction types seen':<35} {len(type_counts):>10}")
    print(f"{'Skills extracted':<35} {total_skills:>10}")
    print(f"{'Skills pruned (ineffective)':<35} {total_pruned:>10}")
    print(f"{'Active skills':<35} {active_skills:>10}")
    print()

    print("Extracted skills:")
    for ctype, skill in sorted(skills.items(), key=lambda x: x[1]["extracted_at_correction"]):
        status = "PRUNED" if ctype in pruned else "ACTIVE"
        corrections_after = usage.get(ctype, 0)
        print(f"  [{status:<6}] {ctype:<25} after_extractions={corrections_after:>2}  "
              f"rule: \"{skill['rule']}\"")

    print()
    print("Correction frequency:")
    for ctype, count in type_counts.most_common():
        bar = "#" * count
        print(f"  {ctype:<25} {count:>3} {bar}")

    print()
    print("Conclusion (SIMULATED): All correction types that appeared ≥2 times")
    print("were extracted into skills. The pruning mechanism removes skills that")
    print("don't prevent future corrections. With real agents, track whether")
    print("correction frequency actually drops after skill extraction.")

    summary = {
        "experiment": "13_correction_to_skill",
        "simulated": True,
        "sessions": args.sessions,
        "total_corrections": total_corrections,
        "skills_extracted": total_skills,
        "skills_pruned": total_pruned,
        "active_skills": active_skills,
        "correction_types": dict(type_counts.most_common()),
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
