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

    def test_checkpoint_rejects_holdout_declarations_as_capture(self):
        self.write_cases()
        declaration = self.results / "other.holdout.json"
        declaration.write_text('{"assertions": [{"status": "pass"}]}', encoding="utf-8")
        reference = {"path": declaration.name, "sha256": self.sha256(declaration),
                     "provenance": "host_capture"}
        for surface in ("trace", "artifact", "assertion"):
            with self.subTest(surface=surface):
                record = self.result_record()
                if surface == "trace":
                    record["trace"] = copy.deepcopy(reference)
                elif surface == "artifact":
                    record["actual_artifacts"] = [copy.deepcopy(reference)]
                else:
                    record["assertions"][0]["evidence"] = [copy.deepcopy(reference)]
                self.write_result(record)
                result = self.verify()
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("declaration cannot", result.stdout)

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
    def test_release_rejects_synthetic_evidence_without_test_mode(self):
        self.write_release_fixture()
        self.write_release_manifest()
        result = self.release_verify_existing_manifest(fixture_mode=False)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("synthetic evidence cannot establish release acceptance", result.stdout)
        self.assertNotIn("RELEASE MATERIAL VERIFIED", result.stdout)

    def test_release_fixture_mode_never_reports_release_acceptance(self):
        self.write_release_fixture()
        result = self.release_verify()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("SYNTHETIC FIXTURE VERIFIED", result.stdout)
        self.assertNotIn("RELEASE MATERIAL VERIFIED", result.stdout)

    def test_holdout_required_run_fields_are_validated(self):
        self.write_release_fixture()
        original = json.loads((self.holdout / "holdout-00.holdout.json").read_text(encoding="utf-8"))
        spec = importlib.util.spec_from_file_location("holdout_shape_test", CHECKER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        fields = [
            "run_id", "subject_source.version", "subject_source.hash", "actor.id",
            "model.id", "model.parameters", "host.id", "conditions_digest",
            "actual_actions", "actual_artifacts", "assertions", "judge.id",
            "judge.type", "trace", "evidence_limits",
        ]
        for field in fields:
            with self.subTest(missing=field):
                record = copy.deepcopy(original)
                keys = field.split(".")
                parent = record
                for key in keys[:-1]:
                    parent = parent[key]
                del parent[keys[-1]]
                with self.assertRaises(module.InputError):
                    module.validate_holdout_shape(record, "holdout")

    def test_holdout_missing_artifacts_returns_controlled_input_error(self):
        self.write_release_fixture()
        path = self.holdout / "holdout-00.holdout.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        del record["actual_artifacts"]
        path.write_text(json.dumps(record), encoding="utf-8")
        self.write_release_manifest()
        result = self.release_verify_existing_manifest(fixture_mode=False)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("actual_artifacts", result.stderr)
        self.assertIn("INPUT ERROR:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_holdout_preserves_legacy_actions_without_target(self):
        self.write_release_fixture()
        path = self.holdout / "holdout-00.holdout.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        for target in (None, ["source-a", "source-b"]):
            with self.subTest(target=target):
                if target is None:
                    record["actual_actions"][0].pop("target", None)
                else:
                    record["actual_actions"][0]["target"] = target
                path.write_text(json.dumps(record), encoding="utf-8")
                self.write_release_manifest()
                code, output = self.protocol_verify()
                self.assertEqual(code, 0, output)

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

    def release_verify_existing_manifest(self, *, fixture_mode=True):
        return self.run_checker(
            "verify", "--cases", self.cases, "--results", self.results,
            "--baseline", self.baseline, "--holdout", self.holdout,
            "--baseline-holdout", self.baseline_holdout,
            "--profile", "release", "--target-candidate-source", "a" * 40,
            "--release-manifest", self.root / "release-manifest.json",
            *(["--allow-synthetic-fixtures"] if fixture_mode else []),
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

    def collection_fixture(self):
        self.write_release_fixture()
        # Independent runs may use the same relative trace name with different bytes.
        for directory in (self.results, self.baseline):
            path = directory / "case-01-r1.result.json"
            record = json.loads(path.read_text(encoding="utf-8"))
            record["run_id"] += "-second"
            path.write_text(json.dumps(record), encoding="utf-8")
        manifest = self.write_release_manifest()
        manifest.update(schema_version=2, collection_id="immutable-collection")
        directories = {"candidate": self.results, "baseline": self.baseline,
                       "holdout": self.holdout, "baseline_holdout": self.baseline_holdout}
        for entry in manifest["records"]:
            directory = directories[entry["side"]]
            record = json.loads((directory / entry["path"]).read_text(encoding="utf-8"))
            entry["run_id"] = record["run_id"]
            entry["evidence_root"] = "packages/" + record["run_id"]
            root = directory / entry["evidence_root"]
            root.mkdir(parents=True, exist_ok=True)
            for evidence in directory.iterdir():
                if evidence.is_file() and not evidence.name.endswith((".result.json", ".holdout.json")):
                    (root / evidence.name).write_bytes(evidence.read_bytes())
        # Colliding root-level files must never mask the original per-package bytes.
        for directory in directories.values():
            (directory / "trace.txt").write_text("unrelated capture\n", encoding="utf-8")
        self.save_manifest(manifest)
        return manifest

    def test_collection_manifest_preserves_independent_run_evidence(self):
        self.collection_fixture()
        code, output = self.protocol_verify()
        self.assertEqual(code, 0, output)
        self.assertIn("AT comparable pairs=60", output)
        self.assertIn("holdout scenarios=10", output)

    def test_collection_requires_original_run_binding(self):
        manifest = self.collection_fixture()
        manifest["records"][0]["run_id"] = "forged-run"
        self.save_manifest(manifest)
        code, output = self.protocol_verify()
        self.assertEqual(code, 1, output)
        self.assertIn("run_id does not match original record", output)

    def test_collection_rejects_unsafe_evidence_roots(self):
        original = self.collection_fixture()
        for root in ("../outside", "/absolute", "C:/outside", "packages\\capture", "packages/../x", "", "./packages", "packages//run"):
            with self.subTest(root=root):
                manifest = copy.deepcopy(original)
                manifest["records"][0]["evidence_root"] = root
                self.save_manifest(manifest)
                code, output = self.protocol_verify()
                self.assertEqual(code, 2, output)
                self.assertIn("evidence_root", output)

    def test_collection_cannot_use_external_symlink_root(self):
        manifest = self.collection_fixture()
        outside = self.root / "external-evidence"
        outside.mkdir()
        link = self.results / "linked-evidence"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"symlinks unavailable: {error}")
        entry = next(item for item in manifest["records"] if item["side"] == "candidate")
        entry["evidence_root"] = link.name
        self.save_manifest(manifest)
        code, output = self.protocol_verify()
        self.assertEqual(code, 2, output)
        self.assertIn("evidence_root escapes", output)

    def test_collection_keeps_original_assertion_failure(self):
        manifest = self.collection_fixture()
        entry = manifest["records"][0]
        path = self.results / entry["path"]
        record = json.loads(path.read_text(encoding="utf-8"))
        record["assertions"][0]["status"] = "fail"
        path.write_text(json.dumps(record), encoding="utf-8")
        entry["sha256"] = self.sha256(path)
        self.save_manifest(manifest)
        code, output = self.protocol_verify()
        self.assertEqual(code, 1, output)
        self.assertIn("status is fail", output)

    def protocol_verify(self, *, target="a" * 40, manifest=True, baseline_holdout=True,
                        fixture_mode=True):
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
            allow_synthetic_fixtures=fixture_mode,
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

    def test_release_rejects_holdout_declarations_as_raw_capture(self):
        # These are declaration-only mechanism probes, never host execution evidence.
        for side, directory in (("holdout", self.holdout), ("baseline_holdout", self.baseline_holdout)):
            with self.subTest(side=side):
                manifest = self.host_labeled_fixture()
                declaration = directory / "holdout-01.holdout.json"
                path = directory / "holdout-00.holdout.json"
                reference = {"path": declaration.name, "sha256": self.sha256(declaration),
                             "provenance": "host_capture"}
                record = json.loads(path.read_text(encoding="utf-8"))
                record["trace"] = copy.deepcopy(reference)
                record["actual_artifacts"] = [copy.deepcopy(reference)]
                record["assertions"][0]["evidence"] = [copy.deepcopy(reference)]
                path.write_text(json.dumps(record), encoding="utf-8")
                entry = next(e for e in manifest["records"] if e["side"] == side and e["path"] == path.name)
                entry["sha256"] = self.sha256(path)
                self.save_manifest(manifest)
                code, output = self.protocol_verify(fixture_mode=False)
                self.assertEqual(code, 2, output)
                self.assertIn("declaration cannot", output)
                self.assertNotIn("RELEASE MATERIAL VERIFIED", output)

    def test_release_rejects_declaration_capture_symlinks(self):
        manifest = self.host_labeled_fixture()
        evidence = self.holdout / "evidence"
        evidence.mkdir()
        declaration = evidence / "other.HOLDOUT.JSON"
        declaration.write_bytes((self.holdout / "holdout-01.holdout.json").read_bytes())
        alias = evidence / "captured-trace.txt"
        try:
            alias.symlink_to(declaration)
        except OSError as error:
            self.skipTest(f"symlinks unavailable: {error}")
        reference = {"path": "evidence/captured-trace.txt", "sha256": self.sha256(declaration),
                     "provenance": "host_capture"}
        path = self.holdout / "holdout-00.holdout.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["trace"] = copy.deepcopy(reference)
        path.write_text(json.dumps(record), encoding="utf-8")
        entry = next(e for e in manifest["records"] if e["side"] == "holdout" and e["path"] == path.name)
        entry["sha256"] = self.sha256(path)
        entry["conditions"]["budget"]["evidence"] = [copy.deepcopy(reference)]
        self.save_manifest(manifest)
        code, output = self.protocol_verify(fixture_mode=False)
        self.assertEqual(code, 2, output)
        self.assertIn("declaration cannot", output)
        self.assertNotIn("RELEASE MATERIAL VERIFIED", output)

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
        self.assertIn("SYNTHETIC FIXTURE VERIFIED", result.stdout)
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


class PatchProfileTests(unittest.TestCase):
    """Structural patch fixtures are host-labelled bytes, never real acceptance."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cases = self.root / "cases"
        self.results = self.root / "results"
        self.holdout = self.root / "holdout"
        for directory in (self.cases, self.results, self.holdout):
            directory.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def save(self, path, data):
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def reference(self, path):
        return {"path": path.name, "sha256": self.digest(path), "provenance": "host_capture"}

    def fixture(self):
        variant = {
            "id": "target", "given": {"request": "check target"}, "when": "actor responds",
            "allowed_capabilities": ["filesystem.read"],
            "expected_actions": [{"assertion_id": "AT-02-A01", "criterion": "correct metric"}],
            "forbidden_actions": [{"assertion_id": "AT-02-F01", "criterion": "no false metric"}],
        }
        case = {"id": "AT-02", "title": "metric", "requirement_ids": ["FR-01"],
                "variants": [variant]}
        self.save(self.cases / "routing.json", {"schema_version": 1, "cases": [case]})
        scope = {
            "schema_version": 1, "target_candidate_source": "a" * 40,
            "cases": [{"case_id": "AT-02", "case_sha256": hashlib.sha256(json.dumps(case,
                       sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest(),
                       "variants": [{"variant_id": "target",
                       "assertion_ids": ["AT-02-A01", "AT-02-F01"], "repeats": 1}]}],
            "holdouts": [],
        }
        manifest = {"schema_version": 2, "collection_id": "patch-fixture",
                    "target_candidate_source": "a" * 40, "patch_scope_sha256": "",
                    "attempt_ledger": None, "records": [], "holdout_exposures": []}

        def captured(directory, name, content):
            evidence_root = directory / "evidence" / name
            evidence_root.mkdir(parents=True)
            trace = evidence_root / "trace.txt"
            trace.write_text(content, encoding="utf-8")
            return self.reference(trace), evidence_root.relative_to(directory).as_posix()

        def record(trace, **identity):
            return {"schema_version": 1, "run_id": "patch-run-" + identity.get("scenario_id", "at02"),
                    "subject_source": {"version": "2.0.2", "hash": "a" * 40},
                    "actor": {"id": "actor"}, "model": {"id": "model", "parameters": {"effort": "high"}},
                    "host": {"id": "windows-codex"}, "conditions_digest": "b" * 64,
                    "actual_actions": [{"action": "read", "target": "rules", "outcome": "done"}],
                    "actual_artifacts": [copy.deepcopy(trace)], "trace": copy.deepcopy(trace),
                    "judge": {"id": "judge", "type": "independent"}, "evidence_limits": [],
                    **identity}

        def binding(side, path, item, root, trace):
            conditions = {field: {"value": {"captured": field}, "evidence": [copy.deepcopy(trace)]}
                          for field in ("task_input", "initial_state", "user_rules", "capabilities", "budget")}
            return {"side": side, "path": path.name, "sha256": self.digest(path),
                    "run_id": item["run_id"], "evidence_root": root, "conditions": conditions}

        def dispatch_binding(entry, item, authored):
            directory = self.results / entry["evidence_root"]
            dispatched = {"case_id": item["case_id"], "variant_id": item["variant_id"],
                          "run_id": item["run_id"], "given": authored["given"],
                          "when": authored["when"],
                          "allowed_capabilities": authored["allowed_capabilities"]}
            input_path = self.save(directory / "dispatch-input.json", dispatched)
            receipt = {"case_id": item["case_id"], "variant_id": item["variant_id"],
                       "run_id": item["run_id"], "actor_id": item["actor"]["id"],
                       "native_invocation_id": "native-" + item["run_id"],
                       "dispatch_sha256": self.digest(input_path), "received": True}
            receipt_path = self.save(directory / "dispatch-receipt.json", receipt)
            entry["dispatch_input"] = self.reference(input_path)
            entry["dispatch_receipt"] = self.reference(receipt_path)

        trace, evidence_root = captured(self.results, "at02", "structural fixture candidate trace")
        candidate = record(trace, case_id="AT-02", variant_id="target", repeat_index=1)
        candidate["assertions"] = [{"id": aid, "status": "pass", "evidence": [copy.deepcopy(trace)]}
                                   for aid in ("AT-02-A01", "AT-02-F01")]
        candidate["loading"] = {"total_bytes": 5, "entries": [{"path": "rules", "bytes": 5}]}
        path = self.save(self.results / "at02.result.json", candidate)
        manifest["records"].append(binding("candidate", path, candidate, evidence_root, trace))
        dispatch_binding(manifest["records"][-1], candidate, variant)

        required = {
            "AT-02": ("default-off-analysis", "enabled-minimal-recording", "stopped-recording", "local-export"),
            "AT-30": ("zero-reads-no-applicable-task", "applicability-unknown"),
            "AT-31": ("untrusted-content-with-embedded-instructions",),
            "AT-33": ("flat-install-missing-shared-template", "complete-package-install",
                      "single-skill-with-dependencies", "linked-install"),
        }
        authored_cases = {"AT-02": case}
        scope_cases = {"AT-02": scope["cases"][0]}
        for case_id, variants in required.items():
            if case_id not in authored_cases:
                authored_cases[case_id] = {"id": case_id, "title": case_id,
                                            "requirement_ids": ["FR-01"], "variants": []}
                scope_cases[case_id] = {"case_id": case_id, "variants": []}
            for variant_id in variants:
                ids = [f"{case_id}-{variant_id}-E01", f"{case_id}-{variant_id}-F01"]
                authored_cases[case_id]["variants"].append({
                    "id": variant_id, "given": {"request": variant_id}, "when": "actor responds",
                    "allowed_capabilities": ["filesystem.read"],
                    "expected_actions": [{"assertion_id": ids[0], "criterion": "required action"}],
                    "forbidden_actions": [{"assertion_id": ids[1], "criterion": "forbidden action"}],
                })
                repeats = 3 if (case_id, variant_id) == ("AT-33", "complete-package-install") else 1
                scope_cases[case_id]["variants"].append({"variant_id": variant_id,
                                                         "assertion_ids": ids, "repeats": repeats})
                for repeat in range(1, repeats + 1):
                    name = f"{case_id}-{variant_id}-r{repeat}"
                    variant_trace, variant_root = captured(self.results, name, f"structural {name} trace")
                    item = record(variant_trace, case_id=case_id, variant_id=variant_id, repeat_index=repeat)
                    item["run_id"] = f"patch-run-{name}"
                    item["actor"]["id"] = "actor-" + name
                    item["assertions"] = [{"id": aid, "status": "pass",
                                           "evidence": [copy.deepcopy(variant_trace)]} for aid in ids]
                    item["loading"] = {"total_bytes": 5, "entries": [{"path": "rules", "bytes": 5}]}
                    item_path = self.save(self.results / f"{name}.result.json", item)
                    manifest["records"].append(binding("candidate", item_path, item,
                                                       variant_root, variant_trace))
                    dispatch_binding(manifest["records"][-1], item, authored_cases[case_id]["variants"][-1])
        scope["cases"] = list(scope_cases.values())
        for item in scope["cases"]:
            item["case_sha256"] = hashlib.sha256(json.dumps(authored_cases[item["case_id"]],
                sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
        self.save(self.cases / "routing.json", {"schema_version": 1, "cases": list(authored_cases.values())})

        for index, category in enumerate(("install_authorization", "observability_identity"), 1):
            scenario_id = f"patch-holdout-{index}"
            trace, evidence_root = captured(self.holdout, scenario_id, f"fixture {scenario_id}")
            packet = {"scenario_id": scenario_id, "category": category,
                      "task": f"new-{index}", "initial_state": {"files": []},
                      "allowed_capabilities": ["filesystem.read"]}
            packet_path = self.save(self.holdout / "evidence" / scenario_id / "packet.json", packet)
            dispatched_path = self.save(self.holdout / "evidence" / scenario_id / "dispatch.json", packet)
            receipt_path = self.save(self.holdout / "evidence" / scenario_id / "receipt.json",
                {"scenario_id": scenario_id, "category": category,
                 "run_id": f"patch-run-{scenario_id}", "actor_id": "actor",
                 "dispatch_sha256": self.digest(dispatched_path), "received": True,
                 "native_invocation_id": f"native-{scenario_id}"})
            input_hash = hashlib.sha256(json.dumps({key: value for key, value in packet.items()
                          if key != "scenario_id"}, sort_keys=True,
                          separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
            assertion_id = f"PATCH-H{index}-A01"
            rubric_path = self.holdout / "evidence" / scenario_id / "rubric.json"
            self.save(rubric_path, {"scenario_id": scenario_id, "category": category,
                                    "assertions": [{"id": assertion_id, "criterion": "accept only safe action"}]})
            scope["holdouts"].append({"scenario_id": scenario_id, "category": category,
                                      "input_sha256": input_hash, "rubric_sha256": self.digest(rubric_path),
                                      "assertion_ids": [assertion_id]})
            holdout = record(trace, scenario_id=scenario_id, category=category)
            holdout["assertions"] = [{"id": assertion_id, "status": "pass", "evidence": [copy.deepcopy(trace)]}]
            path = self.save(self.holdout / f"{scenario_id}.holdout.json", holdout)
            entry = binding("holdout", path, holdout, evidence_root, trace)
            entry["holdout"] = {"input": {"kind": "controller_sealed_input", "path": packet_path.name,
                                             "sha256": self.digest(packet_path)},
                                "dispatch_input": self.reference(dispatched_path),
                                "dispatch_receipt": [self.reference(receipt_path)],
                                "exposure": "unexposed",
                                "evidence": [copy.deepcopy(trace)],
                                "rubric": {"kind": "controller_frozen_rubric", "path": rubric_path.name,
                                           "sha256": self.digest(rubric_path)}}
            manifest["records"].append(entry)

        ledger = self.root / "ledger.txt"
        ledger.write_text("attempt ledger structural fixture", encoding="utf-8")
        manifest["attempt_ledger"] = {"kind": "coordinator_index", "path": ledger.name,
                                      "sha256": self.digest(ledger)}
        self.write_scope(scope, manifest)
        self.write_manifest(manifest)
        return scope, manifest

    def write_scope(self, scope, manifest):
        path = self.save(self.root / "patch-scope.json", scope)
        manifest["patch_scope_sha256"] = self.digest(path)
        seal_path = self.save(self.root / "scope-seal.json", {"schema_version": 1,
            "patch_scope_sha256": manifest["patch_scope_sha256"],
            "target_candidate_source": scope["target_candidate_source"],
            "sealed_at": "2026-09-23T00:00:00Z"})
        manifest["scope_seal"] = {"kind": "coordinator_seal", "path": seal_path.name,
                                  "sha256": self.digest(seal_path)}

    def write_manifest(self, manifest):
        self.save(self.root / "manifest.json", manifest)

    def verify(self):
        return subprocess.run([sys.executable, "-B", str(CHECKER), "verify", "--profile", "patch",
            "--cases", str(self.cases), "--results", str(self.results), "--holdout", str(self.holdout),
            "--target-candidate-source", "a" * 40, "--patch-scope", str(self.root / "patch-scope.json"),
            "--release-manifest", str(self.root / "manifest.json")], capture_output=True, text=True,
            encoding="utf-8", errors="replace", check=False)

    def test_patch_accepts_frozen_candidate_and_two_holdouts_structurally(self):
        self.fixture()
        result = self.verify()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PATCH MATERIAL VERIFIED", result.stdout)
        self.assertIn("cannot authenticate", result.stdout)

    def test_patch_rejects_missing_variant_and_assertion(self):
        scope, manifest = self.fixture()
        case_path = self.cases / "routing.json"
        cases = json.loads(case_path.read_text(encoding="utf-8"))
        other = copy.deepcopy(cases["cases"][0]["variants"][0])
        other["id"] = "other"
        other["expected_actions"][0]["assertion_id"] = "AT-02-A02"
        other["forbidden_actions"][0]["assertion_id"] = "AT-02-F02"
        cases["cases"][0]["variants"].append(other)
        self.save(case_path, cases)
        scope["cases"][0]["case_sha256"] = hashlib.sha256(json.dumps(cases["cases"][0],
            sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
        scope["cases"][0]["variants"].append({"variant_id": "other", "assertion_ids": ["AT-02-A02", "AT-02-F02"], "repeats": 1})
        self.write_scope(scope, manifest)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertEqual(result.returncode, 2)
        self.assertIn("missing candidate result", result.stdout)
        scope["cases"][0]["variants"][0]["assertion_ids"].remove("AT-02-F01")
        self.write_scope(scope, manifest)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("assertion", result.stdout + result.stderr)

    def test_patch_rejects_synthetic_hash_mismatch_and_source_mismatch(self):
        _, manifest = self.fixture()
        candidate_path = self.results / "at02.result.json"
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        candidate["trace"]["provenance"] = "synthetic_unit_fixture"
        self.save(candidate_path, candidate)
        manifest["records"][0]["sha256"] = self.digest(candidate_path)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("synthetic", result.stdout)
        candidate["trace"]["provenance"] = "host_capture"
        candidate["trace"]["sha256"] = "0" * 64
        self.save(candidate_path, candidate)
        manifest["records"][0]["sha256"] = self.digest(candidate_path)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertEqual(result.returncode, 1)
        self.assertIn("hash mismatch", result.stdout)
        candidate["trace"]["sha256"] = self.digest(self.results / "evidence" / "at02" / "trace.txt")
        candidate["subject_source"]["hash"] = "c" * 40
        self.save(candidate_path, candidate)
        manifest["records"][0]["sha256"] = self.digest(candidate_path)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source", result.stdout)

    def test_patch_rejects_duplicate_exposed_holdout_and_missing_ledger(self):
        scope, manifest = self.fixture()
        scope["holdouts"][1]["input_sha256"] = scope["holdouts"][0]["input_sha256"]
        self.write_scope(scope, manifest)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate", result.stdout + result.stderr)
        packet = json.loads((self.holdout / "evidence" / "patch-holdout-2" / "packet.json").read_text(encoding="utf-8"))
        scope["holdouts"][1]["input_sha256"] = hashlib.sha256(json.dumps({key: value for key, value in packet.items()
            if key != "scenario_id"}, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False).encode("utf-8")).hexdigest()
        self.write_scope(scope, manifest)
        holdout_entry = next(item for item in manifest["records"] if item["side"] == "holdout")
        exposed_input_id = scope["holdouts"][0]["input_sha256"]
        exposed_trace = copy.deepcopy(holdout_entry["holdout"]["evidence"][0])
        exposed_trace["path"] = "evidence/patch-holdout-1/trace.txt"
        manifest["holdout_exposures"] = [{"input_sha256": exposed_input_id,
                                          "evidence": [exposed_trace]}]
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exposed", result.stdout)
        manifest["holdout_exposures"] = []
        manifest.pop("attempt_ledger")
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("attempt_ledger", result.stdout + result.stderr)

    def test_patch_rejects_invalid_scope_and_unbound_scope_hash(self):
        scope, manifest = self.fixture()
        original_scope = copy.deepcopy(scope)
        scope["cases"] = []
        self.write_scope(scope, manifest)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("patch scope", result.stdout + result.stderr)
        scope = original_scope
        self.write_scope(scope, manifest)
        manifest["patch_scope_sha256"] = "0" * 64
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("scope hash", result.stdout)

    def test_patch_rejects_extra_result_and_repeated_run_identity(self):
        scope, manifest = self.fixture()
        extra = json.loads((self.results / "at02.result.json").read_text(encoding="utf-8"))
        extra["repeat_index"] = 2
        extra_path = self.save(self.results / "at02-extra.result.json", extra)
        entry = copy.deepcopy(manifest["records"][0])
        entry["path"] = extra_path.name
        entry["sha256"] = self.digest(extra_path)
        manifest["records"].append(entry)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertEqual(result.returncode, 1)
        self.assertIn("outside frozen patch scope", result.stdout)
        scope["cases"][0]["variants"][0]["repeats"] = 2
        self.write_scope(scope, manifest)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertEqual(result.returncode, 1)
        self.assertIn("independent", result.stdout)

    def test_patch_rejects_judge_who_acts_in_another_record(self):
        _, manifest = self.fixture()
        path = self.holdout / "patch-holdout-1.holdout.json"
        holdout = json.loads(path.read_text(encoding="utf-8"))
        holdout["actor"]["id"] = "judge"
        holdout["judge"]["id"] = "other-judge"
        self.save(path, holdout)
        entry = next(item for item in manifest["records"] if item["path"] == path.name)
        entry["sha256"] = self.digest(path)
        receipt_path = self.holdout / entry["evidence_root"] / "receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["actor_id"] = "judge"
        self.save(receipt_path, receipt)
        entry["holdout"]["dispatch_receipt"][0]["sha256"] = self.digest(receipt_path)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertEqual(result.returncode, 2)
        self.assertIn("independent", result.stdout)

    def test_patch_rejects_changed_case_criterion_and_holdout_rubric(self):
        _, manifest = self.fixture()
        case_path = self.cases / "routing.json"
        material = json.loads(case_path.read_text(encoding="utf-8"))
        material["cases"][0]["variants"][0]["expected_actions"][0]["criterion"] = "weaker criterion"
        self.save(case_path, material)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("case material hash", result.stdout + result.stderr)
        material["cases"][0]["variants"][0]["expected_actions"][0]["criterion"] = "correct metric"
        self.save(case_path, material)
        rubric_path = self.holdout / "evidence" / "patch-holdout-1" / "rubric.json"
        rubric_path.write_text("changed rubric", encoding="utf-8")
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("rubric", result.stdout)

    def test_patch_rejects_scope_shrunk_or_relabelled_category(self):
        scope, manifest = self.fixture()
        scope["cases"][1]["variants"].pop()
        omitted = self.results / "AT-30-applicability-unknown-r1.result.json"
        omitted_bytes = omitted.read_bytes()
        omitted.unlink()
        omitted_entry = next(item for item in manifest["records"] if item["path"] == omitted.name)
        manifest["records"].remove(omitted_entry)
        self.write_scope(scope, manifest)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required", result.stdout + result.stderr)
        omitted.write_bytes(omitted_bytes)
        manifest["records"].append(omitted_entry)
        scope["cases"][1]["variants"].append({"variant_id": "applicability-unknown",
            "assertion_ids": ["AT-30-applicability-unknown-E01", "AT-30-applicability-unknown-F01"],
            "repeats": 1})
        scope["holdouts"][1]["category"] = "authorization"
        path = self.holdout / "patch-holdout-2.holdout.json"
        holdout = json.loads(path.read_text(encoding="utf-8"))
        holdout["category"] = "authorization"
        self.save(path, holdout)
        next(item for item in manifest["records"] if item["path"] == path.name)["sha256"] = self.digest(path)
        self.write_scope(scope, manifest)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("category", result.stdout + result.stderr)

    def test_patch_requires_native_dispatch_and_authored_file_provenance(self):
        _, manifest = self.fixture()
        entry = next(item for item in manifest["records"] if item["side"] == "holdout")
        receipt = entry["holdout"].pop("dispatch_receipt")
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dispatch_receipt", result.stdout)

        entry["holdout"]["dispatch_receipt"] = receipt
        dispatched = self.holdout / entry["evidence_root"] / "dispatch.json"
        packet = json.loads((self.holdout / entry["evidence_root"] / "packet.json").read_text(encoding="utf-8"))
        changed = dict(packet, task="other")
        self.save(dispatched, changed)
        entry["holdout"]["dispatch_input"]["sha256"] = self.digest(dispatched)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertEqual(result.returncode, 1)
        self.assertIn("dispatched input differs", result.stdout)

        self.save(dispatched, packet)
        entry["holdout"]["dispatch_input"]["sha256"] = self.digest(dispatched)
        entry["holdout"]["input"]["provenance"] = "host_capture"
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("controller_sealed_input", result.stdout)

        del entry["holdout"]["input"]["provenance"]
        (self.root / "ledger.txt").write_text("mutated ledger", encoding="utf-8")
        self.write_manifest(manifest)
        result = self.verify()
        self.assertEqual(result.returncode, 1)
        self.assertIn("coordinator_index file hash mismatch", result.stdout)

    def test_patch_rejects_reduced_install_repeats_and_unknown_assertion(self):
        scope, manifest = self.fixture()
        install = next(item for item in scope["cases"] if item["case_id"] == "AT-33")
        complete = next(item for item in install["variants"] if item["variant_id"] == "complete-package-install")
        complete["repeats"] = 2
        self.write_scope(scope, manifest)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required AT-33/complete-package-install", result.stdout + result.stderr)

        complete["repeats"] = 3
        self.write_scope(scope, manifest)
        path = self.results / "at02.result.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["assertions"][0]["status"] = "unknown"
        self.save(path, record)
        manifest["records"][0]["sha256"] = self.digest(path)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertEqual(result.returncode, 2)
        self.assertIn("status is unknown", result.stdout)

    def test_patch_requires_exact_current_source_even_with_reuse_claim(self):
        _, manifest = self.fixture()
        candidate_path = self.results / "at02.result.json"
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        candidate["subject_source"]["hash"] = "c" * 40
        self.save(candidate_path, candidate)
        manifest["records"][0]["sha256"] = self.digest(candidate_path)
        manifest["records"][0]["reuse"] = {"target_hash": "a" * 40}
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exact current source", result.stdout)

        candidate["subject_source"]["hash"] = "a" * 40
        self.save(candidate_path, candidate)
        manifest["records"][0]["sha256"] = self.digest(candidate_path)
        holdout_path = self.holdout / "patch-holdout-1.holdout.json"
        holdout = json.loads(holdout_path.read_text(encoding="utf-8"))
        holdout["subject_source"]["hash"] = "c" * 40
        self.save(holdout_path, holdout)
        next(item for item in manifest["records"] if item["path"] == holdout_path.name)["sha256"] = self.digest(holdout_path)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exact current source", result.stdout)

    def test_patch_requires_candidate_dispatch_and_matching_receipt(self):
        _, manifest = self.fixture()
        entry = manifest["records"][0]
        receipt = entry.pop("dispatch_receipt")
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dispatch_receipt", result.stdout)
        entry["dispatch_receipt"] = receipt
        input_path = self.results / entry["evidence_root"] / "dispatch-input.json"
        dispatched = json.loads(input_path.read_text(encoding="utf-8"))
        dispatched["run_id"] = "different-run"
        self.save(input_path, dispatched)
        entry["dispatch_input"]["sha256"] = self.digest(input_path)
        receipt_path = self.results / entry["evidence_root"] / "dispatch-receipt.json"
        received = json.loads(receipt_path.read_text(encoding="utf-8"))
        received["dispatch_sha256"] = self.digest(input_path)
        self.save(receipt_path, received)
        entry["dispatch_receipt"]["sha256"] = self.digest(receipt_path)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dispatch input", result.stdout)

    def test_patch_install_repeats_require_distinct_actor_trace_and_native_invocation(self):
        _, manifest = self.fixture()
        first = next(item for item in manifest["records"] if item["path"] ==
                     "AT-33-complete-package-install-r1.result.json")
        second = next(item for item in manifest["records"] if item["path"] ==
                      "AT-33-complete-package-install-r2.result.json")
        first_path = self.results / first["path"]
        second_path = self.results / second["path"]
        first_record = json.loads(first_path.read_text(encoding="utf-8"))
        second_record = json.loads(second_path.read_text(encoding="utf-8"))
        second_record["actor"]["id"] = first_record["actor"]["id"]
        self.save(second_path, second_record)
        second["sha256"] = self.digest(second_path)
        receipt_path = self.results / second["evidence_root"] / "dispatch-receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["actor_id"] = second_record["actor"]["id"]
        self.save(receipt_path, receipt)
        second["dispatch_receipt"]["sha256"] = self.digest(receipt_path)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("independent native actor", result.stdout)

        second_record["actor"]["id"] = "actor-AT-33-complete-package-install-r2"
        self.save(second_path, second_record)
        second["sha256"] = self.digest(second_path)
        receipt["actor_id"] = second_record["actor"]["id"]
        first_receipt_path = self.results / first["evidence_root"] / "dispatch-receipt.json"
        first_receipt = json.loads(first_receipt_path.read_text(encoding="utf-8"))
        receipt["native_invocation_id"] = first_receipt["native_invocation_id"]
        self.save(receipt_path, receipt)
        second["dispatch_receipt"]["sha256"] = self.digest(receipt_path)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("native invocation", result.stdout)

    def test_patch_install_repeats_reject_reused_raw_trace_digest(self):
        _, manifest = self.fixture()
        first = next(item for item in manifest["records"] if item["path"] ==
                     "AT-33-complete-package-install-r1.result.json")
        second = next(item for item in manifest["records"] if item["path"] ==
                      "AT-33-complete-package-install-r2.result.json")
        source_trace = self.results / first["evidence_root"] / "trace.txt"
        target_trace = self.results / second["evidence_root"] / "trace.txt"
        target_trace.write_bytes(source_trace.read_bytes())
        path = self.results / second["path"]
        record = json.loads(path.read_text(encoding="utf-8"))
        for reference in [record["trace"], *record["actual_artifacts"],
                          *(item for assertion in record["assertions"] for item in assertion["evidence"])]:
            reference["sha256"] = self.digest(target_trace)
        for condition in second["conditions"].values():
            condition["evidence"][0]["sha256"] = self.digest(target_trace)
        self.save(path, record)
        second["sha256"] = self.digest(path)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("distinct raw trace", result.stdout)

    def test_patch_rejects_self_consistent_empty_or_relabelled_rubric(self):
        scope, manifest = self.fixture()
        entry = next(item for item in manifest["records"] if item["side"] == "holdout")
        path = self.holdout / entry["evidence_root"] / "rubric.json"
        rubric = json.loads(path.read_text(encoding="utf-8"))
        rubric["assertions"][0]["criterion"] = ""
        self.save(path, rubric)
        entry["holdout"]["rubric"]["sha256"] = self.digest(path)
        scope["holdouts"][0]["rubric_sha256"] = self.digest(path)
        self.write_scope(scope, manifest)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("rubric criterion", result.stdout)
        rubric["assertions"][0]["criterion"] = "accept only safe action"
        rubric["assertions"][0]["id"] = "different-id"
        self.save(path, rubric)
        entry["holdout"]["rubric"]["sha256"] = self.digest(path)
        scope["holdouts"][0]["rubric_sha256"] = self.digest(path)
        self.write_scope(scope, manifest)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("rubric assertion IDs", result.stdout)

    def test_patch_requires_bound_pre_dispatch_scope_seal(self):
        _, manifest = self.fixture()
        seal = manifest.pop("scope_seal")
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("scope_seal", result.stdout)
        manifest["scope_seal"] = seal
        seal_path = self.root / "scope-seal.json"
        seal_json = json.loads(seal_path.read_text(encoding="utf-8"))
        seal_json["patch_scope_sha256"] = "0" * 64
        self.save(seal_path, seal_json)
        manifest["scope_seal"]["sha256"] = self.digest(seal_path)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("scope seal", result.stdout)

    def test_patch_rejects_unrelated_holdout_receipt(self):
        _, manifest = self.fixture()
        entry = next(item for item in manifest["records"] if item["side"] == "holdout")
        path = self.holdout / entry["evidence_root"] / "receipt.json"
        receipt = json.loads(path.read_text(encoding="utf-8"))
        receipt["scenario_id"] = "unrelated-scenario"
        self.save(path, receipt)
        entry["holdout"]["dispatch_receipt"][0]["sha256"] = self.digest(path)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dispatch receipt", result.stdout)

    def test_patch_rejects_extra_evaluator_fields_in_candidate_dispatch(self):
        _, manifest = self.fixture()
        entry = manifest["records"][0]
        path = self.results / entry["evidence_root"] / "dispatch-input.json"
        dispatched = json.loads(path.read_text(encoding="utf-8"))
        dispatched["expected_actions"] = [{"assertion_id": "AT-02-A01"}]
        self.save(path, dispatched)
        entry["dispatch_input"]["sha256"] = self.digest(path)
        receipt_path = self.results / entry["evidence_root"] / "dispatch-receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["dispatch_sha256"] = self.digest(path)
        self.save(receipt_path, receipt)
        entry["dispatch_receipt"]["sha256"] = self.digest(receipt_path)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exact field set", result.stdout)

    def test_patch_rejects_evaluator_fields_in_sealed_and_dispatched_holdout(self):
        scope, manifest = self.fixture()
        entry = next(item for item in manifest["records"] if item["side"] == "holdout")
        root = self.holdout / entry["evidence_root"]
        packet_path, dispatched_path = root / "packet.json", root / "dispatch.json"
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        packet["assertions"] = [{"id": "PATCH-H1-A01", "status": "pass"}]
        self.save(packet_path, packet)
        self.save(dispatched_path, packet)
        entry["holdout"]["input"]["sha256"] = self.digest(packet_path)
        entry["holdout"]["dispatch_input"]["sha256"] = self.digest(dispatched_path)
        receipt_path = root / "receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["dispatch_sha256"] = self.digest(dispatched_path)
        self.save(receipt_path, receipt)
        entry["holdout"]["dispatch_receipt"][0]["sha256"] = self.digest(receipt_path)
        scope["holdouts"][0]["input_sha256"] = hashlib.sha256(json.dumps({key: value for key, value in packet.items()
            if key != "scenario_id"}, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False).encode("utf-8")).hexdigest()
        self.write_scope(scope, manifest)
        self.write_manifest(manifest)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exact field set", result.stdout)
