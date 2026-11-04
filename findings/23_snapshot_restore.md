# Finding 23: Engrams — Snapshot Idle VM, Restore on Next Prompt

## Source

<https://x.com/DanKornas/status/2112657353665552435>

## Idea

Snapshot an idle VM's full state (memory + disk) and restore it instantly
on the next prompt. Fork a VM by restoring the same snapshot into multiple
instances. This gives:
- **Fast resume:** no boot, no dependency install — restore to exact prior state.
- **Cheap branching:** fork a snapshot to try multiple approaches in parallel.
- **Billing efficiency:** paused/snapshotted VMs cost only storage, not compute.

## Proposal for Gwaihir

1. After an agent completes a task, snapshot the VM.
2. On the next task for the same project, restore from snapshot (~ms).
3. For agent races (Finding 16): fork the snapshot into N instances.

## Experiment Design

**What can be tested:** Simulate snapshot/restore with filesystem checkpoints
and measure overhead. Timing protocol for real VM snapshot/restore.

**What requires vendor services:** Actual VM memory snapshot, restore latency,
and fork-from-snapshot behavior.
