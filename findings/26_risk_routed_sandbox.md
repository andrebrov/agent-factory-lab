# Finding 26: Risk-Routed Sandbox (Combined Experiment)

## Sources

Combines findings 18–24 into a unified architecture.

## Idea

Route tasks to different isolation levels based on risk:

| Risk Level | Isolation | Use Case |
|---|---|---|
| Low (own repos, trusted) | OS sandbox (bubblewrap) | Day-to-day coding |
| Medium (third-party code) | Docker / gVisor container | Dependency installs, untrusted repos |
| High (parallel races, untrusted) | microVM (Firecracker/Lizard) | Agent races, adversarial inputs |

All tiers share:
- **Host-held secrets** with placeholder injection.
- **Egress allowlist** per tier (strictest for high-risk).
- **Booby-trap scanner** runs before any git operation.

## Proposal for Gwaihir / Landroval

1. The orchestrator classifies each task's risk level.
2. A `SandboxRouter` selects the appropriate isolation tier.
3. Secrets, egress, and scanner policies are applied per-tier.
4. Results are extracted and the sandbox is cleaned up.

## Experiment Design

**What can be tested in-sandbox:**
- Bubblewrap OS sandbox: real execution.
- Egress allowlist: protocol only; the experiment checks whether iptables rules can be listed, but does not install or verify enforcement.
- Host-held secret placeholders: real implementation.
- Booby-trap scanner: real execution against a crafted repo.
- Step-log resume: real execution.

**What requires additional infrastructure:**
- Docker containers (no Docker on this VM).
- gVisor, Firecracker, Lizard microVMs.
- Actual cloud-provider sandbox APIs.
