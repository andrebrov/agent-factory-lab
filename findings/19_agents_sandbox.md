# Finding 19: agents-sandbox — Reusable microVM with Host-Held Secrets

## Source

<https://x.com/DanKornas/status/2114427118947807236>

## Idea

One reusable microVM per project/agent. Secrets are held on the host with
`env.secret` placeholders injected at runtime. The VM has scoped filesystem
mounts (only the project worktree) and scoped network (egress allowlist).

Key difference from Perplexity SPACE: the VM is **reused** across tasks on
the same project rather than destroyed after each task, reducing startup
overhead.

## Proposal for Gwaihir

1. Each project gets a persistent microVM that boots once and handles
   multiple tasks.
2. `env.secret` placeholders in code are resolved by the host at mount time.
3. Filesystem mounts are scoped: the VM sees only its worktree plus
   read-only system dependencies.
4. Network is scoped: egress allowlist per project.

## Experiment Design

**What can be tested:** Host-held secret placeholder resolution and egress
allowlist enforcement (both testable without microVMs).

**What requires microVMs:** Actual reusable VM lifecycle, mount scoping,
and boot-amortization measurements.
