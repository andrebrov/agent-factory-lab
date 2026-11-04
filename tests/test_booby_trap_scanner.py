"""Focused safety regressions for the Experiment 21 demonstration fixture."""
import ast
from collections import Counter
import importlib.util
import os
from pathlib import Path
import re
import shlex
import subprocess

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "experiments/21_booby_trap_scanner/run.py"
spec = importlib.util.spec_from_file_location("booby_trap_scanner", SOURCE)
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)


def assert_safe_setup_source():
    tree = ast.parse(SOURCE.read_text())
    setup = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                 and n.name == "create_booby_trapped_repo")
    literals = [n.value for n in ast.walk(setup)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    assert not {"add", "update-index", "commit", "status"}.intersection(literals), \
        "Fixture setup must not invoke index or worktree operations"
    assert not any(re.search(r"https?://|\bcurl\b|\bwget\b|\brm\s+-|\|\s*sh\b|&&\s*sh\b", s)
                   for s in literals), "Fixture payloads must be inert"


def test_setup_source_is_inert():
    assert_safe_setup_source()


@pytest.fixture
def isolated_git(tmp_path, monkeypatch):
    # Gate runtime tests before any original setup subprocess can execute.
    assert_safe_setup_source()
    for name in list(os.environ):
        if name.startswith("GIT_"):
            monkeypatch.delenv(name)
    home = tmp_path / "home"
    home.mkdir()
    template = tmp_path / "template"
    template.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_TEMPLATE_DIR", str(template))
    return tmp_path / "repo"


def exercise(repo, create=True):
    if create:
        scanner.create_booby_trapped_repo(str(repo))
    findings = scanner.scan_repo(str(repo))
    hooks_path = next(f["value"] for f in findings if f["type"] == "core_hooksPath")
    assert Path(hooks_path) == repo / "fixture-hooks"
    assert Counter(f["type"] for f in findings) == {
        "core_fsmonitor": 1, "core_hooksPath": 1, "core_sshCommand": 1,
        "executable_hook": 2, "mcp_json_command": 1, "agents_md_injection": 2,
    }
    assert Counter(f["severity"] for f in findings) == {"critical": 2, "high": 4, "medium": 2}
    assert len(scanner.neutralize_threats(str(repo), findings)) == 6
    remaining = scanner.scan_repo(str(repo))
    assert len(remaining) == 2
    assert all(f["severity"] == "medium" and f["type"] == "agents_md_injection"
               for f in remaining)


def test_fixture_scan_and_neutralize(isolated_git):
    repo = isolated_git
    # Inspect planted values before neutralization removes them.
    scanner.create_booby_trapped_repo(str(repo))
    planted = scanner.scan_repo(str(repo))
    assert next(f["value"] for f in planted if f["type"] == "core_fsmonitor") == "experiment21-inert-fsmonitor"
    assert next(f["value"] for f in planted if f["type"] == "core_sshCommand") == "experiment21-inert-ssh"
    assert (repo / ".mcp.json").read_text() == '{"servers": [{"command": "experiment21-inert-mcp"}]}'
    exercise(isolated_git, create=False)
    config = (repo / ".git/config").read_text()
    assert str(repo / "fixture-hooks") not in config  # neutralized
    for name in ("post-checkout", "pre-commit"):
        assert (repo / ".git/hooks" / name).read_text() == "#!/bin/sh\nexit 0\n"
    for name in ("AGENTS.md", "CLAUDE.md", ".mcp.json.quarantined"):
        assert not re.search(r"https?://|\bcurl\b|\bwget\b|\brm\s+-|\|\s*sh\b",
                             (repo / name).read_text())


@pytest.mark.parametrize("reintroduce_add", [False, True])
def test_fsmonitor_never_executes(isolated_git, monkeypatch, reintroduce_add):
    marker = isolated_git.parent / "fsmonitor-called"
    callback = isolated_git.parent / "fsmonitor-canary"
    callback.write_text("#!/bin/sh\n: > " + shlex.quote(str(marker)) + "\nexit 0\n")
    callback.chmod(0o700)
    real_run = subprocess.run

    def controlled_run(args, **kwargs):
        args = list(args)
        if "core.fsmonitor" in args and "--get" not in args and "--unset" not in args:
            args[-1] = shlex.quote(str(callback))
        result = real_run(args, **kwargs)
        if reintroduce_add and "core.fsmonitor" in args and "--get" not in args and "--unset" not in args:
            # Bounded negative control: a harmless tracked candidate ensures git add
            # reads the index and invokes only our local canary.
            (isolated_git / "canary-input").write_text("safe\n")
            real_run(["git", "-C", str(isolated_git), "add", "."],
                     capture_output=True, check=True, timeout=10)
        return result

    monkeypatch.setattr(scanner.subprocess, "run", controlled_run)
    exercise(isolated_git)
    if reintroduce_add:
        with pytest.raises(AssertionError):
            assert not marker.exists(), "fsmonitor executed"
    else:
        assert not marker.exists(), "fsmonitor executed"
