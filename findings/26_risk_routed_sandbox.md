# Finding 26: Risk-Routed Sandbox (Combined Experiment)

## Sources

Combines findings 18–24 into a unified architecture.

## Idea

Route tasks to different isolation levels based on risk:

| Risk Level | Isolation | Egress | Secrets | Scanner | Use case |
|---|---|---|---|---|---|
| Low | bubblewrap | permissive | environment injection | off | Own repos, trusted code |
| Medium | Docker | allowlist | placeholders | on | Third-party dependencies, unknown repos |
| High | microVM | blocked | none | on | Agent races on untrusted code |

These are proposed settings, not implemented or validated controls.

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

The historical checks are described individually; they do not establish integrated
routing or security. No aggregate of unlike probes is reported.

JSON compatibility: `real_components_tested` has been removed because it counted
only four selected checks against eight component entries. Docker `available`
is null (unknown); `version_command_succeeded` is true or false when the command
was attempted, and null when the path was absent and the command was not checked.
gVisor and Firecracker `available` are null because neither was probed.
