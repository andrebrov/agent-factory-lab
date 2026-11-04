import contextlib
import io
import json
import subprocess
import unittest
from unittest.mock import MagicMock, mock_open, patch

from test_egress import experiment


class ReportingTests(unittest.TestCase):
    def run_main(self, docker_result):
        output, handle = io.StringIO(), mock_open()
        with patch.object(experiment, 'test_bubblewrap', return_value={'works': True, 'startup_sec': .01}), \
             patch.object(experiment, 'test_egress_allowlist', return_value={'iptables_available': False}), \
             patch.object(experiment, 'test_secret_placeholders', return_value={'placeholders_found': 1, 'resolution_works': False}), \
             patch.object(experiment, 'test_scanner', return_value={'fsmonitor_detected': True}), \
             patch.object(experiment, 'test_step_log_resume', return_value={'steps_recovered': 0, 'recovery_works': False}), \
             patch.object(experiment.os.path, 'exists', return_value=True), \
             patch.object(experiment.subprocess, 'run', side_effect=docker_result) as run, \
             patch('sys.argv', ['run.py']), patch('argparse._', side_effect=lambda s: s), \
             patch('builtins.open', handle), contextlib.redirect_stdout(output):
            experiment.main()
        run.assert_called_once()
        return json.loads(''.join(c.args[0] for c in handle().write.call_args_list)), output.getvalue()

    def test_mixed_checks_and_unprobed_availability(self):
        result, output = self.run_main([MagicMock(returncode=0)])
        self.assertEqual(result['real_components_tested'], 2)
        self.assertIn('2/8', output)
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
