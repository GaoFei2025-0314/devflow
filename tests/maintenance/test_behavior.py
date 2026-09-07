import copy
import hashlib
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

    def test_release_profile_is_explicitly_unimplemented_and_cannot_pass(self):
        self.write_cases()
        self.write_result(self.result_record())

        result = self.run_checker(
            "verify", "--cases", self.cases, "--results", self.results,
            "--profile", "release", "--ids", "AT-03",
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("release profile is not implemented", result.stderr)


if __name__ == "__main__":
    unittest.main()
