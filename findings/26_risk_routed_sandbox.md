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

The risk tiers above are a proposal, not implemented routing or integrated policy.
The experiment performs independent checks:

- Bubblewrap: runs one command, not a security assessment.
- Egress: attempts to list iptables rules; no enforcement is installed or verified.
- Secrets: substitutes a synthetic placeholder; no host-held secret or leak test.
- Scanner: reads back a crafted Git fsmonitor setting, not a general scan.
- Step log: reads two prewritten IDs, without a crash or actual resume.
- Docker: checks only `/usr/bin/docker --version` when that path exists;
  this does not establish daemon or container availability.
- gVisor and Firecracker: not probed; availability is unknown. Lizard and
  cloud-provider APIs are also not tested.

The reported historical run had four successful narrow checks out of eight
component entries. It does not establish integrated routing or security.

JSON compatibility: `real_components_tested` retains its legacy name but counts
successful narrow checks, not complete components. Docker `available` now means
container availability and is null (unknown), rather than the old CLI-version
result; use `version_command_succeeded` for the limited path-specific check.
gVisor and Firecracker `available` are null rather than false because neither
was probed. Consumers must handle null rather than treating it as unavailable.
