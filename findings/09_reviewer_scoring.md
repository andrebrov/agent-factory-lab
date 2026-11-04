# Finding 9: Score the Reviewer Against Past Incidents

## Source

<https://x.com/i/status/2114604912520921136>

## Idea

Evaluate the AI reviewer's effectiveness by scoring it against historical
data: past incidents, reverts, and known-clean PRs. A reviewer that flags
real issues (caught in incidents) and ignores clean code is high-quality;
one that misses real bugs or raises false alarms on clean PRs is not.

## Proposal for Gwaihir

1. Maintain a scoring dataset: a set of PRs with known outcomes (reverted,
   caused incident, shipped cleanly).
2. Periodically run the reviewer against this dataset and compute:
   - **Catch rate:** What fraction of bad PRs does it flag?
   - **False-alarm rate:** What fraction of clean PRs does it wrongly flag?
3. Use these scores to calibrate reviewer behavior — e.g., adjust confidence
   thresholds, swap reviewer models, or weight reviewer feedback.

## Experiment Design

**Goal:** Measure catch rate and false-alarm rate on a synthetic PR corpus.

**What can be tested in-sandbox:** Build a corpus of known-good and
known-bad diffs from the sample codebase and score a simulated reviewer.

**What requires real models:** Running an actual LLM reviewer against the
corpus to measure real catch and false-alarm rates.
