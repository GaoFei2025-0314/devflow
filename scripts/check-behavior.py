#!/usr/bin/env python3
"""Validate behavior cases, prepare blind inputs, and check evidence material."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


CASE_ID = re.compile(r"^AT-(?:0[1-9]|[1-3][0-9]|40)$")
REQUIREMENT_ID = re.compile(r"^FR-(?:0[1-9]|[1-3][0-9]|40)$")
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SOURCE_HASH = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
EXPECTED_CASE_IDS = {f"AT-{number:02d}" for number in range(1, 41)}
CAPTURE_PROVENANCE = {"host_capture", "synthetic_unit_fixture"}
ALL_PROVENANCE = CAPTURE_PROVENANCE | {"subject_self_report"}


class InputError(Exception):
    """A command input could not be interpreted safely."""


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate case material")
    validate_parser.add_argument("--cases", required=True)
    validate_parser.add_argument("--ids", help="comma-separated AT IDs")

    prepare_parser = subparsers.add_parser("prepare", help="prepare blind execution packets")
    prepare_parser.add_argument("--cases", required=True)
    prepare_parser.add_argument("--ids", required=True, help="comma-separated AT IDs")
    prepare_parser.add_argument("--out", required=True)

    verify_parser = subparsers.add_parser("verify", help="verify recorded evidence material")
    verify_parser.add_argument("--cases", required=True)
    verify_parser.add_argument("--results", required=True)
    verify_parser.add_argument("--profile", required=True, choices=("checkpoint", "release"))
    verify_parser.add_argument("--ids", help="comma-separated AT IDs")
    return parser.parse_args()


def plural(count: int, singular: str) -> str:
    return singular if count == 1 else singular + "s"


def parse_ids(value: str | None) -> list[str] | None:
    if value is None:
        return None
    values = value.split(",")
    if not values or any(item != item.strip() or not item for item in values):
        raise InputError("--ids must be a comma-separated list without blank entries or whitespace")
    if len(set(values)) != len(values):
        raise InputError("--ids contains a duplicate case ID")
    for case_id in values:
        if not CASE_ID.fullmatch(case_id):
            raise InputError(f"invalid case ID in --ids: {case_id!r}")
    return values


def read_json(path: Path, label: str) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeError as error:
        raise InputError(f"{label} is not valid UTF-8: {error}") from error
    except OSError as error:
        raise InputError(f"cannot read {label}: {error}") from error
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise InputError(
            f"invalid JSON in {label} at line {error.lineno}, column {error.colno}: {error.msg}"
        ) from error


def require_object(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError(f"{location} must be an object")
    return value


def require_nonempty_string(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{location} must be a non-empty string")
    return value


def require_string_array(value: Any, location: str, *, nonempty: bool) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        qualifier = "non-empty " if nonempty else ""
        raise InputError(f"{location} must be a {qualifier}array of strings")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise InputError(f"{location} must be a{' non-empty' if nonempty else ''} array of strings")
    return value


def required_field(mapping: dict[str, Any], field: str, location: str) -> Any:
    if field not in mapping:
        raise InputError(f"{location}.{field} is required")
    return mapping[field]


def load_cases(cases_directory: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not cases_directory.is_dir():
        raise InputError(f"cases path is not a directory: {cases_directory}")
    try:
        root = cases_directory.resolve()
        paths = sorted(cases_directory.glob("*.json"), key=lambda path: path.name)
    except (OSError, RuntimeError, ValueError) as error:
        raise InputError(f"cannot enumerate cases directory {cases_directory}: {error}") from error
    if not paths:
        raise InputError(f"cases directory contains no JSON files: {cases_directory}")

    cases: list[dict[str, Any]] = []
    errors: list[str] = []
    case_locations: dict[str, str] = {}
    assertion_locations: dict[str, str] = {}
    for path in paths:
        try:
            resolved = path.resolve()
            resolved.relative_to(root)
        except ValueError as error:
            raise InputError(f"case file escapes cases directory: {path.name}") from error
        except (OSError, RuntimeError) as error:
            raise InputError(f"invalid case file path {path.name!r}: {error}") from error
        document = require_object(read_json(path, path.name), path.name)
        if type(document.get("schema_version")) is not int or document["schema_version"] != 1:
            raise InputError(f"{path.name}.schema_version must be the integer 1")
        document_cases = document.get("cases")
        if not isinstance(document_cases, list) or not document_cases:
            raise InputError(f"{path.name}.cases must be a non-empty array")
        for case_index, raw_case in enumerate(document_cases):
            location = f"{path.name}.cases[{case_index}]"
            case = require_object(raw_case, location)
            case_id = require_nonempty_string(required_field(case, "id", location), f"{location}.id")
            if not CASE_ID.fullmatch(case_id):
                errors.append(f"{location}.id is not a valid AT-01..AT-40 ID: {case_id!r}")
            if case_id in case_locations:
                errors.append(f"{location}: duplicate case '{case_id}' (first at {case_locations[case_id]})")
            else:
                case_locations[case_id] = location

            requirement_ids = require_string_array(
                required_field(case, "requirement_ids", location),
                f"{location}.requirement_ids",
                nonempty=True,
            )
            if len(set(requirement_ids)) != len(requirement_ids):
                errors.append(f"{location}.requirement_ids contains a duplicate")
            for requirement_id in requirement_ids:
                if not REQUIREMENT_ID.fullmatch(requirement_id):
                    errors.append(f"{location}: invalid requirement ID {requirement_id!r}")

            variants = required_field(case, "variants", location)
            if not isinstance(variants, list) or not variants:
                raise InputError(f"{location}.variants must be a non-empty array")
            variant_locations: dict[str, str] = {}
            for variant_index, raw_variant in enumerate(variants):
                variant_location = f"{location}.variants[{variant_index}]"
                variant = require_object(raw_variant, variant_location)
                variant_id = require_nonempty_string(
                    required_field(variant, "id", variant_location), f"{variant_location}.id"
                )
                if not SAFE_ID.fullmatch(variant_id):
                    errors.append(f"{variant_location}.id is not an input-safe stable ID: {variant_id!r}")
                if variant_id in variant_locations:
                    errors.append(
                        f"{variant_location}: duplicate variant '{variant_id}' "
                        f"(first at {variant_locations[variant_id]})"
                    )
                else:
                    variant_locations[variant_id] = variant_location
                given = required_field(variant, "given", variant_location)
                if not isinstance(given, dict):
                    raise InputError(f"{variant_location}.given must be an object")
                require_nonempty_string(
                    required_field(variant, "when", variant_location), f"{variant_location}.when"
                )
                require_string_array(
                    required_field(variant, "allowed_capabilities", variant_location),
                    f"{variant_location}.allowed_capabilities",
                    nonempty=False,
                )
                for action_field in ("expected_actions", "forbidden_actions"):
                    actions = required_field(variant, action_field, variant_location)
                    if not isinstance(actions, list):
                        raise InputError(f"{variant_location}.{action_field} must be an array")
                    if not actions:
                        errors.append(
                            f"{variant_location}.{action_field} must contain at least one assertion"
                        )
                    for action_index, raw_action in enumerate(actions):
                        action_location = f"{variant_location}.{action_field}[{action_index}]"
                        action = require_object(raw_action, action_location)
                        assertion_id = require_nonempty_string(
                            required_field(action, "assertion_id", action_location),
                            f"{action_location}.assertion_id",
                        )
                        require_nonempty_string(
                            required_field(action, "criterion", action_location),
                            f"{action_location}.criterion",
                        )
                        if not SAFE_ID.fullmatch(assertion_id):
                            errors.append(
                                f"{action_location}.assertion_id is not input-safe: {assertion_id!r}"
                            )
                        if assertion_id in assertion_locations:
                            errors.append(
                                f"{action_location}: duplicate assertion '{assertion_id}' "
                                f"(first at {assertion_locations[assertion_id]})"
                            )
                        else:
                            assertion_locations[assertion_id] = action_location
            cases.append(case)
    return cases, errors


def select_cases(
    cases: list[dict[str, Any]], selected_ids: list[str] | None, errors: list[str]
) -> list[dict[str, Any]]:
    first_by_id: dict[str, dict[str, Any]] = {}
    for case in cases:
        first_by_id.setdefault(case["id"], case)
    if selected_ids is None:
        present = set(first_by_id)
        for case_id in sorted(EXPECTED_CASE_IDS - present):
            errors.append(f"missing required case '{case_id}'")
        for case_id in sorted(present - EXPECTED_CASE_IDS):
            errors.append(f"unexpected case '{case_id}' in full scope")
        return [first_by_id[case_id] for case_id in sorted(EXPECTED_CASE_IDS & present)]
    selected: list[dict[str, Any]] = []
    for case_id in selected_ids:
        case = first_by_id.get(case_id)
        if case is None:
            errors.append(f"selected case '{case_id}' is missing")
        else:
            selected.append(case)
    return selected


def scope_line(selected_ids: list[str] | None, cases: list[dict[str, Any]], *, profile: str | None = None) -> str:
    case_count = len(cases)
    variant_count = sum(len(case["variants"]) for case in cases)
    if selected_ids is None:
        scope = "full AT-01..AT-40"
    else:
        scope = "selected " + ",".join(selected_ids)
    prefix = f"{profile} " if profile else ""
    return (
        f"SCOPE: {prefix}{scope} ({case_count} {plural(case_count, 'case')}, "
        f"{variant_count} {plural(variant_count, 'variant')})"
    )


def print_material_errors(errors: list[str]) -> None:
    for error in errors:
        print(f"ERROR: {error}")
    print(f"BEHAVIOR MATERIAL INVALID: {len(errors)} error(s)")


def validate_command(arguments: argparse.Namespace) -> int:
    selected_ids = parse_ids(arguments.ids)
    cases, errors = load_cases(Path(arguments.cases))
    selected = select_cases(cases, selected_ids, errors)
    print(scope_line(selected_ids, selected))
    if errors:
        print_material_errors(errors)
        return 1
    print(
        "BEHAVIOR MATERIAL VALID: authoring structure is valid; "
        "no actor behavior or semantic assertion was executed"
    )
    return 0


def prepare_command(arguments: argparse.Namespace) -> int:
    output = Path(arguments.out)
    try:
        if output.exists() or output.is_symlink():
            raise InputError(f"output path already exists; choose a new directory: {output}")
        if not output.parent.is_dir():
            raise InputError(f"output parent is not an existing directory: {output.parent}")
    except (OSError, RuntimeError, ValueError) as error:
        if isinstance(error, InputError):
            raise
        raise InputError(f"cannot inspect output path {output}: {error}") from error

    selected_ids = parse_ids(arguments.ids)
    cases, errors = load_cases(Path(arguments.cases))
    selected = select_cases(cases, selected_ids, errors)
    print(scope_line(selected_ids, selected))
    if errors:
        print_material_errors(errors)
        return 1

    packets: list[tuple[str, dict[str, Any]]] = []
    packet_names: dict[str, str] = {}
    packet_errors: list[str] = []
    for case in selected:
        for variant in case["variants"]:
            packet = {
                "case_id": case["id"],
                "variant_id": variant["id"],
                "given": variant["given"],
                "when": variant["when"],
                "allowed_capabilities": variant["allowed_capabilities"],
            }
            filename = f"{case['id']}--{variant['id']}.json"
            portable_name = filename.casefold()
            previous_name = packet_names.get(portable_name)
            if previous_name is not None:
                packet_errors.append(
                    f"portable packet filename collision: {previous_name} and {filename}"
                )
            else:
                packet_names[portable_name] = filename
            packets.append((filename, packet))
    if packet_errors:
        for error in packet_errors:
            print(f"ERROR: {error}")
        print(f"PACKET PREPARATION FAILED: {len(packet_errors)} collision(s)")
        return 1
    try:
        output.mkdir()
        for filename, packet in packets:
            (output / filename).write_text(
                json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
    except (OSError, UnicodeError, RuntimeError, ValueError) as error:
        raise InputError(f"cannot write execution packets to {output}: {error}") from error
    print(f"PREPARED: {len(packets)} blind execution packet(s) in new directory {output}")
    return 0


def validate_result_shape(record: Any, location: str) -> dict[str, Any]:
    result = require_object(record, location)
    if type(result.get("schema_version")) is not int or result["schema_version"] != 1:
        raise InputError(f"{location}.schema_version must be the integer 1")
    for field in ("run_id", "case_id", "variant_id"):
        value = require_nonempty_string(required_field(result, field, location), f"{location}.{field}")
        pattern = CASE_ID if field == "case_id" else SAFE_ID
        if not pattern.fullmatch(value):
            raise InputError(f"{location}.{field} is not an input-safe ID: {value!r}")
    repeat_index = required_field(result, "repeat_index", location)
    if type(repeat_index) is not int or repeat_index < 1:
        raise InputError(f"{location}.repeat_index must be a positive integer")

    source = require_object(required_field(result, "subject_source", location), f"{location}.subject_source")
    for field in ("version", "hash"):
        value = required_field(source, field, f"{location}.subject_source")
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise InputError(f"{location}.subject_source.{field} must be null or a non-empty string")
    source_hash = source["hash"]
    if source_hash is not None and not SOURCE_HASH.fullmatch(source_hash):
        raise InputError(
            f"{location}.subject_source.hash must be null, a 40-character Git SHA, "
            "or a 64-character SHA-256 digest"
        )
    actor = require_object(required_field(result, "actor", location), f"{location}.actor")
    require_nonempty_string(required_field(actor, "id", f"{location}.actor"), f"{location}.actor.id")
    model = require_object(required_field(result, "model", location), f"{location}.model")
    model_id = required_field(model, "id", f"{location}.model")
    if model_id is not None and (not isinstance(model_id, str) or not model_id.strip()):
        raise InputError(f"{location}.model.id must be null or a non-empty string")
    if not isinstance(required_field(model, "parameters", f"{location}.model"), dict):
        raise InputError(f"{location}.model.parameters must be an object")
    host = require_object(required_field(result, "host", location), f"{location}.host")
    host_id = required_field(host, "id", f"{location}.host")
    if host_id is not None and (not isinstance(host_id, str) or not host_id.strip()):
        raise InputError(f"{location}.host.id must be null or a non-empty string")
    digest = require_nonempty_string(
        required_field(result, "conditions_digest", location), f"{location}.conditions_digest"
    )
    if not SHA256.fullmatch(digest):
        raise InputError(f"{location}.conditions_digest must be a lowercase SHA-256 digest")

    actions = required_field(result, "actual_actions", location)
    if not isinstance(actions, list) or not actions:
        raise InputError(f"{location}.actual_actions must be a non-empty array")
    for index, raw_action in enumerate(actions):
        action_location = f"{location}.actual_actions[{index}]"
        action = require_object(raw_action, action_location)
        for field in ("action", "target", "outcome"):
            require_nonempty_string(required_field(action, field, action_location), f"{action_location}.{field}")
    artifacts = required_field(result, "actual_artifacts", location)
    if not isinstance(artifacts, list):
        raise InputError(f"{location}.actual_artifacts must be an array")
    assertions = required_field(result, "assertions", location)
    if not isinstance(assertions, list) or not assertions:
        raise InputError(f"{location}.assertions must be a non-empty array")
    judge = require_object(required_field(result, "judge", location), f"{location}.judge")
    for field in ("id", "type"):
        require_nonempty_string(required_field(judge, field, f"{location}.judge"), f"{location}.judge.{field}")
    require_string_array(
        required_field(result, "evidence_limits", location), f"{location}.evidence_limits", nonempty=False
    )
    return result


def load_results(results_directory: Path) -> list[tuple[str, dict[str, Any]]]:
    if not results_directory.is_dir():
        raise InputError(f"results path is not a directory: {results_directory}")
    try:
        root = results_directory.resolve()
        paths = sorted(results_directory.glob("*.result.json"), key=lambda path: path.name)
    except (OSError, RuntimeError, ValueError) as error:
        raise InputError(f"cannot enumerate results directory {results_directory}: {error}") from error
    if not paths:
        raise InputError(f"results directory contains no *.result.json files: {results_directory}")
    results: list[tuple[str, dict[str, Any]]] = []
    for path in paths:
        try:
            path.resolve().relative_to(root)
        except ValueError as error:
            raise InputError(f"result file escapes results directory: {path.name}") from error
        except (OSError, RuntimeError) as error:
            raise InputError(f"invalid result file path {path.name!r}: {error}") from error
        results.append((path.name, validate_result_shape(read_json(path, path.name), path.name)))
    return results


def check_evidence_reference(
    raw_reference: Any,
    location: str,
    results_directory: Path,
    detected: list[str],
    insufficient: list[str],
) -> str | None:
    if not isinstance(raw_reference, dict):
        insufficient.append(f"{location}: evidence reference must be an object")
        return None
    path_value = raw_reference.get("path")
    digest = raw_reference.get("sha256")
    provenance = raw_reference.get("provenance")
    if not isinstance(path_value, str) or not path_value:
        insufficient.append(f"{location}: evidence path must be a non-empty string")
        return None
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        insufficient.append(f"{location}: evidence sha256 must be a lowercase SHA-256 digest")
        return None
    if not isinstance(provenance, str) or provenance not in ALL_PROVENANCE:
        insufficient.append(f"{location}: evidence provenance must identify capture or subject self-report")
        return None
    try:
        declared = Path(path_value)
        if declared.is_absolute() or "\\" in path_value:
            insufficient.append(f"{location}: evidence path must be portable and relative: {path_value!r}")
            return provenance
        if ".." in declared.parts:
            insufficient.append(f"{location}: path escapes results directory: {path_value!r}")
            return provenance
        root = results_directory.resolve()
        resolved = (results_directory / declared).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            insufficient.append(f"{location}: path escapes results directory: {path_value!r}")
            return provenance
    except (OSError, RuntimeError, ValueError) as error:
        insufficient.append(f"{location}: invalid evidence path {path_value!r}: {error}")
        return provenance
    try:
        is_file = resolved.is_file()
    except (OSError, RuntimeError, ValueError) as error:
        insufficient.append(f"{location}: cannot inspect evidence file {path_value}: {error}")
        return provenance
    if not is_file:
        insufficient.append(f"{location}: referenced evidence file is missing: {path_value}")
        return provenance
    if resolved.name.endswith(".result.json"):
        insufficient.append(f"{location}: a result declaration cannot be its own evidence: {path_value}")
        return provenance
    try:
        actual_digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
    except OSError as error:
        insufficient.append(f"{location}: cannot read evidence file {path_value}: {error}")
        return provenance
    if actual_digest != digest:
        detected.append(f"{location}: evidence hash mismatch for {path_value}")
    return provenance


def verify_command(arguments: argparse.Namespace) -> int:
    if arguments.profile == "release":
        raise InputError(
            "release profile is not implemented in T03.1; T30 must add repeats, baseline, "
            "holdout, and cost comparison before release verification can pass"
        )
    selected_ids = parse_ids(arguments.ids)
    cases, material_errors = load_cases(Path(arguments.cases))
    selected = select_cases(cases, selected_ids, material_errors)
    print(scope_line(selected_ids, selected, profile="checkpoint"))
    if material_errors:
        print_material_errors(material_errors)
        return 1

    result_items = load_results(Path(arguments.results))
    results_directory = Path(arguments.results)
    expected_variants: dict[tuple[str, str], set[str]] = {}
    for case in selected:
        for variant in case["variants"]:
            assertions = {
                action["assertion_id"]
                for field in ("expected_actions", "forbidden_actions")
                for action in variant[field]
            }
            expected_variants[(case["id"], variant["id"])] = assertions

    detected: list[str] = []
    insufficient: list[str] = []
    seen_runs: set[tuple[str, str, int]] = set()
    seen_variants: set[tuple[str, str]] = set()
    run_ids: set[str] = set()
    status_counts = {"pass": 0, "fail": 0, "unknown": 0}
    synthetic_records = 0
    unknown_model_records = 0
    unknown_host_records = 0
    unknown_source_records = 0

    for filename, result in result_items:
        identity = f"{filename} ({result['case_id']}/{result['variant_id']} repeat {result['repeat_index']})"
        run_ids.add(result["run_id"])
        variant_key = (result["case_id"], result["variant_id"])
        repeat_key = (result["case_id"], result["variant_id"], result["repeat_index"])
        if variant_key not in expected_variants:
            scope_name = "AT-01..AT-40" if selected_ids is None else ",".join(selected_ids)
            detected.append(f"{identity}: result is outside selected scope {scope_name}")
        else:
            seen_variants.add(variant_key)
        if repeat_key in seen_runs:
            detected.append(f"{identity}: duplicate case/variant/repeat result")
        seen_runs.add(repeat_key)

        actor_id = result["actor"]["id"]
        if result["judge"]["id"] == actor_id:
            insufficient.append(f"{identity}: judge identity must be distinct from actor identity")
        model_unknown = result["model"]["id"] is None
        host_unknown = result["host"]["id"] is None
        source_unknown = (
            result["subject_source"]["version"] is None
            or result["subject_source"]["hash"] is None
        )
        unknown_model_records += int(model_unknown)
        unknown_host_records += int(host_unknown)
        unknown_source_records += int(source_unknown)
        if source_unknown and not result["evidence_limits"]:
            insufficient.append(f"{identity}: unknown subject source requires evidence_limits")
        if (model_unknown or host_unknown) and not result["evidence_limits"]:
            insufficient.append(f"{identity}: unknown model or host requires evidence_limits")

        record_is_synthetic = False
        for index, reference in enumerate(result["actual_artifacts"]):
            provenance = check_evidence_reference(
                reference, f"{identity}.actual_artifacts[{index}]", results_directory,
                detected, insufficient,
            )
            record_is_synthetic |= provenance == "synthetic_unit_fixture"
        if "trace" not in result:
            insufficient.append(f"{identity}: trace is required")
            trace_provenance = None
        else:
            trace_provenance = check_evidence_reference(
                result["trace"], f"{identity}.trace", results_directory, detected, insufficient
            )
            record_is_synthetic |= trace_provenance == "synthetic_unit_fixture"
            if trace_provenance == "subject_self_report":
                insufficient.append(f"{identity}: subject self-report cannot be the raw trace")
        expected_assertions = expected_variants.get(variant_key, set())
        seen_assertions: set[str] = set()
        for index, raw_assertion in enumerate(result["assertions"]):
            location = f"{identity}.assertions[{index}]"
            if not isinstance(raw_assertion, dict):
                raise InputError(f"{location} must be an object")
            assertion_id = require_nonempty_string(
                required_field(raw_assertion, "id", location), f"{location}.id"
            )
            status = required_field(raw_assertion, "status", location)
            if not isinstance(status, str) or status not in status_counts:
                raise InputError(f"{location}.status must be pass, fail, or unknown")
            evidence = required_field(raw_assertion, "evidence", location)
            if not isinstance(evidence, list):
                raise InputError(f"{location}.evidence must be an array")
            status_counts[status] += 1
            if assertion_id in seen_assertions:
                detected.append(f"{identity}: duplicate assertion '{assertion_id}'")
            seen_assertions.add(assertion_id)
            if expected_assertions and assertion_id not in expected_assertions:
                detected.append(f"{identity}: unknown assertion '{assertion_id}'")
            independent_capture = False
            for evidence_index, reference in enumerate(evidence):
                provenance = check_evidence_reference(
                    reference, f"{location}.evidence[{evidence_index}]", results_directory,
                    detected, insufficient,
                )
                independent_capture |= provenance in CAPTURE_PROVENANCE
                record_is_synthetic |= provenance == "synthetic_unit_fixture"
            if status == "pass" and not independent_capture:
                insufficient.append(f"{identity}: assertion '{assertion_id}' pass has no independent capture evidence")
            elif status == "fail":
                detected.append(f"{identity}: assertion '{assertion_id}' status is fail")
            elif status == "unknown":
                insufficient.append(f"{identity}: assertion '{assertion_id}' status is unknown")
        for assertion_id in sorted(expected_assertions - seen_assertions):
            insufficient.append(f"{identity}: missing required assertion '{assertion_id}'")
        synthetic_records += int(record_is_synthetic)

    if len(run_ids) > 1:
        detected.append("results directory contains multiple run_id values")
    for case_id, variant_id in sorted(set(expected_variants) - seen_variants):
        insufficient.append(f"missing result for {case_id}/{variant_id}")

    print(
        "RESULT COUNTS: "
        f"records={len(result_items)}; assertions: pass={status_counts['pass']} "
        f"fail={status_counts['fail']} unknown={status_counts['unknown']}; "
        f"synthetic_fixture_records={synthetic_records}; "
        f"unknown_source_records={unknown_source_records}; "
        f"unknown_model_records={unknown_model_records}; unknown_host_records={unknown_host_records}"
    )
    for error in detected:
        print(f"FAIL: {error}")
    for error in insufficient:
        print(f"INSUFFICIENT: {error}")
    print(
        "BOUNDARY: this checker verifies material shape, scope, hashes, and resolvable references; "
        "it does not authenticate semantic truth, which an independent reviewer (agent or human) "
        "must inspect"
    )
    if detected:
        print(f"CHECKPOINT FAILED: {len(detected)} detected failure(s)")
        return 1
    if insufficient:
        print(f"CHECKPOINT INSUFFICIENT: {len(insufficient)} evidence gap(s)")
        return 2
    print("CHECKPOINT MATERIAL VERIFIED: structural evidence is complete for the reported scope")
    return 0


def main() -> int:
    arguments = parse_arguments()
    try:
        if arguments.command == "validate":
            return validate_command(arguments)
        if arguments.command == "prepare":
            return prepare_command(arguments)
        return verify_command(arguments)
    except InputError as error:
        print(f"INPUT ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
