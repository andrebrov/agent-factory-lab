import contextlib
import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch


spec = importlib.util.spec_from_file_location("experiment_26", Path(__file__).with_name("run.py"))
assert spec is not None and spec.loader is not None
experiment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiment)


class EgressReportingTests(unittest.TestCase):
    def test_successful_listing_does_not_claim_enforcement(self):
        output = io.StringIO()
        handle = mock_open()
        with patch.object(experiment.subprocess, "run", return_value=MagicMock(returncode=0)) as run, \
             patch.object(experiment, "test_bubblewrap", return_value={"works": False}), \
             patch.object(experiment, "test_secret_placeholders", return_value={"placeholders_found": 0, "resolution_works": False}), \
             patch.object(experiment, "test_scanner", return_value={"fsmonitor_detected": False}), \
             patch.object(experiment, "test_step_log_resume", return_value={"steps_recovered": 0, "recovery_works": False}), \
             patch.object(experiment.os.path, "exists", return_value=False), \
             patch("sys.argv", ["run.py"]), patch("builtins.open", handle), contextlib.redirect_stdout(output):
            experiment.main()
        run.assert_called_once_with(["sudo", "iptables", "-L", "-n"], capture_output=True, text=True, timeout=5)
        result = json.loads(''.join(call.args[0] for call in handle().write.call_args_list))
        egress = result["components"]["egress_allowlist"]
        self.assertEqual(egress["iptables_listing_status"], "succeeded")
        self.assertEqual(egress["enforcement"], "protocol_only")
        line = next(line for line in output.getvalue().splitlines() if "Egress allowlist:" in line)
        self.assertIn("PROTOCOL", line)
        self.assertNotIn("REAL", line)

    def test_no_misleading_aggregate_of_selected_checks(self):
        for works in (False, True):
            with self.subTest(works=works):
                output = io.StringIO()
                handle = mock_open()
                with patch.object(experiment, "test_bubblewrap", return_value={"works": works, "startup_sec": 0}), \
                     patch.object(experiment, "test_egress_allowlist", return_value={"iptables_listing_status": "succeeded", "enforcement": "protocol_only"}), \
                     patch.object(experiment, "test_secret_placeholders", return_value={"placeholders_found": 1, "resolution_works": works}), \
                     patch.object(experiment, "test_scanner", return_value={"fsmonitor_detected": works}), \
                     patch.object(experiment, "test_step_log_resume", return_value={"steps_recovered": 2, "recovery_works": works}), \
                     patch.object(experiment.os.path, "exists", return_value=False), \
                     patch("sys.argv", ["run.py"]), patch("builtins.open", handle), contextlib.redirect_stdout(output):
                    experiment.main()
                result = json.loads(''.join(call.args[0] for call in handle().write.call_args_list))
                self.assertEqual(len(result["components"]), 8)
                self.assertNotIn("real_components_tested", result)
                self.assertNotIn("Successful real component checks", output.getvalue())
                self.assertNotIn("all work correctly", output.getvalue())
                self.assertNotIn("protocol-only: 7/7", output.getvalue())

    def test_probe_outcomes_do_not_claim_availability(self):
        cases = [(MagicMock(returncode=0), None, "succeeded"),
                 (MagicMock(returncode=1), None, "failed"),
                 (None, FileNotFoundError(), "not_found"),
                 (None, experiment.subprocess.TimeoutExpired("sudo", 5), "timed_out")]
        for response, error, status in cases:
            with self.subTest(status=status), patch.object(experiment.subprocess, "run", return_value=response, side_effect=error):
                result = experiment.test_egress_allowlist()
                self.assertEqual(result["iptables_listing_status"], status)
                self.assertNotIn("iptables_available", result)

    def test_bubblewrap_command_outcomes(self):
        cases = [(MagicMock(returncode=0, stdout="sandboxed"), None, "succeeded", True),
                 (MagicMock(returncode=1, stdout=""), None, "failed", False),
                 (None, FileNotFoundError(), "not_found", None),
                 (None, experiment.subprocess.TimeoutExpired("bwrap", 5), "timed_out", None)]
        for response, error, status, works in cases:
            with self.subTest(status=status), patch.object(experiment.subprocess, "run", return_value=response, side_effect=error):
                result = experiment.test_bubblewrap()
                self.assertEqual(result["command_status"], status)
                self.assertIs(result["works"], works)
                self.assertNotIn("available", result)

    def test_bubblewrap_timeout_is_not_missing_binary(self):
        with patch.object(experiment.subprocess, "run", side_effect=experiment.subprocess.TimeoutExpired("bwrap", 5)):
            result = experiment.test_bubblewrap()
        self.assertEqual(result["command_status"], "timed_out")
        self.assertNotIn("available", result)
        self.assertIsNone(result["works"])

    def test_unavailable_listing_is_protocol_only(self):
        with patch.object(experiment.subprocess, "run", side_effect=FileNotFoundError):
            result = experiment.test_egress_allowlist()
        self.assertEqual(result["iptables_listing_status"], "not_found")
        self.assertEqual(result["enforcement"], "protocol_only")


if __name__ == "__main__":
    unittest.main()
