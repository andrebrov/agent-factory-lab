"""Local regression checks for the finite Experiment 10 controls."""
import importlib.util
import json
import os
import re
import subprocess
import sys
import venv
from types import SimpleNamespace

import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('stop_hook', ROOT / 'experiments/10_stop_hook/run.py')
hook = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hook)


def test_real_controls():
    for filename, passed, failed in [('mathlib.py', 0, 10), ('mathlib_fixed.py', 10, 0)]:
        result = hook.run_checks(filename)
        assert (result['passed'], result['failed'], result['errors'], result['skipped']) == (passed, failed, 0, 0)


@pytest.mark.parametrize('report,code,valid', [
    ('<testsuite tests="999"><testcase/></testsuite>', 0, True),
    ('<testsuite><testcase><failure message="assert 0"/></testcase></testsuite>', 1, True),
    (None, 0, False), ('broken', 0, False), ('', 0, False),
    ('<testsuite tests="10"/>', 0, False),
    ('<unexpected><testcase/></unexpected>', 0, False),
    ('<testsuite><testcase><failure/><error/></testcase></testsuite>', 1, False),
    ('<testsuite><testcase><skipped/></testcase></testsuite>', 0, False),
    ('<testsuite><testcase><error/></testcase></testsuite>', 1, False),
    ('<testsuite><testcase><failure message="ValueError"/></testcase></testsuite>', 1, True),
    ('<testsuite><testcase/></testsuite>', 1, False),
    ('<testsuite><testcase><failure message="assert 0"/></testcase></testsuite>', 0, False),
    *[('<testsuite><testcase/></testsuite>', code, False) for code in (2, 3, 4, 5, -9)],
])
def test_reports_through_run_checks(monkeypatch, report, code, valid):
    def run(command, **kwargs):
        assert '--junitxml=report.xml' in command
        if report is not None:
            (Path(kwargs['cwd']) / 'report.xml').write_text(report)
        return SimpleNamespace(returncode=code, stdout=' PASSED FAILED ' * 30, stderr='')
    monkeypatch.setattr(hook.subprocess, 'run', run)
    if valid:
        result = hook.run_checks('mathlib.py')
        assert result['passed'] + result['failed'] == 1
    else:
        with pytest.raises(RuntimeError):
            hook.run_checks('mathlib.py')


@pytest.mark.parametrize('source', [
    'def test_bad(: pass',
    'import absent_stop_hook_module',
    'import pytest\n@pytest.mark.skip\ndef test_skip(): pass',
    '# no tests',
    'import pytest\n@pytest.fixture(autouse=True)\ndef broken(): raise ValueError("setup")\ndef test_ok(): pass',
    'def pytest_sessionstart(session): raise RuntimeError("internal")',
])
def test_real_failure_runs(tmp_path, monkeypatch, source):
    (tmp_path / 'mathlib.py').write_text('')
    internal = source.startswith('def pytest_sessionstart')
    (tmp_path / 'test_mathlib.py').write_text('def test_ok(): pass' if internal else source)
    if internal:
        # run_checks copies only the test and module, so load the plugin from the test directory.
        (tmp_path / 'plugin.py').write_text(source)
        monkeypatch.setenv('PYTEST_PLUGINS', 'plugin')
        monkeypatch.setenv('PYTHONPATH', str(tmp_path))
    monkeypatch.setattr(hook, 'SAMPLE_DIR', tmp_path)
    with pytest.raises(RuntimeError):
        hook.run_checks('mathlib.py')


@pytest.mark.parametrize('wrong', ['buggy', 'fixed'])
def test_control_mismatch_no_artifact(tmp_path, monkeypatch, capsys, wrong):
    out = tmp_path / 'results.json'
    def checks(filename):
        passed = 0 if filename == 'mathlib.py' else 10
        failed = 10 - passed
        if (wrong == 'buggy') == (filename == 'mathlib.py'):
            passed, failed = 1, 9
        return dict(passed=passed, failed=failed, errors=0, skipped=0,
                    exit_code=int(bool(failed)), all_pass=not failed)
    monkeypatch.setattr(hook, 'run_checks', checks)
    monkeypatch.setattr(sys, 'argv', ['run.py', '--output', str(out)])
    with pytest.raises(RuntimeError, match='control mismatch'):
        hook.main()
    assert not out.exists()
    assert 'Conclusion:' not in capsys.readouterr().out


def test_cli_success(tmp_path):
    out = tmp_path / 'results.json'
    result = subprocess.run([sys.executable, str(SPEC.origin), '--output', str(out)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    data = json.loads(out.read_text())
    assert data['buggy_scenario']['tests_failed'] == 10
    assert data['fixed_scenario']['tests_passed'] == 10
    assert not any('reopen' in key for key in data)
    assert 'frequency was not measured' in result.stdout


def test_no_pytest_cli_and_runner_refusal(tmp_path):
    envdir = tmp_path / 'env'
    venv.EnvBuilder(with_pip=False).create(envdir)
    python = envdir / 'bin/python'
    out = tmp_path / 'results.json'
    result = subprocess.run([str(python), str(SPEC.origin), '--output', str(out)], capture_output=True, text=True)
    assert result.returncode != 0
    assert 'No module named pytest' in result.stderr
    assert 'Conclusion:' not in result.stdout
    assert not out.exists()
    # Only the prerequisite interpreter can execute; all later commands are tripwires.
    bindir = tmp_path / 'bin'
    bindir.mkdir()
    log = tmp_path / 'calls'
    for name in ('python3', 'pip3', 'pip', 'python', 'tmux', 'sudo'):
        stub = bindir / name
        stub.write_text('#!/bin/bash\necho "$0 $*" >> "$CALL_LOG"\nexit 91\n')
        stub.chmod(0o755)
    result = subprocess.run(['/bin/bash', str(ROOT / 'run_all.sh')],
                            env={**os.environ, 'PATH': str(bindir) + ':/usr/bin:/bin', 'CALL_LOG': str(log)},
                            capture_output=True, text=True)
    assert result.returncode != 0
    assert 'python3 -m pip install pytest' in result.stderr
    assert len(log.read_text().splitlines()) == 1
    assert '-c import pytest' in log.read_text()


@pytest.mark.parametrize('event', ['pull_request', 'push'])
def test_workflow_paths_cover_public_claims(event):
    # Bound each match by indentation so other events/jobs cannot supply paths.
    # This guard deliberately requires the workflow's current block-list format.
    workflow = (ROOT / '.github/workflows/stop-hook.yml').read_text()
    triggers = re.findall(r'^on:\n((?: +[^\n]*\n|\n)*)', workflow, re.MULTILINE)
    assert len(triggers) == 1
    sections = re.findall(
        rf'^  {event}:\n((?: {{4,}}[^\n]*\n|\n)*)', triggers[0], re.MULTILINE)
    assert len(sections) == 1
    filters = re.findall(
        r'^    paths:\n((?: {6,}[^\n]*\n|\n)*)', sections[0], re.MULTILINE)
    assert len(filters) == 1
    paths = set()
    for line in filters[0].splitlines():
        entry = re.fullmatch(r"      - '([^']+)'", line)
        assert entry is not None, f'Unsupported path entry: {line!r}'
        paths.add(entry.group(1))
    required = {'REPORT.md', 'docs/index.html', 'docs/llms-full.txt',
                'findings/10_stop_hook.md'}
    assert required <= paths, f'{event} paths missing: {sorted(required - paths)}'


def test_public_claims():
    for name in ('REPORT.md', 'docs/index.html', 'docs/llms-full.txt', 'findings/10_stop_hook.md'):
        text = (ROOT / name).read_text()
        assert '0% reopen rate' not in text
        assert '35% to 0%' not in text
        assert '35% (estimated without hook)' not in text
        assert 'frequency was not measured' in text or 'does not measure reopening frequency' in text


@pytest.mark.parametrize('wrong_file', ['mathlib.py', 'mathlib_fixed.py'])
def test_cli_control_failure(tmp_path, wrong_file):
    # Reuse the existing fixtures; override only the control under test.
    for name in ('mathlib.py', 'mathlib_fixed.py', 'test_mathlib.py'):
        (tmp_path / name).write_text((hook.SAMPLE_DIR / name).read_text())
    replacement = 'mathlib_fixed.py' if wrong_file == 'mathlib.py' else 'mathlib.py'
    (tmp_path / wrong_file).write_text((hook.SAMPLE_DIR / replacement).read_text())
    out = tmp_path / 'result.json'
    code = (
        'import runpy,sys; from pathlib import Path; '
        f'ns=runpy.run_path({str(SPEC.origin)!r}); '
        f'ns["main"].__globals__["SAMPLE_DIR"]=Path({str(tmp_path)!r}); '
        f'sys.argv=["run.py","--output",{str(out)!r}]; ns["main"]()'
    )
    result = subprocess.run([sys.executable, '-O', '-c', code], capture_output=True, text=True)
    assert result.returncode != 0
    assert 'control mismatch' in result.stderr
    assert 'Conclusion:' not in result.stdout
    assert not out.exists()
