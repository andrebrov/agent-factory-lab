# Finding 13: Two Corrections → Skill; Prune Unused Skills

## Source

<https://x.com/educalvolpz/status/2115004827910496389>

## Idea

When the same correction is given twice, the agent should extract it into a
reusable skill (rule, template, or code pattern). Conversely, prune skills
that never prevent a correction — they're noise. This creates a self-improving
feedback loop.

## Proposal for Gwaihir

1. Track corrections (user feedback, reviewer rejections) in a log.
2. When the same type of correction appears twice, extract a skill:
   - A rule in the system prompt (e.g., "always check for nil before access")
   - A code template or snippet
   - A test pattern
3. Periodically audit skills: if a skill hasn't prevented a correction in N
   sessions, prune it.

## Experiment Design

**Goal:** Measure correction frequency over time and skill accumulation/pruning
rates.

**What can be tested in-sandbox:** Simulate a correction log, run the skill
extraction and pruning logic, and measure how the skill set evolves.

**What requires real models:** Whether LLM-extracted skills are useful and
whether they actually reduce future corrections.
