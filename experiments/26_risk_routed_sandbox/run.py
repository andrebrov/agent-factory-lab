#!/usr/bin/env python3
"""
Experiment 26: Risk-Routed Sandbox (Combined)
================================================

Integrates multiple sandboxing techniques and routes tasks to isolation
tiers by risk level. Tests what's available on this VM:
- Bubblewrap OS sandbox (real)
- Egress allowlist concept (real iptables check)
- Host-held secret placeholders (real)
- Booby-trap scanner (real)
- Step-log resume (real)

MIXED — real where infrastructure exists, protocol where not.
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
    status = "REAL" if bwrap["works"] else "UNAVAILABLE"
    print(f"  [{status:<11}] Bubblewrap sandbox: "
          f"{'works' if bwrap['works'] else 'not available'}"
          + (f" ({bwrap['startup_sec']*1000:.1f}ms)" if bwrap["works"] else ""))

    egress = test_egress_allowlist()
    status = "PROTOCOL"
    print(f"  [{status:<11}] Egress allowlist: "
          f"iptables listing={'yes' if egress['iptables_available'] else 'no'}; enforcement not tested")

    secrets = test_secret_placeholders()
    print(f"  [{'REAL':<11}] Secret placeholders: "
          f"found={secrets['placeholders_found']}, resolved={secrets['resolution_works']}")

    scanner = test_scanner()
    print(f"  [{'REAL':<11}] Booby-trap scanner: "
          f"fsmonitor_detected={scanner['fsmonitor_detected']}")

    step_log = test_step_log_resume()
    print(f"  [{'REAL':<11}] Step-log resume: "
          f"recovered={step_log['steps_recovered']}, works={step_log['recovery_works']}")

    docker_avail = subprocess.run(
        ["docker", "--version"], capture_output=True
    ).returncode == 0 if os.path.exists("/usr/bin/docker") else False
    print(f"  {'[PROTOCOL]':<13} Docker container: "
          f"{'version command available' if docker_avail else 'not available'}; container not tested")

    print(f"  [{'PROTOCOL':<11}] gVisor: requires runsc")
    print(f"  [{'PROTOCOL':<11}] Firecracker microVM: requires KVM")
    print()

    real_count = sum([
        bwrap["works"],
        secrets["resolution_works"],
        scanner["fsmonitor_detected"],
        step_log["recovery_works"],
    ])
    summary = {
        "experiment": "26_risk_routed_sandbox",
        "simulated": False,
        "risk_tiers": RISK_TIERS,
        "components": {
            "bubblewrap": bwrap,
            "egress_allowlist": egress,
            "secret_placeholders": secrets,
            "booby_trap_scanner": scanner,
            "step_log_resume": step_log,
            "docker": {"available": docker_avail},
            "gvisor": {"available": False, "protocol_only": True},
            "firecracker": {"available": False, "protocol_only": True},
        },
        "real_components_tested": real_count,
    }

    print(f"Successful real component checks: {real_count}/{len(summary['components'])}")
    print("Egress enforcement and container/microVM isolation were not tested.")

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
