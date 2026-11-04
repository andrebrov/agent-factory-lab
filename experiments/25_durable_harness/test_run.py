import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


spec = importlib.util.spec_from_file_location("durable_harness", Path(__file__).with_name("run.py"))
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)


class ResumeSemanticsTests(unittest.TestCase):
    def test_effect_replays_if_crash_precedes_completion_record(self):
        step = {"id": "effect", "cost_tokens": 1, "time_sec": 0}
        effects = []
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "steps.jsonl")
            log = harness.StepLog(path)
            record = log.record

            def crash_before_completion(step_id, status, **kwargs):
                if status == "completed":
                    raise RuntimeError("simulated crash after effect")
                return record(step_id, status, **kwargs)

            with mock.patch.object(harness, "WORKFLOW_STEPS", [step]), \
                 mock.patch.object(harness, "execute_step", side_effect=lambda s: effects.append(s["id"]) or "ok"), \
                 mock.patch.object(log, "record", side_effect=crash_before_completion):
                with self.assertRaisesRegex(RuntimeError, "simulated crash"):
                    harness.run_workflow(log)
                self.assertEqual(effects, ["effect"])
                resumed_log = harness.StepLog(path)
                self.assertFalse(resumed_log.is_completed("effect"))
                result = harness.run_workflow(resumed_log)
                self.assertEqual(effects, ["effect", "effect"])
                self.assertEqual(result["executed"], 1)
                self.assertEqual(harness.run_workflow(harness.StepLog(path))["skipped"], 1)
                self.assertEqual(effects, ["effect", "effect"])

    def test_output_discloses_replay_and_idempotency(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "results.json"
            stdout = io.StringIO()
            with mock.patch("sys.argv", ["run.py", "--output", str(out)]), \
                 mock.patch.object(harness.time, "sleep"), contextlib.redirect_stdout(stdout):
                harness.main()
            text = stdout.getvalue().lower()
            self.assertIn("at-least-once", text)
            self.assertIn("idempoten", text)
            self.assertIn("replay", text)
            self.assertNotIn("provides exactly-once", text)
            result = json.loads(out.read_text())
            self.assertIn("replay", json.dumps(result).lower())
            self.assertIn("not total crash+resume savings", text)
            self.assertEqual(result["fresh_run_tokens"], 18000)
            self.assertEqual(result["crash_resume_tokens"], 18000)
            self.assertEqual(result["tokens_saved"], 10500)
            self.assertEqual(result["tokens_saved_pct"], 58.33)


if __name__ == "__main__":
    unittest.main()
