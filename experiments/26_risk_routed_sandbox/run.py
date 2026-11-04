#!/usr/bin/env python3
"""
Experiment 26: Risk-Routed Sandbox (Combined)
================================================

Defines proposed risk tiers and runs independent, narrow component checks.
It does not implement routing or integrate security controls. The checks do
not validate egress enforcement, secret isolation, a general scanner, crash
recovery, or container/microVM isolation.
"""
import json
import os
import re
import subprocess
import time
import tempfile
import argparse
from pathlib import Path


RISK_TIERS = {
    "low": {
        "isolation": "bubblewrap",
        "egress": "permissive",
        "secrets": "env_inject",
        "scanner": False,
        "example": "Own repo, trusted code",
    },
    "medium": {
        "isolation": "docker",
        "egress": "allowlist",
        "secrets": "placeholder",
        "scanner": True,
        "example": "Third-party dependency, unknown repo",
    },
    "high": {
        "isolation": "microvm",
        "egress": "blocked",
        "secrets": "none",
        "scanner": True,
        "example": "Agent race on untrusted code",
    },
}


def test_bubblewrap() -> dict:
    """Test bubblewrap sandbox (real)."""
    try:
        base_args = [
            "--ro-bind", "/usr", "/usr",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind", "/lib64", "/lib64",
            "--ro-bind", "/bin", "/bin",
            "--ro-bind", "/sbin", "/sbin",
            "--proc", "/proc",
            "--dev", "/dev",
            "--tmpfs", "/tmp",
            "--unshare-all",
            "--die-with-parent",
        ]

        start = time.monotonic()
        r = subprocess.run(
            ["bwrap"] + base_args + ["echo", "sandboxed"],
            capture_output=True, text=True, timeout=5,
        )
        elapsed = time.monotonic() - start
        return {
            "available": True,
            "works": r.returncode == 0,
            "startup_sec": round(elapsed, 4),
            "output": r.stdout.strip(),
        }
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {"available": False, "works": False, "startup_sec": 0}


def test_egress_allowlist() -> dict:
    """Probe whether iptables rules can be listed; do not enforce egress."""
    try:
        r = subprocess.run(["sudo", "iptables", "-L", "-n"], capture_output=True, text=True, timeout=5)
        has_iptables = r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        has_iptables = False

    allowlist = ["pypi.org", "registry.npmjs.org", "github.com", "api.anthropic.com"]
    return {
        "iptables_available": has_iptables,
        "allowlist": allowlist,
        "enforcement": "protocol_only",
    }


def test_secret_placeholders() -> dict:
    """Test secret placeholder resolution (real)."""
    code = 'KEY = "${env.secret.TEST_KEY}"'
    pattern = re.compile(r'\$\{env\.secret\.(\w+)\}')
    placeholders = pattern.findall(code)
    resolved = pattern.sub(lambda m: "sk-live-redacted", code)
    return {
        "placeholders_found": len(placeholders),
        "resolution_works": "${env.secret" not in resolved,
    }


def test_scanner() -> dict:
    """Quick booby-trap scan (real)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(["git", "init", tmpdir], capture_output=True, check=True)
        subprocess.run(
            ["git", "-C", tmpdir, "config", "core.fsmonitor", "echo pwned"],
            capture_output=True, check=True,
        )
        r = subprocess.run(
            ["git", "-C", tmpdir, "config", "--get", "core.fsmonitor"],
            capture_output=True, text=True,
        )
        detected = r.returncode == 0 and "pwned" in r.stdout
        return {"fsmonitor_detected": detected}


def test_step_log_resume() -> dict:
    """Quick step-log resume test (real)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        log_path = f.name
        f.write('{"step_id":"s1","status":"completed","result":"ok"}\n')
        f.write('{"step_id":"s2","status":"completed","result":"ok"}\n')

    with open(log_path) as f:
        completed = [json.loads(line)["step_id"] for line in f if "completed" in line]
    os.unlink(log_path)

    return {
        "steps_recovered": len(completed),
        "recovery_works": completed == ["s1", "s2"],
    }


def main():
    parser = argparse.ArgumentParser(description="Experiment 26: Risk-Routed Sandbox")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 26: Risk-Routed Sandbox (Combined)")
    print("=" * 65)
    print()

    print("Risk tiers:")
    for level, config in RISK_TIERS.items():
        print(f"  {level:<8} isolation={config['isolation']:<12} egress={config['egress']:<12} "
              f"scanner={config['scanner']}")
    print()

    print("Component tests:")
    print("-" * 50)

    bwrap = test_bubblewrap()
    status = "CHECK PASS" if bwrap["works"] else "CHECK FAIL"
    print(f"  [{status:<11}] Bubblewrap sandbox: "
          f"{'works' if bwrap['works'] else 'command did not succeed'}"
          + (f" ({bwrap['startup_sec']*1000:.1f}ms)" if bwrap["works"] else ""))

    egress = test_egress_allowlist()
    status = "PROTOCOL"
    print(f"  [{status:<11}] Egress allowlist: "
          f"iptables listing={'yes' if egress['iptables_available'] else 'no'}; enforcement not tested")

    secrets = test_secret_placeholders()
    print(f"  [{'CHECK':<11}] Placeholder substitution (synthetic): "
          f"found={secrets['placeholders_found']}, resolved={secrets['resolution_works']}")

    scanner = test_scanner()
    print(f"  [{'CHECK':<11}] Git fsmonitor config readback: "
          f"fsmonitor_detected={scanner['fsmonitor_detected']}")

    step_log = test_step_log_resume()
    print(f"  [{'CHECK':<11}] Step-log readback: "
          f"recovered={step_log['steps_recovered']}, works={step_log['recovery_works']}")

    # This checks only a specific CLI path and version command, not the daemon.
    docker_version_ok = None
    if os.path.exists("/usr/bin/docker"):
        try:
            docker_version_ok = subprocess.run(
                ["/usr/bin/docker", "--version"], capture_output=True, timeout=5
            ).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            docker_version_ok = False
    print(f"  {'[PROTOCOL]':<13} Docker: /usr/bin/docker version command "
          f"{'not checked' if docker_version_ok is None else 'succeeded' if docker_version_ok else 'failed'}; container not tested")
    print(f"  {'[PROTOCOL]':<13} gVisor: availability unknown; not tested")
    print(f"  {'[PROTOCOL]':<13} Firecracker: availability unknown; not tested")
    print()

    summary = {
        "experiment": "26_risk_routed_sandbox",
        "simulated": False,
        "scope": "Independent narrow checks only; no integrated routing, egress enforcement, secret isolation, general scanning, crash recovery, or container/microVM isolation validated.",
        "risk_tiers": RISK_TIERS,
        "components": {
            "bubblewrap": bwrap,
            "egress_allowlist": egress,
            "secret_placeholders": secrets,
            "booby_trap_scanner": scanner,
            "step_log_resume": step_log,
            "docker": {"available": None, "version_command_succeeded": docker_version_ok,
                       "version_probe_path": "/usr/bin/docker", "protocol_only": True},
            "gvisor": {"available": None, "protocol_only": True},
            "firecracker": {"available": None, "protocol_only": True},
        },
    }

    print("Independent checks only; routing, egress enforcement, secret isolation, general scanning, crash recovery, and container/microVM isolation were not tested.")

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
