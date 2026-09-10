import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


USAGE = Path(__file__).resolve().parents[2] / "scripts" / "usage.py"


class UsageToolTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary_directory.name)
        self.store = self.base / "usage-store"

    def tearDown(self):
        self.temporary_directory.cleanup()

    def run_usage(self, *arguments):
        return subprocess.run(
            [sys.executable, str(USAGE), *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def base_event(self, **overrides):
        event = {
            "schema_version": 1,
            "event_id": "ev-0001",
            "task_id": "task-1",
            "parent_task_id": None,
            "turn_id": "turn-1",
            "occurred_at": "2026-09-10T12:00:00+00:00",
            "category": "select",
            "skill_id": "devflow",
            "source": None,
            "value": None,
            "unit": None,
            "status": "ok",
            "reason": None,
        }
        event.update(overrides)
        return event

    def write_input(self, events, name="input.jsonl"):
        path = self.base / name
        path.write_text(
            "\n".join(json.dumps(event, ensure_ascii=False) for event in events) + "\n",
            encoding="utf-8",
        )
        return path

    def enable(self):
        result = self.run_usage("enable", "--store", str(self.store))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_status_on_uninitialized_store_shows_off_without_creating(self):
        result = self.run_usage("status", "--store", str(self.store))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("off", result.stdout)
        self.assertIn("disabled", result.stdout)
        self.assertFalse(self.store.exists(), "status must not create the store")

    def test_enable_then_status_shows_on(self):
        self.enable()

        result = self.run_usage("status", "--store", str(self.store))

        self.assertEqual(result.returncode, 0)
        self.assertIn("on", result.stdout)
        self.assertTrue((self.store / "state.json").is_file())

    def test_disable_keeps_events_and_shows_off(self):
        self.enable()
        events = self.base / "events.jsonl"
        events.write_text("[]\n", encoding="utf-8")
        self.run_usage("disable", "--store", str(self.store))

        result = self.run_usage("status", "--store", str(self.store))

        self.assertEqual(result.returncode, 0)
        self.assertIn("off", result.stdout)

    def test_append_requires_enabled_store(self):
        path = self.write_input([self.base_event()])

        result = self.run_usage(
            "append", "--store", str(self.store), "--input", str(path)
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("disabled", result.stderr)
        self.assertFalse(self.store.exists(), "append must not create a disabled store")

    def test_append_writes_canonical_events(self):
        self.enable()
        path = self.write_input(
            [
                self.base_event(),
                self.base_event(
                    event_id="ev-0002",
                    category="authorization",
                    action_category="push",
                    evidence_id="grant-7",
                ),
            ]
        )

        result = self.run_usage(
            "append", "--store", str(self.store), "--input", str(path)
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        stored = [
            json.loads(line)
            for line in (self.store / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual(len(stored), 2)
        self.assertEqual(stored[1]["action_category"], "push")

    def test_append_rejects_unknown_field(self):
        self.enable()
        path = self.write_input([self.base_event(raw_dialogue="user said ...")])

        result = self.run_usage(
            "append", "--store", str(self.store), "--input", str(path)
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("raw_dialogue", result.stdout)
        events_file = self.store / "events.jsonl"
        if events_file.exists():
            self.assertNotIn(
                "ev-0001",
                events_file.read_text(encoding="utf-8"),
                "a rejected batch must not be partially stored",
            )

    def test_append_rejects_forbidden_field_names(self):
        self.enable()
        for forbidden in ("command", "prompt", "api_key", "password", "secret", "token"):
            with self.subTest(field=forbidden):
                path = self.write_input(
                    [self.base_event(**{forbidden: "x"})], name=f"bad-{forbidden}.jsonl"
                )
                result = self.run_usage(
                    "append", "--store", str(self.store), "--input", str(path)
                )
                self.assertEqual(result.returncode, 1)
                self.assertIn(forbidden, result.stdout)

    def test_append_rejects_oversized_and_mistyped_fields(self):
        self.enable()
        path = self.write_input([self.base_event(reason="r" * 300)])
        result = self.run_usage("append", "--store", str(self.store), "--input", str(path))
        self.assertEqual(result.returncode, 1)
        self.assertIn("reason", result.stdout)

        path = self.write_input([self.base_event(value="many")], name="bad-type.jsonl")
        result = self.run_usage("append", "--store", str(self.store), "--input", str(path))
        self.assertEqual(result.returncode, 1)
        self.assertIn("value", result.stdout)

    def test_append_rejects_unknown_category(self):
        self.enable()
        path = self.write_input([self.base_event(category="vibes")])

        result = self.run_usage("append", "--store", str(self.store), "--input", str(path))

        self.assertEqual(result.returncode, 1)
        self.assertIn("category", result.stdout)

    def test_append_rejects_missing_required_field(self):
        self.enable()
        event = self.base_event()
        del event["task_id"]
        path = self.write_input([event])

        result = self.run_usage("append", "--store", str(self.store), "--input", str(path))

        self.assertEqual(result.returncode, 1)
        self.assertIn("task_id", result.stdout)

    def test_nothing_appended_after_disable(self):
        self.enable()
        self.run_usage("disable", "--store", str(self.store))
        path = self.write_input([self.base_event()])

        result = self.run_usage("append", "--store", str(self.store), "--input", str(path))

        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.store / "events.jsonl").exists())

    def test_export_refuses_existing_target(self):
        self.enable()
        existing = self.base / "report.jsonl"
        existing.write_text("precious", encoding="utf-8")

        result = self.run_usage(
            "export", "--store", str(self.store), "--out", str(existing)
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("already exists", result.stderr)
        self.assertEqual(existing.read_text(encoding="utf-8"), "precious")

    def test_export_copies_stored_events(self):
        self.enable()
        path = self.write_input([self.base_event()])
        self.run_usage("append", "--store", str(self.store), "--input", str(path))
        target = self.base / "export.jsonl"

        result = self.run_usage("export", "--store", str(self.store), "--out", str(target))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        exported = [
            json.loads(line)
            for line in target.read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(len(exported), 1)
        self.assertEqual(exported[0]["event_id"], "ev-0001")

    def test_boolean_schema_version_is_rejected(self):
        self.enable()
        path = self.write_input([self.base_event(schema_version=True)])

        result = self.run_usage("append", "--store", str(self.store), "--input", str(path))

        self.assertEqual(result.returncode, 1)
        self.assertIn("schema_version", result.stdout)

    def test_control_characters_in_free_text_are_rejected(self):
        self.enable()
        path = self.write_input([self.base_event(reason="bad\x02char")])

        result = self.run_usage("append", "--store", str(self.store), "--input", str(path))

        self.assertEqual(result.returncode, 1)
        self.assertIn("reason", result.stdout)

    def test_corrupt_state_reports_input_error_without_traceback(self):
        self.enable()
        (self.store / "state.json").write_text("{broken", encoding="utf-8")

        result = self.run_usage("status", "--store", str(self.store))

        self.assertEqual(result.returncode, 2)
        self.assertIn("INPUT ERROR", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_empty_store_argument_is_rejected(self):
        result = self.run_usage("status", "--store", "")

        self.assertEqual(result.returncode, 2)
        self.assertIn("--store", result.stderr)
        self.assertFalse(Path("state.json").exists(), "must not write into the CWD")


if __name__ == "__main__":
    unittest.main()
