# Finding 17 (Extra): Rex on a Remote Linux VM for Session Durability

## Source

<https://x.com/denCual/status/2115801768571621812>

## Idea

Run Rex on a remote Linux VM (cloud instance or home server) instead of the
developer's laptop. Sessions survive the laptop sleeping, network drops, and
reboots. The developer connects via SSH/tmux/mosh and picks up where they
left off.

## Proposal for Rex / Landroval

1. Rex runs inside a persistent tmux session on a remote VM.
2. The developer connects via `mosh` (handles roaming/sleep) or SSH + tmux
   attach.
3. Long-running tasks (test suites, builds) continue even when the laptop
   is closed.
4. Combined with herdr-core session persistence (Finding 5), this provides
   both process durability and state durability.

## Experiment Design

**Goal:** Measure session survival rate across simulated disconnections and
reconnections.

**What can be tested in-sandbox:** Simulate disconnect/reconnect cycles with
tmux sessions and verify process and state continuity.

**What requires real Rex:** Actual Rex running on a remote VM with network
interruption testing.
