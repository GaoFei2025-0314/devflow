import copy
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


CHECKER = Path(__file__).resolve().parents[2] / "scripts" / "check-behavior.py"


class BehaviorCheckerTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.cases = self.root / "cases"
        self.results = self.root / "results"
        self.cases.mkdir()
        self.results.mkdir()

    def tearDown(self):
        self.temporary_directory.cleanup()

    @staticmethod
    def variant(variant_id="spec-only"):
        return {
            "id": variant_id,
            "given": {"request": "Produce a specification only."},
            "when": "The actor handles the request.",
            "allowed_capabilities": ["filesystem.read", "filesystem.write"],
            "expected_actions": [
                {"assertion_id": "AT-03-A01", "criterion": "A local specification is produced."}
            ],
            "forbidden_actions": [
                {"assertion_id": "AT-03-F01", "criterion": "Implementation does not begin."}
            ],
        }

    @classmethod
    def case(cls, case_id="AT-03", variants=None):
        return {
            "id": case_id,
            "title": "Specification-only request",
            "requirement_ids": ["FR-01", "FR-03"],
            "variants": variants or [cls.variant()],
        }

    def write_cases(self, cases=None, raw=None):
        path = self.cases / "routing.json"
        if raw is not None:
            path.write_bytes(raw)
        else:
            document = {"schema_version": 1, "cases": cases or [self.case()]}
            path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def write_full_cases(self):
        cases = []
        for number in range(1, 41):
            case_id = f"AT-{number:02d}"
            variant = self.variant(f"variant-{number:02d}")
            variant["expected_actions"][0]["assertion_id"] = f"{case_id}-A01"
            variant["forbidden_actions"][0]["assertion_id"] = f"{case_id}-F01"
            cases.append(self.case(case_id, [variant]))
        self.write_cases(cases)

    @staticmethod
    def sha256(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def result_record(self, *, case_id="AT-03", variant_id="spec-only", repeat_index=1):
        trace = self.results / "trace.txt"
        trace.write_text("synthetic capture: actor wrote a specification only\n", encoding="utf-8")
        evidence = {
            "path": "trace.txt",
            "sha256": self.sha256(trace),
            "provenance": "synthetic_unit_fixture",
        }
        return {
            "schema_version": 1,
            "run_id": "run-unit-001",
            "case_id": case_id,
            "variant_id": variant_id,
            "repeat_index": repeat_index,
            "subject_source": {"version": "2.0.0-test", "hash": "a" * 40},
            "actor": {"id": "actor-unit"},
            "model": {"id": "synthetic-model", "parameters": {"temperature": 0}},
            "host": {"id": "synthetic-host"},
            "conditions_digest": hashlib.sha256(b"fixed test conditions").hexdigest(),
            "actual_actions": [
                {"action": "write", "target": "specification", "outcome": "completed"}
            ],
            "actual_artifacts": [copy.deepcopy(evidence)],
            "trace": copy.deepcopy(evidence),
            "assertions": [
                {"id": "AT-03-A01", "status": "pass", "evidence": [copy.deepcopy(evidence)]},
                {"id": "AT-03-F01", "status": "pass", "evidence": [copy.deepcopy(evidence)]},
            ],
            "judge": {"id": "judge-unit", "type": "human_fixture"},
            "evidence_limits": ["Synthetic unit fixture; not release evidence."],
        }

    def write_result(self, record, name="one.result.json"):
        path = self.results / name
        path.write_text(json.dumps(record), encoding="utf-8")
        return path

    def run_checker(self, *arguments):
        return subprocess.run(
            [sys.executable, "-B", str(CHECKER), *map(str, arguments)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def verify(self, *extra):
        return self.run_checker(
            "verify", "--cases", self.cases, "--results", self.results,
            "--profile", "checkpoint", "--ids", "AT-03", *extra,
        )

    def test_validate_accepts_minimal_selected_case_and_reports_scope(self):
        self.write_cases()

        result = self.run_checker("validate", "--cases", self.cases, "--ids", "AT-03")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("SCOPE: selected AT-03 (1 case, 1 variant)", result.stdout)
        self.assertIn("BEHAVIOR MATERIAL VALID", result.stdout)
        self.assertNotIn("behavior passed", result.stdout.lower())

    def test_default_validate_requires_exactly_all_40_cases(self):
        self.write_cases()

        result = self.run_checker("validate", "--cases", self.cases)

        self.assertEqual(result.returncode, 1)
        self.assertIn("SCOPE: full AT-01..AT-40", result.stdout)
        self.assertIn("missing required case 'AT-01'", result.stdout)
        self.assertNotIn("40 cases passed", result.stdout)

    def test_default_validate_accepts_exactly_all_40_cases(self):
        self.write_full_cases()

        result = self.run_checker("validate", "--cases", self.cases)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("SCOPE: full AT-01..AT-40 (40 cases, 40 variants)", result.stdout)

    def test_each_variant_requires_both_expected_and_forbidden_actions(self):
        variant = self.variant()
        variant["expected_actions"] = []
        self.write_cases([self.case(variants=[variant])])

        result = self.run_checker("validate", "--cases", self.cases, "--ids", "AT-03")

        self.assertEqual(result.returncode, 1)
        self.assertIn("expected_actions must contain at least one assertion", result.stdout)

    def test_prepare_emits_only_execution_allowlist_even_with_rubric_extensions(self):
        variant = self.variant()
        variant["private_rubric"] = {"answer": "secret"}
        variant["notes"] = "judge-only"
        case = self.case(variants=[variant])
        case["author_notes"] = "do not reveal"
        self.write_cases([case])
        output = self.root / "packets"

        result = self.run_checker(
            "prepare", "--cases", self.cases, "--ids", "AT-03", "--out", output
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        packets = list(output.glob("*.json"))
        self.assertEqual(len(packets), 1)
        packet = json.loads(packets[0].read_text(encoding="utf-8"))
        self.assertEqual(
            set(packet), {"case_id", "variant_id", "given", "when", "allowed_capabilities"}
        )
        serialized = json.dumps(packet)
        for forbidden in ("expected_actions", "forbidden_actions", "requirement_ids", "title", "private_rubric", "secret", "notes"):
            self.assertNotIn(forbidden, serialized)

    def test_prepare_refuses_existing_output_and_leaves_it_untouched(self):
        self.write_cases()
        output = self.root / "packets"
        output.mkdir()
        marker = output / "keep.txt"
        marker.write_text("untouched", encoding="utf-8")

        result = self.run_checker(
            "prepare", "--cases", self.cases, "--ids", "AT-03", "--out", output
        )

        self.assertEqual(result.returncode, 2)
        self.assertEqual(marker.read_text(encoding="utf-8"), "untouched")
        self.assertEqual(sorted(path.name for path in output.iterdir()), ["keep.txt"])

    def test_prepare_rejects_unsafe_variant_id_before_creating_output(self):
        self.write_cases([self.case(variants=[self.variant("../escape")])])
        output = self.root / "packets"

        result = self.run_checker(
            "prepare", "--cases", self.cases, "--ids", "AT-03", "--out", output
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("not an input-safe stable ID", result.stdout)
        self.assertFalse(output.exists())

    def test_prepare_rejects_casefolded_packet_filename_collision_before_writing(self):
        upper = self.variant("Spec")
        lower = self.variant("spec")
        lower["expected_actions"][0]["assertion_id"] = "AT-03-A02"
        lower["forbidden_actions"][0]["assertion_id"] = "AT-03-F02"
        self.write_cases([self.case(variants=[upper, lower])])
        output = self.root / "packets"

        result = self.run_checker(
            "prepare", "--cases", self.cases, "--ids", "AT-03", "--out", output
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("portable packet filename collision", result.stdout)
        self.assertIn("AT-03--Spec.json", result.stdout)
        self.assertIn("AT-03--spec.json", result.stdout)
        self.assertFalse(output.exists())

    def test_complete_synthetic_checkpoint_evidence_passes_with_explicit_limit(self):
        self.write_cases()
        self.write_result(self.result_record())

        result = self.verify()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("assertions: pass=2 fail=0 unknown=0", result.stdout)
        self.assertIn("synthetic_fixture_records=1", result.stdout)
        self.assertIn("does not authenticate semantic truth", result.stdout)

    def test_assertion_only_synthetic_evidence_counts_record_as_synthetic(self):
        self.write_cases()
        record = self.result_record()
        record["trace"]["provenance"] = "host_capture"
        for artifact in record["actual_artifacts"]:
            artifact["provenance"] = "host_capture"
        self.write_result(record)

        result = self.verify()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("synthetic_fixture_records=1", result.stdout)

    def test_absent_trace_is_evidence_insufficient(self):
        self.write_cases()
        record = self.result_record()
        del record["trace"]
        self.write_result(record)

        result = self.verify()

        self.assertEqual(result.returncode, 2)
        self.assertIn("trace is required", result.stdout + result.stderr)

    def test_subject_self_report_only_is_evidence_insufficient(self):
        self.write_cases()
        record = self.result_record()
        record["trace"]["provenance"] = "subject_self_report"
        for artifact in record["actual_artifacts"]:
            artifact["provenance"] = "subject_self_report"
        for assertion in record["assertions"]:
            assertion["evidence"][0]["provenance"] = "subject_self_report"
        self.write_result(record)

        result = self.verify()

        self.assertEqual(result.returncode, 2)
        self.assertIn("subject self-report cannot be the raw trace", result.stdout)
        self.assertIn("pass has no independent capture evidence", result.stdout)

    def test_missing_required_variant_is_evidence_insufficient(self):
        second = self.variant("plan-only")
        second["expected_actions"][0]["assertion_id"] = "AT-03-A02"
        second["forbidden_actions"][0]["assertion_id"] = "AT-03-F02"
        self.write_cases([self.case(variants=[self.variant(), second])])
        self.write_result(self.result_record())

        result = self.verify()

        self.assertEqual(result.returncode, 2)
        self.assertIn("missing result for AT-03/plan-only", result.stdout)

    def test_unknown_and_duplicate_assertions_are_detected_failures(self):
        self.write_cases()
        record = self.result_record()
        record["assertions"].append(copy.deepcopy(record["assertions"][0]))
        record["assertions"].append(
            {"id": "AT-03-X99", "status": "pass", "evidence": [record["trace"]]}
        )
        self.write_result(record)

        result = self.verify()

        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate assertion 'AT-03-A01'", result.stdout)
        self.assertIn("unknown assertion 'AT-03-X99'", result.stdout)

    def test_result_outside_selected_scope_is_detected_failure(self):
        other = self.case("AT-24")
        other["variants"][0]["expected_actions"][0]["assertion_id"] = "AT-24-A01"
        other["variants"][0]["forbidden_actions"][0]["assertion_id"] = "AT-24-F01"
        self.write_cases([self.case(), other])
        self.write_result(self.result_record(case_id="AT-24"))

        result = self.verify()

        self.assertEqual(result.returncode, 1)
        self.assertIn("outside selected scope AT-03", result.stdout)

    def test_fail_and_unknown_statuses_are_reported_separately(self):
        self.write_cases()
        passed = self.result_record(repeat_index=1)
        failed = self.result_record(repeat_index=2)
        unknown = self.result_record(repeat_index=3)
        failed["assertions"][0]["status"] = "fail"
        unknown["assertions"][1]["status"] = "unknown"
        unknown["assertions"][1]["evidence"] = []
        self.write_result(passed, "pass.result.json")
        self.write_result(failed, "fail.result.json")
        self.write_result(unknown, "unknown.result.json")

        result = self.verify()

        self.assertEqual(result.returncode, 1)
        self.assertIn("assertions: pass=4 fail=1 unknown=1", result.stdout)

    def test_unknown_model_and_host_are_accepted_only_with_reported_limits(self):
        self.write_cases()
        record = self.result_record()
        record["model"]["id"] = None
        record["host"]["id"] = None
        record["evidence_limits"] = ["Model and host identities were unavailable."]
        self.write_result(record)

        result = self.verify()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("unknown_model_records=1", result.stdout)
        self.assertIn("unknown_host_records=1", result.stdout)

    def test_unknown_model_without_evidence_limit_is_insufficient(self):
        self.write_cases()
        record = self.result_record()
        record["model"]["id"] = None
        record["evidence_limits"] = []
        self.write_result(record)

        result = self.verify()

        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown model or host requires evidence_limits", result.stdout)

    def test_known_subject_hash_must_be_git_or_sha256_hex(self):
        self.write_cases()
        record = self.result_record()
        record["subject_source"]["hash"] = "invented-hash-label"
        self.write_result(record)

        result = self.verify()

        self.assertEqual(result.returncode, 2)
        self.assertIn("subject_source.hash must be null, a 40-character Git SHA", result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_unknown_subject_source_requires_reported_limit(self):
        self.write_cases()
        record = self.result_record()
        record["subject_source"] = {"version": None, "hash": None}
        record["evidence_limits"] = []
        self.write_result(record)

        result = self.verify()

        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown subject source requires evidence_limits", result.stdout)

    def test_malformed_case_json_is_input_error_without_traceback(self):
        self.write_cases(raw=b"{not json")

        result = self.run_checker("validate", "--cases", self.cases, "--ids", "AT-03")

        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid JSON", result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_malformed_case_utf8_is_input_error_without_traceback(self):
        self.write_cases(raw=b"\xff")

        result = self.run_checker("validate", "--cases", self.cases, "--ids", "AT-03")

        self.assertEqual(result.returncode, 2)
        self.assertIn("not valid UTF-8", result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_wrong_case_field_type_is_input_error_without_traceback(self):
        case = self.case()
        case["variants"] = "not an array"
        self.write_cases([case])

        result = self.run_checker("validate", "--cases", self.cases, "--ids", "AT-03")

        self.assertEqual(result.returncode, 2)
        self.assertIn("variants must be a non-empty array", result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_malformed_result_json_is_input_error_without_traceback(self):
        self.write_cases()
        (self.results / "bad.result.json").write_text("{bad", encoding="utf-8")

        result = self.verify()

        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid JSON", result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_evidence_path_escape_is_rejected_without_traceback(self):
        self.write_cases()
        outside = self.root / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        record = self.result_record()
        escaped = {"path": "../outside.txt", "sha256": self.sha256(outside), "provenance": "synthetic_unit_fixture"}
        record["trace"] = escaped
        record["assertions"][0]["evidence"] = [escaped]
        self.write_result(record)

        result = self.verify()

        self.assertEqual(result.returncode, 2)
        self.assertIn("path escapes results directory", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_nul_evidence_path_is_rejected_without_traceback(self):
        self.write_cases()
        record = self.result_record()
        record["trace"]["path"] = "bad\x00trace.txt"
        self.write_result(record)

        result = self.verify()

        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid evidence path", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_evidence_hash_mismatch_is_detected_failure(self):
        self.write_cases()
        record = self.result_record()
        record["trace"]["sha256"] = "0" * 64
        self.write_result(record)

        result = self.verify()

        self.assertEqual(result.returncode, 1)
        self.assertIn("evidence hash mismatch", result.stdout)

    def test_wrong_evidence_provenance_type_is_controlled_input_error(self):
        self.write_cases()
        record = self.result_record()
        record["trace"]["provenance"] = []
        self.write_result(record)

        result = self.verify()

        self.assertEqual(result.returncode, 2)
        self.assertIn("evidence provenance", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_wrong_assertion_status_type_is_controlled_input_error(self):
        self.write_cases()
        record = self.result_record()
        record["assertions"][0]["status"] = []
        self.write_result(record)

        result = self.verify()

        self.assertEqual(result.returncode, 2)
        self.assertIn("status must be pass, fail, or unknown", result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_release_profile_requires_full_scope_and_companion_directories(self):
        self.write_cases()
        self.write_result(self.result_record())

        scoped = self.run_checker(
            "verify", "--cases", self.cases, "--results", self.results,
            "--profile", "release", "--ids", "AT-03",
        )
        self.assertEqual(scoped.returncode, 2)
        self.assertIn("--ids is not accepted", scoped.stderr)

        missing = self.run_checker(
            "verify", "--cases", self.cases, "--results", self.results,
            "--profile", "release",
        )
        self.assertEqual(missing.returncode, 2)
        self.assertIn("the release profile requires --baseline and --holdout", missing.stderr)


if __name__ == "__main__":
    unittest.main()


KEY_RELEASE_CASES = (
    "AT-03", "AT-14", "AT-20", "AT-21", "AT-22",
    "AT-23", "AT-24", "AT-25", "AT-31", "AT-33",
)
HOLDOUT_CATEGORIES = (
    "phase", "authorization", "evidence_invalidation", "host", "recovery",
)


class ReleaseProfileTests(BehaviorCheckerTests):
    def setUp(self):
        super().setUp()
        self.baseline = self.root / "baseline"
        self.holdout = self.root / "holdout"
        self.baseline_holdout = self.root / "baseline-holdout"
        self.baseline.mkdir()
        self.holdout.mkdir()
        self.baseline_holdout.mkdir()

    def release_record(self, case_number, repeat_index, *, trace_name=None):
        case_id = f"AT-{case_number:02d}"
        variant_id = f"variant-{case_number:02d}"
        record = self.result_record(
            case_id=case_id, variant_id=variant_id, repeat_index=repeat_index
        )
        record["assertions"] = [
            {"id": f"{case_id}-A01", "status": "pass", "evidence": [dict(record["trace"])]},
            {"id": f"{case_id}-F01", "status": "pass", "evidence": [dict(record["trace"])]},
        ]
        record["loading"] = {"total_bytes": 1000, "entries": [{"path": "router", "bytes": 1000}]}
        return record

    def write_release_fixture(self):
        self.write_full_cases()
        for number in range(1, 41):
            repeats = (1, 2, 3) if f"AT-{number:02d}" in KEY_RELEASE_CASES else (1,)
            for repeat in repeats:
                candidate = self.release_record(number, repeat)
                self.write_result(candidate, f"case-{number:02d}-r{repeat}.result.json")
                baseline_record = self.release_record(number, repeat)
                baseline_record["run_id"] = "run-baseline-001"
                baseline_record["subject_source"] = {"version": "1.3.1", "hash": "b" * 40}
                path = self.baseline / f"case-{number:02d}-r{repeat}.result.json"
                path.write_text(json.dumps(baseline_record), encoding="utf-8")
        (self.baseline / "trace.txt").write_bytes((self.results / "trace.txt").read_bytes())
        trace = self.holdout / "trace.txt"
        trace.write_text("synthetic holdout capture\n", encoding="utf-8")
        evidence = {
            "path": "trace.txt",
            "sha256": self.sha256(trace),
            "provenance": "synthetic_unit_fixture",
        }
        for index in range(10):
            category = HOLDOUT_CATEGORIES[index % len(HOLDOUT_CATEGORIES)]
            scenario = {
                "schema_version": 1,
                "scenario_id": f"holdout-{index:02d}",
                "category": category,
                "run_id": "run-unit-001",
                "subject_source": {"version": "2.0.0-test", "hash": "a" * 40},
                "actor": {"id": "actor-unit"},
                "model": {"id": "synthetic-model", "parameters": {"temperature": 0}},
                "host": {"id": "synthetic-host"},
                "conditions_digest": hashlib.sha256(b"holdout conditions").hexdigest(),
                "actual_actions": [
                    {"action": "observe", "target": "scenario", "outcome": "completed"}
                ],
                "actual_artifacts": [copy.deepcopy(evidence)],
                "trace": copy.deepcopy(evidence),
                "assertions": [
                    {
                        "id": f"HOLDOUT-{index:02d}-A01",
                        "status": "pass",
                        "evidence": [copy.deepcopy(evidence)],
                    }
                ],
                "judge": {"id": "judge-unit", "type": "human_fixture"},
                "evidence_limits": ["Synthetic unit fixture; not release evidence."],
            }
            (self.holdout / f"holdout-{index:02d}.holdout.json").write_text(
                json.dumps(scenario), encoding="utf-8"
            )
            baseline_scenario = copy.deepcopy(scenario)
            baseline_scenario["subject_source"] = {"version": "1.3.1", "hash": "b" * 40}
            baseline_scenario["run_id"] = "baseline-holdout-unit"
            (self.baseline_holdout / f"holdout-{index:02d}.holdout.json").write_text(
                json.dumps(baseline_scenario), encoding="utf-8"
            )
        (self.baseline_holdout / "trace.txt").write_bytes(trace.read_bytes())

    def release_verify(self):
        self.write_release_manifest()
        return self.release_verify_existing_manifest()

    def release_verify_existing_manifest(self):
        return self.run_checker(
            "verify", "--cases", self.cases, "--results", self.results,
            "--baseline", self.baseline, "--holdout", self.holdout,
            "--baseline-holdout", self.baseline_holdout,
            "--profile", "release", "--target-candidate-source", "a" * 40,
            "--release-manifest", self.root / "release-manifest.json",
        )

    def write_release_manifest(self):
        entries = []
        for side, directory, suffix in (
            ("candidate", self.results, "*.result.json"),
            ("baseline", self.baseline, "*.result.json"),
            ("holdout", self.holdout, "*.holdout.json"),
            ("baseline_holdout", self.baseline_holdout, "*.holdout.json"),
        ):
            for path in sorted(directory.glob(suffix)):
                record = json.loads(path.read_text(encoding="utf-8"))
                values = {
                    "task_input": {"request": record.get("case_id", record.get("scenario_id"))},
                    "initial_state": {"files": []},
                    "user_rules": {"phase": "evaluation"},
                    "capabilities": {"tools": ["read", "write"]},
                    "budget": {"turns": 5, "tokens": 1000},
                }
                entry = {
                    "side": side, "path": path.name, "sha256": self.sha256(path),
                    "conditions": {
                        field: {"value": value, "evidence": [copy.deepcopy(record["trace"])]}
                        for field, value in values.items()
                    },
                }
                if side in ("holdout", "baseline_holdout"):
                    packet = directory / (path.stem + ".packet.json")
                    packet.write_text(json.dumps({"scenario_id": record["scenario_id"],
                                                  "when": "Unique input " + record["scenario_id"]}),
                                      encoding="utf-8")
                    entry["holdout"] = {
                        "input": {"path": packet.name, "sha256": self.sha256(packet),
                                  "provenance": "synthetic_unit_fixture"},
                        "exposure": "unexposed", "evidence": [copy.deepcopy(record["trace"])],
                    }
                entries.append(entry)
        manifest = {"schema_version": 1, "target_candidate_source": "a" * 40,
                    "records": entries, "holdout_exposures": []}
        self.save_manifest(manifest)
        return manifest

    def save_manifest(self, manifest):
        (self.root / "release-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def protocol_verify(self, *, target="a" * 40, manifest=True, baseline_holdout=True):
        # Direct invocation establishes RED for the missing gate, rather than an
        # argparse error for options that the old checker does not yet recognize.
        spec = importlib.util.spec_from_file_location("behavior_protocol_test", CHECKER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        arguments = argparse.Namespace(
            ids=None, cases=str(self.cases), results=str(self.results),
            baseline=str(self.baseline), holdout=str(self.holdout), profile="release",
            baseline_holdout=str(self.baseline_holdout) if baseline_holdout else None,
            target_candidate_source=target,
            release_manifest=str(self.root / "release-manifest.json") if manifest else None,
        )
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            try:
                code = module.verify_release_command(arguments)
            except module.InputError as error:
                print(error)
                code = 2
        return code, stream.getvalue()

    def test_release_requires_baseline_holdout_evidence(self):
        self.write_release_fixture()
        self.write_release_manifest()
        code, output = self.protocol_verify(baseline_holdout=False)
        self.assertEqual(code, 2, output)
        self.assertIn("--baseline-holdout", output)

    @staticmethod
    def relabel_fixture_capture_references(value, provenance="host_capture"):
        # Deliberate declaration-only mechanism probe; never actual host evidence.
        if isinstance(value, dict):
            if "provenance" in value:
                value["provenance"] = provenance
            for item in value.values():
                ReleaseProfileTests.relabel_fixture_capture_references(item, provenance)
        elif isinstance(value, list):
            for item in value:
                ReleaseProfileTests.relabel_fixture_capture_references(item, provenance)

    def host_labeled_fixture(self):
        self.write_release_fixture()
        for directory in (self.results, self.baseline, self.holdout, self.baseline_holdout):
            for path in directory.glob("*.json"):
                record = json.loads(path.read_text(encoding="utf-8"))
                self.relabel_fixture_capture_references(record)
                path.write_text(json.dumps(record), encoding="utf-8")
        manifest = self.write_release_manifest()
        self.relabel_fixture_capture_references(manifest)
        self.save_manifest(manifest)
        return manifest

    def test_release_manifest_only_synthetic_is_reported(self):
        manifest = self.host_labeled_fixture()
        entry = next(e for e in manifest["records"] if e["side"] == "candidate")
        entry["conditions"]["budget"]["evidence"][0]["provenance"] = "synthetic_unit_fixture"
        self.save_manifest(manifest)
        code, output = self.protocol_verify()
        self.assertEqual(code, 0, output)
        self.assertIn("candidate records=60 (pass=120 fail=0 unknown=0; synthetic=1)", output)
        self.assertIn("synthetic evidence references=1", output)

    def test_release_missing_baseline_holdout_counterpart_is_insufficient(self):
        self.write_release_fixture()
        (self.baseline_holdout / "holdout-00.holdout.json").unlink()
        self.write_release_manifest()
        code, output = self.protocol_verify()
        self.assertEqual(code, 2, output)
        self.assertIn("missing baseline holdout counterpart for holdout-00", output)

    def test_release_holdout_comparable_conditions_are_paired(self):
        self.write_release_fixture()
        for field in ("task_input", "initial_state", "user_rules", "capabilities", "budget"):
            with self.subTest(field=field):
                manifest = self.write_release_manifest()
                entry = next(e for e in manifest["records"] if e["side"] == "baseline_holdout")
                entry["conditions"][field]["value"] = {"different": True}
                self.save_manifest(manifest)
                code, output = self.protocol_verify()
                self.assertEqual(code, 1, output)
                self.assertIn("baseline holdout conditions do not match", output)
                self.assertIn(field, output)

    def test_release_holdout_model_host_and_parameters_are_paired(self):
        self.write_release_fixture()
        path = self.baseline_holdout / "holdout-00.holdout.json"
        original = json.loads(path.read_text(encoding="utf-8"))
        for field, subfield, value in (("model", "id", "other-model"), ("host", "id", "other-host"),
                                       ("model", "parameters", {"temperature": 0.5})):
            with self.subTest(field=field, subfield=subfield):
                record = copy.deepcopy(original)
                record[field][subfield] = value
                path.write_text(json.dumps(record), encoding="utf-8")
                self.write_release_manifest()
                code, output = self.protocol_verify()
                self.assertEqual(code, 1, output)
                self.assertIn(f"{field}.{subfield}", output)

    def test_release_holdout_unknown_condition_is_insufficient(self):
        self.write_release_fixture()
        manifest = self.write_release_manifest()
        entry = next(e for e in manifest["records"] if e["side"] == "baseline_holdout")
        entry["conditions"]["initial_state"]["value"] = None
        self.save_manifest(manifest)
        code, output = self.protocol_verify()
        self.assertEqual(code, 2, output)
        self.assertIn("initial_state", output)

    def test_release_holdout_matching_unknown_identity_is_insufficient(self):
        self.write_release_fixture()
        paths = [directory / "holdout-00.holdout.json"
                 for directory in (self.holdout, self.baseline_holdout)]
        originals = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
        for field in ("model", "host"):
            for value in ("", "   ", "unknown", "UNAVAILABLE"):
                with self.subTest(field=field, value=value):
                    for path, original in zip(paths, originals):
                        record = copy.deepcopy(original)
                        record[field]["id"] = value
                        path.write_text(json.dumps(record), encoding="utf-8")
                    self.write_release_manifest()
                    code, output = self.protocol_verify()
                    self.assertEqual(code, 2, output)
                    self.assertIn(f"{field}.id", output)

    def test_release_holdout_matching_unknown_parameters_are_insufficient(self):
        self.write_release_fixture()
        for directory in (self.holdout, self.baseline_holdout):
            path = directory / "holdout-00.holdout.json"
            record = json.loads(path.read_text(encoding="utf-8"))
            record["model"]["parameters"] = {"temperature": None}
            path.write_text(json.dumps(record), encoding="utf-8")
        self.write_release_manifest()
        code, output = self.protocol_verify()
        self.assertEqual(code, 2, output)
        self.assertIn("model.parameters", output)

    def test_release_baseline_holdout_source_hash_must_be_valid(self):
        self.write_release_fixture()
        path = self.baseline_holdout / "holdout-00.holdout.json"
        original = json.loads(path.read_text(encoding="utf-8"))
        for value in ("", "unknown", "a" * 39, "b" * 63, "G" * 40, 123):
            with self.subTest(value=value):
                record = copy.deepcopy(original)
                record["subject_source"]["hash"] = value
                path.write_text(json.dumps(record), encoding="utf-8")
                self.write_release_manifest()
                code, output = self.protocol_verify()
                self.assertEqual(code, 2, output)
                self.assertIn("subject_source.hash", output)

    def test_release_unilateral_unknown_holdout_metadata_is_insufficient_not_mismatch(self):
        self.write_release_fixture()
        path = self.baseline_holdout / "holdout-00.holdout.json"
        original = json.loads(path.read_text(encoding="utf-8"))
        for field, value in (("id", "unknown"), ("parameters", {"temperature": None})):
            with self.subTest(field=field):
                record = copy.deepcopy(original)
                record["model"][field] = value
                path.write_text(json.dumps(record), encoding="utf-8")
                self.write_release_manifest()
                code, output = self.protocol_verify()
                self.assertEqual(code, 2, output)
                self.assertNotIn("baseline holdout conditions do not match", output)

    def test_release_empty_model_parameter_object_remains_supported(self):
        self.write_release_fixture()
        for directory in (self.holdout, self.baseline_holdout):
            path = directory / "holdout-00.holdout.json"
            record = json.loads(path.read_text(encoding="utf-8"))
            record["model"]["parameters"] = {}
            path.write_text(json.dumps(record), encoding="utf-8")
        self.write_release_manifest()
        code, output = self.protocol_verify()
        self.assertEqual(code, 0, output)

    def test_checkpoint_unknown_parameter_values_remain_readable(self):
        self.write_cases()
        record = self.result_record()
        record["model"]["parameters"] = {"temperature": None}
        self.write_result(record)
        result = self.verify()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_release_holdout_same_label_with_different_input_fails(self):
        self.write_release_fixture()
        manifest = self.write_release_manifest()
        entry = next(e for e in manifest["records"] if e["side"] == "baseline_holdout")
        packet = self.baseline_holdout / entry["holdout"]["input"]["path"]
        packet.write_text(json.dumps({"when": "Actually different actor input"}), encoding="utf-8")
        entry["holdout"]["input"]["sha256"] = self.sha256(packet)
        self.save_manifest(manifest)
        code, output = self.protocol_verify()
        self.assertEqual(code, 1, output)
        self.assertIn("underlying input", output)

    def test_release_unique_input_can_pair_with_different_scenario_label(self):
        self.write_release_fixture()
        manifest = self.write_release_manifest()
        entry = next(e for e in manifest["records"] if e["side"] == "baseline_holdout")
        path = self.baseline_holdout / entry["path"]
        record = json.loads(path.read_text(encoding="utf-8"))
        record["scenario_id"] = "baseline-label"
        path.write_text(json.dumps(record), encoding="utf-8")
        entry["sha256"] = self.sha256(path)
        self.save_manifest(manifest)
        code, output = self.protocol_verify()
        self.assertEqual(code, 0, output)
        self.assertIn("holdout scenarios=10", output)

    def test_release_holdout_baseline_failures_are_preserved_in_counts(self):
        self.write_release_fixture()
        path = self.baseline_holdout / "holdout-00.holdout.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["assertions"][0]["status"] = "fail"
        path.write_text(json.dumps(record), encoding="utf-8")
        self.write_release_manifest()
        code, output = self.protocol_verify()
        self.assertEqual(code, 0, output)
        self.assertIn("baseline_holdout records=10 (pass=9 fail=1 unknown=0; synthetic=10)", output)

    def test_release_synthetic_in_each_manifest_evidence_surface_is_reported(self):
        for surface in ("condition", "input", "exposure"):
            with self.subTest(surface=surface):
                manifest = self.host_labeled_fixture()
                entry = next(e for e in manifest["records"] if e["side"] == "baseline_holdout")
                reference = {
                    "condition": entry["conditions"]["budget"]["evidence"][0],
                    "input": entry["holdout"]["input"],
                    "exposure": entry["holdout"]["evidence"][0],
                }[surface]
                reference["provenance"] = "synthetic_unit_fixture"
                self.save_manifest(manifest)
                code, output = self.protocol_verify()
                self.assertEqual(code, 0, output)
                self.assertIn("baseline_holdout records=10 (pass=10 fail=0 unknown=0; synthetic=1)", output)
                self.assertIn("synthetic evidence references=1", output)

    def test_release_raw_holdout_only_synthetic_is_reported(self):
        manifest = self.host_labeled_fixture()
        entry = next(e for e in manifest["records"] if e["side"] == "holdout")
        path = self.holdout / entry["path"]
        record = json.loads(path.read_text(encoding="utf-8"))
        record["trace"]["provenance"] = "synthetic_unit_fixture"
        path.write_text(json.dumps(record), encoding="utf-8")
        entry["sha256"] = self.sha256(path)
        self.save_manifest(manifest)
        code, output = self.protocol_verify()
        self.assertEqual(code, 0, output)
        self.assertIn("holdout records=10 (pass=10 fail=0 unknown=0; synthetic=1)", output)
        self.assertIn("synthetic evidence references=1", output)

    def test_release_raw_baseline_only_synthetic_is_reported(self):
        manifest = self.host_labeled_fixture()
        entry = next(e for e in manifest["records"] if e["side"] == "baseline")
        path = self.baseline / entry["path"]
        record = json.loads(path.read_text(encoding="utf-8"))
        record["trace"]["provenance"] = "synthetic_unit_fixture"
        path.write_text(json.dumps(record), encoding="utf-8")
        entry["sha256"] = self.sha256(path)
        self.save_manifest(manifest)
        code, output = self.protocol_verify()
        self.assertEqual(code, 0, output)
        self.assertIn("baseline records=60 (pass=120 fail=0 unknown=0; synthetic=1)", output)
        self.assertIn("synthetic evidence references=1", output)

    def test_release_exposure_registry_only_synthetic_is_reported(self):
        manifest = self.host_labeled_fixture()
        packet = self.holdout / "historical-exposed.packet.json"
        packet.write_text(json.dumps({"when": "Historical tuned input, outside current holdouts"}), encoding="utf-8")
        manifest["holdout_exposures"] = [{
            "input": {"path": packet.name, "sha256": self.sha256(packet), "provenance": "host_capture"},
            "evidence": [{"path": "trace.txt", "sha256": self.sha256(self.holdout / "trace.txt"),
                          "provenance": "synthetic_unit_fixture"}],
        }]
        self.save_manifest(manifest)
        code, output = self.protocol_verify()
        self.assertEqual(code, 0, output)
        self.assertIn("synthetic evidence references=1", output)
        self.assertIn("manifest synthetic evidence references=1", output)

    def test_release_explicit_protocol_passes_despite_legacy_digest_differences(self):
        self.write_release_fixture()
        path = self.baseline / "case-10-r1.result.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["conditions_digest"] = "d" * 64
        path.write_text(json.dumps(record), encoding="utf-8")
        self.write_release_manifest()
        code, output = self.protocol_verify()
        self.assertEqual(code, 0, output)

    def test_release_protocol_rejects_each_comparable_condition_mismatch(self):
        self.write_release_fixture()
        for field in ("task_input", "initial_state", "user_rules", "capabilities", "budget"):
            with self.subTest(field=field):
                manifest = self.write_release_manifest()
                entry = next(e for e in manifest["records"]
                             if e["side"] == "baseline" and e["path"] == "case-10-r1.result.json")
                entry["conditions"][field]["value"] = {"different": True}
                self.save_manifest(manifest)
                code, output = self.protocol_verify()
                self.assertEqual(code, 1, output)
                self.assertIn(field, output)

    def test_release_protocol_missing_or_unknown_conditions_are_insufficient(self):
        self.write_release_fixture()
        for value in (None, {}, {"value": {"tokens": None}, "evidence": []}):
            with self.subTest(value=value):
                manifest = self.write_release_manifest()
                manifest["records"][0]["conditions"]["budget"] = value
                self.save_manifest(manifest)
                code, output = self.protocol_verify()
                self.assertEqual(code, 2, output)
                self.assertIn("budget", output)

    def test_release_protocol_requires_target_and_manifest(self):
        self.write_release_fixture()
        self.write_release_manifest()
        for target, manifest in ((None, True), ("a" * 40, False)):
            with self.subTest(target=target, manifest=manifest):
                code, output = self.protocol_verify(target=target, manifest=manifest)
                self.assertEqual(code, 2, output)

    def test_release_old_source_cannot_supply_key_repeats_without_reviewed_reuse(self):
        self.write_release_fixture()
        path = self.results / "case-03-r3.result.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["subject_source"]["hash"] = "c" * 40
        path.write_text(json.dumps(record), encoding="utf-8")
        self.write_release_manifest()
        code, output = self.protocol_verify()
        self.assertEqual(code, 2, output)
        self.assertIn("reuse", output)
        self.assertIn("found 2", output)

    def test_release_manifest_binds_original_result_bytes(self):
        self.write_release_fixture()
        self.write_release_manifest()
        with (self.results / "case-10-r1.result.json").open("a", encoding="utf-8") as stream:
            stream.write("\n")
        code, output = self.protocol_verify()
        self.assertEqual(code, 1, output)
        self.assertIn("record hash mismatch", output)

    def test_release_renamed_duplicate_holdout_input_fails(self):
        self.write_release_fixture()
        manifest = self.write_release_manifest()
        entries = [e for e in manifest["records"] if e["side"] == "holdout"]
        original = json.loads((self.holdout / entries[0]["holdout"]["input"]["path"]).read_text())
        original["scenario_id"] = "renamed-r2"
        target = self.holdout / entries[1]["holdout"]["input"]["path"]
        target.write_text(json.dumps(original, indent=2), encoding="utf-8")
        entries[1]["holdout"]["input"]["sha256"] = self.sha256(target)
        self.save_manifest(manifest)
        code, output = self.protocol_verify()
        self.assertEqual(code, 1, output)
        self.assertIn("duplicate underlying holdout input", output)

    def test_release_promoted_regression_does_not_fill_holdout_coverage(self):
        self.write_release_fixture()
        manifest = self.write_release_manifest()
        entry = next(e for e in manifest["records"] if e["side"] == "holdout")
        entry["holdout"]["exposure"] = "promoted_regression"
        baseline_entry = next(e for e in manifest["records"]
                              if e["side"] == "baseline_holdout" and e["path"] == entry["path"])
        baseline_entry["holdout"]["exposure"] = "promoted_regression"
        self.save_manifest(manifest)
        code, output = self.protocol_verify()
        self.assertEqual(code, 2, output)
        self.assertIn("holdout has 9 scenario(s)", output)

    def test_release_exposure_registry_rejects_relabeled_untouched_holdout(self):
        self.write_release_fixture()
        manifest = self.write_release_manifest()
        entry = next(e for e in manifest["records"] if e["side"] == "holdout")
        manifest["holdout_exposures"] = [{"input": entry["holdout"]["input"],
                                         "evidence": entry["holdout"]["evidence"]}]
        self.save_manifest(manifest)
        code, output = self.protocol_verify()
        self.assertEqual(code, 1, output)
        self.assertIn("exposed input cannot be an unexposed holdout", output)

    def reviewed_reuse_fixture(self):
        self.write_release_fixture()
        path = self.results / "case-03-r3.result.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["subject_source"]["hash"] = "c" * 40
        path.write_text(json.dumps(record), encoding="utf-8")
        manifest = self.write_release_manifest()
        entry = next(e for e in manifest["records"]
                     if e["side"] == "candidate" and e["path"] == path.name)
        resources = []
        for side in ("source", "target"):
            resource = self.results / (side + "-router.md")
            resource.write_text("Identical relevant router instructions.\n", encoding="utf-8")
            resources.append({"path": resource.name, "sha256": self.sha256(resource),
                              "provenance": "synthetic_unit_fixture"})
        entry["reuse"] = {
            "source_hash": "c" * 40, "target_hash": "a" * 40,
            "record_sha256": self.sha256(path),
            "claim_scope": [a["id"] for a in record["assertions"]] + ["loading"],
            "reviewer": {"id": "reviewer-unit"},
            "justification": "Synthetic dependency review: only this unchanged router affects these claims.",
            "evidence": [copy.deepcopy(record["trace"])],
            "resources": [{"path": "skills/devflow/SKILL.md",
                           "source": resources[0], "target": resources[1]}],
        }
        self.save_manifest(manifest)
        return manifest, entry

    def test_release_reviewed_unchanged_resources_allow_bound_old_source_reuse(self):
        self.reviewed_reuse_fixture()
        code, output = self.protocol_verify()
        self.assertEqual(code, 0, output)

    def test_release_reuse_only_synthetic_is_reported(self):
        for surface in ("review", "resource"):
            with self.subTest(surface=surface):
                manifest, reused_entry = self.reviewed_reuse_fixture()
                directories = {"candidate": self.results, "baseline": self.baseline,
                               "holdout": self.holdout, "baseline_holdout": self.baseline_holdout}
                for entry in manifest["records"]:
                    path = directories[entry["side"]] / entry["path"]
                    record = json.loads(path.read_text(encoding="utf-8"))
                    self.relabel_fixture_capture_references(record)
                    path.write_text(json.dumps(record), encoding="utf-8")
                    entry["sha256"] = self.sha256(path)
                    if "reuse" in entry:
                        entry["reuse"]["record_sha256"] = entry["sha256"]
                self.relabel_fixture_capture_references(manifest)
                reference = (reused_entry["reuse"]["evidence"][0] if surface == "review"
                             else reused_entry["reuse"]["resources"][0]["source"])
                reference["provenance"] = "synthetic_unit_fixture"
                self.save_manifest(manifest)
                code, output = self.protocol_verify()
                self.assertEqual(code, 0, output)
                self.assertIn("candidate records=60 (pass=120 fail=0 unknown=0; synthetic=1)", output)
                self.assertIn("synthetic evidence references=1", output)

    def test_release_reuse_cannot_waive_a_changed_relevant_resource(self):
        manifest, entry = self.reviewed_reuse_fixture()
        target = self.results / "target-router.md"
        target.write_text("Changed authorization behavior.\n", encoding="utf-8")
        entry["reuse"]["resources"][0]["target"]["sha256"] = self.sha256(target)
        self.save_manifest(manifest)
        code, output = self.protocol_verify()
        self.assertEqual(code, 1, output)
        self.assertIn("changed relevant resource", output)

    def test_release_reuse_requires_complete_claim_scope_and_record_binding(self):
        for field, value in (("claim_scope", ["AT-03-A01"]), ("record_sha256", "d" * 64),
                             ("target_hash", "e" * 40), ("resources", [])):
            with self.subTest(field=field):
                manifest, entry = self.reviewed_reuse_fixture()
                entry["reuse"][field] = value
                self.save_manifest(manifest)
                code, output = self.protocol_verify()
                self.assertEqual(code, 2, output)
                self.assertIn(field, output)

    def test_release_malformed_assertions_have_consistent_controlled_errors(self):
        for malformed in ({"status": "pass", "evidence": []}, None,
                          {"id": [], "status": "pass", "evidence": []}):
            for source in ("old", "target"):
                with self.subTest(malformed=malformed, source=source):
                    manifest, entry = self.reviewed_reuse_fixture()
                    path = self.results / entry["path"]
                    record = json.loads(path.read_text(encoding="utf-8"))
                    record["assertions"][0] = malformed
                    if source == "target":
                        record["subject_source"]["hash"] = "a" * 40
                    path.write_text(json.dumps(record), encoding="utf-8")
                    entry["sha256"] = entry["reuse"]["record_sha256"] = self.sha256(path)
                    self.save_manifest(manifest)
                    result = self.release_verify_existing_manifest()
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn("INPUT ERROR:", result.stderr)
                    self.assertIn("assertions[0]", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)

    def test_release_holdout_declaration_symlinks_cannot_escape_either_side(self):
        self.write_release_fixture()
        for directory in (self.holdout, self.baseline_holdout):
            with self.subTest(side=directory.name):
                self.write_release_manifest()
                declared = directory / "holdout-00.holdout.json"
                outside = self.root / (directory.name + "-outside-record.json")
                contents = declared.read_bytes()
                outside.write_bytes(contents)
                declared.unlink()
                try:
                    declared.symlink_to(outside)
                    self.assertTrue(declared.is_symlink())
                    self.assertFalse(declared.resolve().is_relative_to(directory.resolve()))
                    result = self.release_verify_existing_manifest()
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn("holdout file escapes holdout directory", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)
                finally:
                    if declared.is_symlink():
                        declared.unlink()
                    declared.write_bytes(contents)

    def test_release_holdout_declaration_symlink_inside_side_remains_supported(self):
        self.write_release_fixture()
        self.write_release_manifest()
        declared = self.baseline_holdout / "holdout-00.holdout.json"
        inside = self.baseline_holdout / "archive" / "original-record.data"
        inside.parent.mkdir()
        inside.write_bytes(declared.read_bytes())
        declared.unlink()
        declared.symlink_to(inside)
        self.assertTrue(declared.is_symlink())
        self.assertTrue(declared.resolve().is_relative_to(self.baseline_holdout.resolve()))
        result = self.release_verify_existing_manifest()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_release_reuse_preserves_old_source_declared_failure(self):
        manifest, entry = self.reviewed_reuse_fixture()
        path = self.results / entry["path"]
        record = json.loads(path.read_text(encoding="utf-8"))
        record["assertions"][0]["status"] = "fail"
        path.write_text(json.dumps(record), encoding="utf-8")
        entry["sha256"] = entry["reuse"]["record_sha256"] = self.sha256(path)
        self.save_manifest(manifest)
        code, output = self.protocol_verify()
        self.assertEqual(code, 1, output)
        self.assertIn("status is fail", output)

    def test_release_condition_capture_missing_or_tampered_blocks_material(self):
        self.write_release_fixture()
        for key, value, expected in (("path", "missing.json", 2), ("sha256", "f" * 64, 1)):
            with self.subTest(key=key):
                manifest = self.write_release_manifest()
                manifest["records"][0]["conditions"]["budget"]["evidence"][0][key] = value
                self.save_manifest(manifest)
                code, output = self.protocol_verify()
                self.assertEqual(code, expected, output)

    def test_release_opaque_schema1_remains_checkpoint_readable(self):
        self.write_cases()
        self.write_result(self.result_record())
        result = self.verify()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_release_incomparable_pairs_do_not_supply_loading_comparison(self):
        self.write_release_fixture()
        manifest = self.write_release_manifest()
        for entry in manifest["records"]:
            if entry["side"] == "baseline":
                entry["conditions"]["budget"]["value"] = {"tokens": 2000}
        self.save_manifest(manifest)
        code, output = self.protocol_verify()
        self.assertEqual(code, 1, output)
        self.assertIn("COMPARISON: paired runs=0", output)

    def test_release_passes_with_complete_fixture(self):
        self.write_release_fixture()

        result = self.release_verify()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("RELEASE MATERIAL VERIFIED", result.stdout)
        self.assertIn("holdout scenarios=10", result.stdout)
        self.assertIn("AT comparable pairs=60; holdout comparable unexposed pairs=10", result.stdout)
        self.assertIn("COMPARISON", result.stdout)

    def test_release_missing_key_repeat_is_insufficient(self):
        self.write_release_fixture()
        (self.results / "case-03-r3.result.json").unlink()
        (self.baseline / "case-03-r3.result.json").unlink()

        result = self.release_verify()

        self.assertEqual(result.returncode, 2)
        self.assertIn("AT-03/variant-03: key case requires 3 repeats, found 2", result.stdout)

    def test_release_holdout_category_gap_is_insufficient(self):
        self.write_release_fixture()
        (self.holdout / "holdout-04.holdout.json").unlink()

        result = self.release_verify()

        self.assertEqual(result.returncode, 2)
        self.assertIn("holdout category 'recovery' has 1 scenario(s), requires 2", result.stdout)

    def test_release_holdout_failure_is_detected(self):
        self.write_release_fixture()
        path = self.holdout / "holdout-00.holdout.json"
        scenario = json.loads(path.read_text(encoding="utf-8"))
        scenario["assertions"][0]["status"] = "fail"
        path.write_text(json.dumps(scenario), encoding="utf-8")

        result = self.release_verify()

        self.assertEqual(result.returncode, 1)
        self.assertIn("holdout-00", result.stdout)
        self.assertIn("status is fail", result.stdout)

    def test_release_mismatched_baseline_conditions_are_detected(self):
        self.write_release_fixture()
        path = self.baseline / "case-10-r1.result.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["model"]["id"] = "different-model"
        path.write_text(json.dumps(record), encoding="utf-8")

        result = self.release_verify()

        self.assertEqual(result.returncode, 1)
        self.assertIn("baseline conditions do not match", result.stdout)

    def test_release_missing_baseline_run_is_insufficient(self):
        self.write_release_fixture()
        (self.baseline / "case-10-r1.result.json").unlink()

        result = self.release_verify()

        self.assertEqual(result.returncode, 2)
        self.assertIn("missing baseline run for AT-10/variant-10 repeat 1", result.stdout)

    def test_release_missing_loading_is_insufficient(self):
        self.write_release_fixture()
        path = self.results / "case-10-r1.result.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        del record["loading"]
        path.write_text(json.dumps(record), encoding="utf-8")

        result = self.release_verify()

        self.assertEqual(result.returncode, 2)
        self.assertIn("loading", result.stdout)

    def test_release_comparison_reports_loading_medians_as_exploratory(self):
        self.write_release_fixture()
        for number in (10, 11, 12):
            path = self.results / f"case-{number:02d}-r1.result.json"
            record = json.loads(path.read_text(encoding="utf-8"))
            record["loading"]["total_bytes"] = 500
            path.write_text(json.dumps(record), encoding="utf-8")

        result = self.release_verify()

        self.assertEqual(result.returncode, 0)
        self.assertIn("median loading", result.stdout)
        self.assertIn("exploratory", result.stdout)

    def test_release_duplicate_holdout_scenario_id_is_detected(self):
        self.write_release_fixture()
        duplicated = json.loads((self.holdout / "holdout-00.holdout.json").read_text(encoding="utf-8"))
        (self.holdout / "holdout-10.holdout.json").write_text(
            json.dumps(duplicated), encoding="utf-8"
        )

        result = self.release_verify()

        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate scenario_id 'holdout-00'", result.stdout)

    def test_release_malformed_holdout_rejects_without_traceback(self):
        self.write_release_fixture()
        path = self.holdout / "holdout-00.holdout.json"
        scenario = json.loads(path.read_text(encoding="utf-8"))
        del scenario["judge"]
        path.write_text(json.dumps(scenario), encoding="utf-8")

        result = self.release_verify()

        self.assertEqual(result.returncode, 2)
        self.assertIn("judge", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_release_without_any_paired_loading_is_insufficient(self):
        self.write_release_fixture()
        for path in sorted(self.results.glob("*.result.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            record["loading"]["total_bytes"] = None
            path.write_text(json.dumps(record), encoding="utf-8")

        result = self.release_verify()

        self.assertEqual(result.returncode, 2)
        self.assertIn("no paired loading data", result.stdout)
