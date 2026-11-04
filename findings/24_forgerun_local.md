# Finding 24: forgerun — Local microVM per Task

## Source

<https://x.com/depak_7/status/2115134288060731597>

## Idea

Run a local microVM per task on the developer's own hardware instead of
a cloud service. Benefits:
- No cloud costs.
- Low latency (no network round-trip to a remote VM).
- Full control over the sandbox environment.
- Works offline.

Requires a machine with KVM/virtualization support.

## Proposal for Rex

1. Rex spawns a local microVM for each task using forgerun (or similar).
2. The worktree is mounted into the VM; secrets are injected by the host.
3. On completion, the VM is destroyed and the diff is extracted.
4. Combined with Finding 17 (remote VM): run forgerun on the remote VM
   host for both session durability and task isolation.

## Experiment Design

**What can be tested:** Protocol and architecture design only — local microVMs
require KVM, which this sandbox does not provide.

**What requires KVM host:** Boot time, overhead, and integration measurements.
