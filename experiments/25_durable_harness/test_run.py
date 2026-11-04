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
    def test_valid_crash_boundaries_skip_prior_steps(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(harness.time, "sleep"):
            for value in (1, len(harness.WORKFLOW_STEPS) - 1):
                out = Path(tmp) / f"{value}.json"
                with mock.patch("sys.argv", ["run.py", "--crash-after", str(value), "--output", str(out)]), contextlib.redirect_stdout(io.StringIO()):
                    harness.main()
                result = json.loads(out.read_text())
                self.assertEqual(result["steps_skipped_on_resume"], value)
                self.assertEqual(result["steps_executed_on_resume"], len(harness.WORKFLOW_STEPS) - value)
                self.assertEqual(result["net_tokens_saved_vs_fresh"], 0)

    def test_invalid_complete_and_unterminated_records_fail_closed(self):
        for bad in ('not-json\n', '{}\n', '{"step_id":"x","status":"completed"}'):
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "steps.jsonl"
                data = '{"step_id":"a","status":"completed"}\n' + bad
                if bad.endswith('\n'):
                    data += '{"step_id":"b","status":"completed"}\n'
                path.write_text(data)
                with self.assertRaisesRegex(ValueError, "line 2"):
                    harness.StepLog(str(path))
                self.assertEqual(path.read_text(), data)

    def test_log_line_endings_and_invalid_utf8(self):
        record = b'{"step_id":"a","status":"completed"}'
        for ending in (b'\n', b'\r\n'):
            with self.subTest(ending=ending), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'steps.jsonl'
                data = record + ending
                path.write_bytes(data)
                self.assertTrue(harness.StepLog(str(path)).is_completed('a'))
                self.assertEqual(path.read_bytes(), data)
        for bad in (record + b'\r', b'\xff\n'):
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'steps.jsonl'
                data = record + b'\n' + bad
                path.write_bytes(data)
                with self.assertRaisesRegex(ValueError, 'line 2'):
                    harness.StepLog(str(path))
                self.assertEqual(path.read_bytes(), data)

    def test_crash_after_requires_interrupted_workflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            for value in (0, -1, len(harness.WORKFLOW_STEPS), len(harness.WORKFLOW_STEPS) + 1):
                with self.subTest(value=value), mock.patch("sys.argv", ["run.py", "--crash-after", str(value), "--output", str(Path(tmp) / "out.json")]), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        harness.main()
                    self.assertEqual(error.exception.code, 2)
                    self.assertFalse((Path(tmp) / "out.json").exists())

    def test_torn_log_fails_closed_with_line_number_without_modification(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "steps.jsonl"
            data = b'{"step_id":"a","status":"completed"}\n{"step_id":"b"'
            path.write_bytes(data)
            with self.assertRaisesRegex(ValueError, "line 2"):
                harness.StepLog(str(path))
            self.assertEqual(path.read_bytes(), data)

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
            self.assertEqual(result["skipped_step_tokens_on_resume"], 10500)
            self.assertEqual(result["skipped_step_tokens_pct_of_fresh"], 58.33)
            self.assertEqual(result["net_tokens_saved_vs_fresh"], 0)
            self.assertIn("legacy", result["token_metric_notes"].lower())


if __name__ == "__main__":
    unittest.main()
