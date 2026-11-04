# Finding 18: Firecracker microVM per Task (Perplexity SPACE)

## Sources

- <https://x.com/perplexity_ai/status/2110778478312481167>
- <https://x.com/stretchcloud/status/2110846174651679186>

## Idea

One Firecracker microVM per task. Credentials are held outside the VM and
injected only as needed. Network egress is controlled by the host. The VM
is destroyed at task end — no state leaks between tasks.

## Proposal for Gwaihir / Landroval

1. Each coding task gets its own microVM with a minimal rootfs.
2. API keys and secrets live on the host; the VM receives only
   scoped, short-lived tokens.
3. An egress allowlist on the host firewall limits outbound traffic
   to approved domains (PyPI, npm, GitHub).
4. On completion or timeout, the VM is destroyed and the worktree
   diff is extracted.

## Experiment Design

**What can be tested:** Protocol and cost model only — Firecracker requires
KVM and a bare-metal or nested-virt host, which this sandbox VM does not
provide.

**What requires Firecracker:** Actual boot time, memory overhead, and
destruction latency measurements.
