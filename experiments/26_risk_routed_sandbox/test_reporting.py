import contextlib
import io
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from test_egress import experiment


class ReportingTests(unittest.TestCase):
    def run_main(self, docker_result, docker_exists=True):
        output, handle = io.StringIO(), mock_open()
        with patch.object(experiment, 'test_bubblewrap', return_value={'works': True, 'startup_sec': .01}), \
             patch.object(experiment, 'test_egress_allowlist', return_value={'iptables_available': False}), \
             patch.object(experiment, 'test_secret_placeholders', return_value={'placeholders_found': 1, 'resolution_works': False}), \
             patch.object(experiment, 'test_scanner', return_value={'fsmonitor_detected': True}), \
             patch.object(experiment, 'test_step_log_resume', return_value={'steps_recovered': 0, 'recovery_works': False}), \
             patch.object(experiment.os.path, 'exists', return_value=docker_exists), \
             patch.object(experiment.subprocess, 'run', side_effect=docker_result) as run, \
             patch('sys.argv', ['run.py']), patch('argparse._', side_effect=lambda s: s), \
             patch('builtins.open', handle), contextlib.redirect_stdout(output):
            experiment.main()
        self.assertEqual(run.call_count, 1 if docker_exists else 0)
        return json.loads(''.join(c.args[0] for c in handle().write.call_args_list)), output.getvalue()

    def test_mixed_checks_and_unprobed_availability(self):
        result, output = self.run_main([MagicMock(returncode=0)])
        self.assertNotIn('real_components_tested', result)
        self.assertNotIn('2/8', output)
        self.assertTrue(result['components']['docker']['version_command_succeeded'])
        self.assertIsNone(result['components']['docker']['available'])
        self.assertIsNone(result['components']['gvisor']['available'])
        self.assertIsNone(result['components']['firecracker']['available'])
        self.assertIn('not tested', output.lower())
        self.assertNotIn('[REAL       ] Secret', output)

    def test_docker_version_nonzero_and_timeout_are_not_availability_verdicts(self):
        for outcome in ([MagicMock(returncode=1)], subprocess.TimeoutExpired('docker', 5), FileNotFoundError()):
            with self.subTest(outcome=outcome):
                result, output = self.run_main(outcome)
                self.assertFalse(result['components']['docker']['version_command_succeeded'])
                self.assertIsNone(result['components']['docker']['available'])
                self.assertIn('container not tested', output)

    def test_missing_docker_path_is_not_a_failed_command(self):
        result, output = self.run_main([], docker_exists=False)
        self.assertIsNone(result['components']['docker']['version_command_succeeded'])
        self.assertIn('not checked', output)

    def test_documented_tier_policies_match_proposal(self):
        doc = (Path(__file__).resolve().parents[2] / 'findings/26_risk_routed_sandbox.md').read_text()
        rows = {line.split('|')[1].strip().lower(): [cell.strip() for cell in line.split('|')[2:6]]
                for line in doc.splitlines() if line.startswith('|')}
        display = {'env_inject': 'environment injection', 'placeholder': 'placeholders'}
        for tier, config in experiment.RISK_TIERS.items():
            expected = [config['isolation'], config['egress'],
                        display.get(config['secrets'], config['secrets']),
                        'on' if config['scanner'] else 'off']
            self.assertEqual([value.lower() for value in rows[tier]], expected)
