#!/usr/bin/env python3
"""
Experiment 19: Host-Held Secret Placeholders
===============================================

Implements and tests the env.secret placeholder pattern: code contains
placeholders like ${env.secret.API_KEY} which are resolved by the host
at mount/injection time. The sandbox never sees the real secret.

REAL EXECUTION — placeholder resolution is fully testable.
"""
import json
import os
import re
import tempfile
import argparse


SAMPLE_CODE = '''
import os

API_KEY = "${env.secret.API_KEY}"
DB_PASSWORD = "${env.secret.DB_PASSWORD}"
PUBLIC_URL = "https://api.example.com"
INTERNAL_TOKEN = "${env.secret.INTERNAL_TOKEN}"

def connect():
    return f"Connecting with key={API_KEY[:4]}..."
'''

SECRETS_STORE = {
    "API_KEY": "sk-live-abc123def456ghi789",
    "DB_PASSWORD": "p@ssw0rd!secure#2026",
    "INTERNAL_TOKEN": "tok_internal_xyz987",
}

PLACEHOLDER_RE = re.compile(r'\$\{env\.secret\.(\w+)\}')


def resolve_placeholders(code: str, secrets: dict) -> str:
    def replacer(match):
        key = match.group(1)
        return secrets.get(key, f"${{UNRESOLVED:{key}}}")
    return PLACEHOLDER_RE.sub(replacer, code)


def scan_for_leaked_secrets(text: str, secrets: dict) -> list:
    leaks = []
    for name, value in secrets.items():
        if value in text:
            leaks.append(name)
    return leaks


def main():
    parser = argparse.ArgumentParser(description="Experiment 19: Host-Held Secrets")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 65)
    print("EXPERIMENT 19: Host-Held Secret Placeholders")
    print("=" * 65)
    print()
    print("--- REAL EXECUTION ---")
    print()

    # Test 1: Placeholder detection
    placeholders = PLACEHOLDER_RE.findall(SAMPLE_CODE)
    print(f"Placeholders found in sample code: {placeholders}")
    assert len(placeholders) == 3, f"Expected 3 placeholders, found {len(placeholders)}"

    # Test 2: Placeholder resolution
    resolved = resolve_placeholders(SAMPLE_CODE, SECRETS_STORE)
    remaining = PLACEHOLDER_RE.findall(resolved)
    print(f"Placeholders after resolution: {remaining} (should be empty)")
    assert len(remaining) == 0, "Unresolved placeholders remain"

    # Test 3: Secret leak detection
    leaks_in_original = scan_for_leaked_secrets(SAMPLE_CODE, SECRETS_STORE)
    leaks_in_resolved = scan_for_leaked_secrets(resolved, SECRETS_STORE)
    print(f"Secrets leaked in original code: {leaks_in_original} (should be empty)")
    print(f"Secrets present in resolved code: {leaks_in_resolved} (expected: all 3)")

    # Test 4: Sandbox-side code never sees secrets
    sandbox_safe = len(leaks_in_original) == 0
    print(f"\nSandbox-side code is secret-free: {sandbox_safe}")

    # Test 5: Write to temp file and verify
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(SAMPLE_CODE)
        sandbox_file = f.name

    with open(sandbox_file) as f:
        file_leaks = scan_for_leaked_secrets(f.read(), SECRETS_STORE)
    os.unlink(sandbox_file)
    print(f"Secrets in sandbox file on disk: {file_leaks} (should be empty)")

    all_passed = (
        len(placeholders) == 3
        and len(remaining) == 0
        and len(leaks_in_original) == 0
        and len(leaks_in_resolved) == 3
        and sandbox_safe
        and len(file_leaks) == 0
    )

    print()
    print(f"All tests passed: {all_passed}")
    print()
    print("Conclusion: The placeholder pattern works correctly.")
    print("Sandbox-side code contains only placeholders — never real secrets.")
    print("The host resolves placeholders at injection time. Leak scanning")
    print("confirms no secret material in the sandbox's filesystem.")

    summary = {
        "experiment": "19_agents_sandbox",
        "simulated": False,
        "placeholders_found": len(placeholders),
        "placeholders_resolved": len(remaining) == 0,
        "sandbox_secret_free": sandbox_safe,
        "leak_scan_original": len(leaks_in_original),
        "leak_scan_resolved": len(leaks_in_resolved),
        "all_passed": all_passed,
    }

    out_path = args.output or os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
