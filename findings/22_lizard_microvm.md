# Finding 22: Lizard — Fast microVM Boot and Per-Second Billing

## Source

<https://x.com/LizardBuild/status/2111492342754537792>

## Idea

Lizard claims ~238 ms microVM boot time, 100 parallel VMs, per-second
billing, and free while paused. This makes microVMs practical for
short-lived coding tasks where traditional VM startup (30–60s) would
dominate the task time.

**Note:** These are Lizard's own claimed benchmarks, not independently
verified.

## Proposal for Landroval

1. Use Lizard (or equivalent fast-microVM provider) for parallel agent
   races (Finding 16) and untrusted-code execution.
2. Per-second billing means short tasks (< 30s) cost almost nothing.
3. Pause VMs between tasks instead of destroying them (amortizes boot).

## Experiment Design

**What can be tested:** Cost model comparing per-second vs per-minute billing
for typical task durations, and a timing protocol for when Lizard access is
available.

**What requires Lizard:** Actual boot time verification and parallel VM
scaling benchmarks.
