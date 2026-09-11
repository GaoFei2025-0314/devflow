import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


USAGE = Path(__file__).resolve().parents[2] / "scripts" / "usage.py"


class UsageReportTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary_directory.name)
        self.store = self.base / "store"

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

    def event(self, **overrides):
        base = {
            "schema_version": 1,
            "event_id": "ev-1",
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
        base.update(overrides)
        return base

    def fill_store(self, events):
        self.run_usage("enable", "--store", str(self.store))
        path = self.base / "input.jsonl"
        path.write_text(
            "\n".join(json.dumps(event, ensure_ascii=False) for event in events) + "\n",
            encoding="utf-8",
        )
        result = self.run_usage("append", "--store", str(self.store), "--input", str(path))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def report(self, name="report.json", store=None):
        output = self.base / name
        result = self.run_usage(
            "report", "--store", str(store or self.store), "--out", str(output)
        )
        return result, output

    def test_report_requires_existing_store(self):
        result, _ = self.report()

        self.assertEqual(result.returncode, 2)
        self.assertIn("INPUT ERROR", result.stderr)

    def test_report_refuses_existing_output(self):
        self.fill_store([self.event()])
        target = self.base / "precious.json"
        target.write_text("keep", encoding="utf-8")

        result = self.run_usage(
            "report", "--store", str(self.store), "--out", str(target)
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("already exists", result.stderr)
        self.assertEqual(target.read_text(encoding="utf-8"), "keep")

    def test_exact_duplicates_collapse_and_are_counted(self):
        event = self.event()
        self.fill_store([event, dict(event)])

        result, output = self.report()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["events_input"]["total"], 2)
        self.assertEqual(report["events_input"]["unique"], 1)
        self.assertEqual(report["deduplication"]["exact_duplicates_collapsed"], 1)

    def test_conflicting_identity_is_listed_and_excluded(self):
        first = self.event(event_id="ev-x")
        conflicting = self.event(event_id="ev-x", status="failed", reason="other")
        third = self.event(event_id="ev-y", category="result")
        self.fill_store([first, conflicting, third])

        result, output = self.report()

        self.assertEqual(result.returncode, 0)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(len(report["conflicts"]), 1)
        self.assertEqual(report["conflicts"][0]["event_id"], "ev-x")
        self.assertIn("status", report["conflicts"][0]["differing_fields"])
        self.assertEqual(report["events_input"]["unique"], 2)
        self.assertEqual(report["events_input"]["excluded_conflicting"], 1)
        self.assertEqual(report["counts_by_category"], {"result": 1})

    def test_task_grouping_separates_parent_and_subagent_tasks(self):
        self.fill_store(
            [
                self.event(event_id="a", task_id="main"),
                self.event(
                    event_id="b",
                    task_id="sub",
                    parent_task_id="main",
                    category="request",
                ),
            ]
        )

        result, output = self.report()

        self.assertEqual(result.returncode, 0)
        report = json.loads(output.read_text(encoding="utf-8"))
        groups = {group["task_id"]: group for group in report["task_groups"]}
        self.assertIn("main", groups)
        self.assertIn("sub", groups)
        self.assertEqual(groups["sub"]["parent_task_id"], "main")
        self.assertEqual(groups["sub"]["is_subagent_task"], True)

    def test_applicability_counts_explicit_states_and_treats_absence_as_unknown(self):
        self.fill_store(
            [
                self.event(event_id="1", task_id="applicable", category="select"),
                self.event(event_id="2", task_id="applicable", category="result"),
                self.event(event_id="3", task_id="explicit-na", category="select",
                           status="not_applicable"),
                self.event(event_id="4", task_id="explicit-na", category="result",
                           status="not_applicable"),
                self.event(event_id="5", task_id="unknown-task", category="result",
                           status="unknown"),
            ]
        )

        result, output = self.report()

        self.assertEqual(result.returncode, 0)
        report = json.loads(output.read_text(encoding="utf-8"))
        applicability = report["applicability"]
        self.assertEqual(applicability["applicable_tasks"], 1)
        self.assertEqual(applicability["not_applicable_tasks"], 1)
        self.assertEqual(applicability["unknown_applicability_tasks"], 1)
        self.assertIn("unknown", applicability["method"])
        self.assertIn("never as zero", applicability["method"])

    def test_measurement_reports_units_and_unknown_values_honestly(self):
        self.fill_store(
            [
                self.event(event_id="1", category="full_return", value=1024, unit="bytes"),
                self.event(event_id="2", category="partial_return", value=None),
                self.event(event_id="3", category="request", value=30, unit="ms"),
            ]
        )

        result, output = self.report()

        self.assertEqual(result.returncode, 0)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(sorted(report["measurement"]["units_present"]), ["bytes", "ms"])
        self.assertEqual(report["measurement"]["events_without_value"], 1)
        self.assertIn("cost", json.dumps(report["limits"]).lower())

    def test_report_carries_no_cost_satisfaction_or_deletion_fields(self):
        self.fill_store([self.event()])

        result, output = self.report()

        self.assertEqual(result.returncode, 0)
        text = output.read_text(encoding="utf-8")
        for forbidden in ('"satisfaction"', '"cost_saved"', '"deletion_candidates"',
                          '"suggest_delete"'):
            self.assertNotIn(forbidden, text)

    def test_report_includes_generated_at_and_store_path(self):
        self.fill_store([self.event()])

        result, output = self.report()

        self.assertEqual(result.returncode, 0)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertIn("generated_at", report)
        self.assertIn(str(self.store), report["store"])


    def test_report_rejects_corrupt_store_without_partial_output(self):
        self.fill_store([self.event()])
        (self.store / "events.jsonl").write_text(
            (self.store / "events.jsonl").read_text(encoding="utf-8") + "{broken\n",
            encoding="utf-8",
        )
        target = self.base / "report.json"

        result = self.run_usage(
            "report", "--store", str(self.store), "--out", str(target)
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("schema validation", result.stdout)
        self.assertFalse(target.exists(), "no partial report on rejection")

    def test_report_includes_time_range_and_source_summary(self):
        self.fill_store(
            [
                self.event(event_id="1", occurred_at="2026-09-10T10:00:00+00:00",
                           source="bundle-x"),
                self.event(event_id="2", occurred_at="2026-09-10T11:00:00+00:00",
                           skill_id="security-and-hardening"),
            ]
        )

        result, output = self.report()

        self.assertEqual(result.returncode, 0)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["events_time_range"]["first"], "2026-09-10T10:00:00+00:00")
        self.assertEqual(report["events_time_range"]["last"], "2026-09-10T11:00:00+00:00")
        self.assertEqual(report["sources_present"], ["bundle-x"])
        self.assertIn("security-and-hardening", report["skills_present"])


if __name__ == "__main__":
    unittest.main()
