# Finding 20: Isolation Tiers — OS Sandbox / gVisor / microVM

## Source

<https://x.com/pauliusztin_/status/2113246493763088553>

## Idea

Three isolation tiers, chosen by risk level:
1. **OS sandbox** (Seatbelt on macOS, Bubblewrap on Linux): lightweight,
   ~0 startup overhead, restricts syscalls and filesystem access.
2. **gVisor**: user-space kernel that intercepts syscalls; stronger than
   OS sandbox, lighter than a full VM.
3. **microVM** (Firecracker, Cloud Hypervisor): full hardware isolation;
   strongest guarantee but highest startup cost.

Keep the orchestrator local and sandbox only the tools. A single executor
interface switches between local, Docker, and Modal backends.

## Proposal for Gwaihir / Rex

1. Own repos (trusted): OS sandbox (bubblewrap) — near-zero overhead.
2. Unknown/third-party code: Docker container or gVisor.
3. Parallel races on untrusted tasks: microVM per racer.
4. One `Executor` interface with `.run(command, tier=...)`.

## Experiment Design

**What can be tested in-sandbox:** Bubblewrap OS-level sandboxing — real
execution with filesystem and network restrictions.

**What requires additional infrastructure:** gVisor (needs runsc), Firecracker
(needs KVM), Docker (not available on this VM), Modal (needs credentials).
