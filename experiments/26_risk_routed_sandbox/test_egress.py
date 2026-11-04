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
        self.assertTrue(egress["iptables_available"])
        self.assertEqual(egress["enforcement"], "protocol_only")
        line = next(line for line in output.getvalue().splitlines() if "Egress allowlist:" in line)
        self.assertIn("PROTOCOL", line)
        self.assertNotIn("REAL", line)

    def test_unavailable_listing_is_protocol_only(self):
        with patch.object(experiment.subprocess, "run", side_effect=FileNotFoundError):
            result = experiment.test_egress_allowlist()
        self.assertFalse(result["iptables_available"])
        self.assertEqual(result["enforcement"], "protocol_only")


if __name__ == "__main__":
    unittest.main()
