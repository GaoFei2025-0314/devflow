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
    verify_parser.add_argument("--profile", required=True, choices=("checkpoint", "release", "patch"))
    verify_parser.add_argument("--ids", help="comma-separated AT IDs")
    verify_parser.add_argument("--baseline", help="baseline results directory (release profile)")
    verify_parser.add_argument("--holdout", help="holdout scenarios directory (release profile)")
    verify_parser.add_argument("--baseline-holdout", help="paired baseline holdout directory (release profile)")
    verify_parser.add_argument("--target-candidate-source", help="target Git SHA or source SHA-256 (release)")
    verify_parser.add_argument("--release-manifest", help="bound comparison, reuse and holdout metadata JSON")
    verify_parser.add_argument("--patch-scope", help="frozen selected scope JSON (patch profile)")
    verify_parser.add_argument("--allow-synthetic-fixtures", action="store_true",
                               help="release mechanism tests only; never establishes release acceptance")
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
    return validate_run_fields(result, location)


def validate_run_fields(result: dict[str, Any], location: str, *, require_action_target: bool = True) -> dict[str, Any]:
    """Validate fields shared by ordinary and holdout execution records."""

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
        fields = ("action", "outcome")
        if require_action_target:
            fields += ("target",)
        for field in fields:
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
    declaration_suffixes = (".result.json", ".holdout.json")
    if any(path.name.lower().endswith(declaration_suffixes) for path in (declared, resolved)):
        insufficient.append(f"{location}: a result or holdout declaration cannot serve as capture evidence: {path_value}")
        return provenance
    try:
        actual_digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
    except OSError as error:
        insufficient.append(f"{location}: cannot read evidence file {path_value}: {error}")
        return provenance
    if actual_digest != digest:
        detected.append(f"{location}: evidence hash mismatch for {path_value}")
    return provenance


KEY_RELEASE_CASES = {
    "AT-03", "AT-14", "AT-20", "AT-21", "AT-22",
    "AT-23", "AT-24", "AT-25", "AT-31", "AT-33",
}
REQUIRED_KEY_REPEATS = 3
HOLDOUT_CATEGORIES = ("phase", "authorization", "evidence_invalidation", "host", "recovery")
MIN_HOLDOUT_SCENARIOS = 10
MIN_HOLDOUT_PER_CATEGORY = 2
COMPARABLE_FIELDS = ("task_input", "initial_state", "user_rules", "capabilities", "budget")
INPUT_LABELS = {"scenario_id", "case_id", "variant_id", "run_id", "repeat_index"}
PATCH_REQUIRED_VARIANTS = {
    "AT-02": ("default-off-analysis", "enabled-minimal-recording", "stopped-recording", "local-export"),
    "AT-30": ("zero-reads-no-applicable-task", "applicability-unknown"),
    "AT-31": ("untrusted-content-with-embedded-instructions",),
    "AT-33": ("flat-install-missing-shared-template", "complete-package-install",
              "single-skill-with-dependencies", "linked-install"),
}
PATCH_REQUIRED_HOLDOUT_CATEGORIES = {"install_authorization", "observability_identity"}
PATCH_CANDIDATE_DISPATCH_FIELDS = {
    "case_id", "variant_id", "run_id", "given", "when", "allowed_capabilities",
}
PATCH_HOLDOUT_PACKET_FIELDS = {
    "scenario_id", "category", "task", "initial_state", "allowed_capabilities",
}
PATCH_HOLDOUT_RECEIPT_FIELDS = {
    "scenario_id", "category", "run_id", "actor_id", "dispatch_sha256", "received",
    "native_invocation_id",
}
PATCH_FORBIDDEN_INPUT_KEYS = {
    "expected_actions", "forbidden_actions", "rubric", "assertions", "criterion", "judge",
}


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise InputError(f"comparison value is not finite JSON: {error}") from error


def contains_unknown(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"", "unknown", "unavailable", "not recorded"}
    if isinstance(value, dict):
        return any(contains_unknown(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_unknown(item) for item in value)
    return False


def release_metadata(record):
    """Return known comparison metadata; unknown values cannot prove a mismatch."""
    model_id, host_id = record["model"].get("id"), record["host"].get("id")
    parameters = record["model"].get("parameters")
    if (not isinstance(model_id, str) or contains_unknown(model_id)
            or not isinstance(host_id, str) or contains_unknown(host_id)
            or not isinstance(parameters, dict) or contains_unknown(parameters)):
        return None
    return {"model.id": model_id, "host.id": host_id, "model.parameters": parameters}


def check_capture_list(raw, location, directory, detected, insufficient) -> bool:
    """Require valid inspectable capture references, not declarations or self-report."""
    before = (len(detected), len(insufficient))
    if not isinstance(raw, list) or not raw:
        insufficient.append(f"{location}: non-empty capture evidence is required")
        return False
    for index, reference in enumerate(raw):
        provenance = check_evidence_reference(
            reference, f"{location}[{index}]", directory, detected, insufficient
        )
        if provenance not in CAPTURE_PROVENANCE:
            insufficient.append(f"{location}[{index}]: independent capture evidence is required")
    return before == (len(detected), len(insufficient))


def synthetic_reference_keys(value: Any) -> set[str]:
    """Collect unique declared synthetic references, including manifest evidence.

    These are provenance declarations, not authenticated capture classifications.
    Repeated uses of the same local path/hash are one reference identity.
    """
    found = set()
    if isinstance(value, dict):
        if (value.get("provenance") == "synthetic_unit_fixture"
                and isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str)):
            found.add(canonical_json({"path": value["path"], "sha256": value["sha256"]}))
        for item in value.values():
            found.update(synthetic_reference_keys(item))
    elif isinstance(value, list):
        for item in value:
            found.update(synthetic_reference_keys(item))
    return found


def load_release_manifest(arguments, detected, insufficient):
    target = getattr(arguments, "target_candidate_source", None)
    path = getattr(arguments, "release_manifest", None)
    if not isinstance(target, str) or not SOURCE_HASH.fullmatch(target):
        raise InputError("release requires --target-candidate-source with a lowercase Git SHA or SHA-256")
    if not path:
        raise InputError("release requires --release-manifest with explicit comparison and holdout evidence")
    manifest = require_object(read_json(Path(path), "release manifest"), "release manifest")
    version = manifest.get("schema_version")
    if type(version) is not int or version not in (1, 2):
        raise InputError("release manifest.schema_version must be the integer 1 or 2")
    if version == 2:
        collection_id = manifest.get("collection_id")
        if not isinstance(collection_id, str) or not SAFE_ID.fullmatch(collection_id):
            raise InputError("release manifest.collection_id must be an input-safe ID")
    if manifest.get("target_candidate_source") != target:
        detected.append("release manifest target_candidate_source does not match explicit target")
    records = manifest.get("records")
    if not isinstance(records, list):
        raise InputError("release manifest.records must be an array")
    entries = {}
    for index, raw in enumerate(records):
        entry = require_object(raw, f"release manifest.records[{index}]")
        side, filename = entry.get("side"), entry.get("path")
        if side not in ("candidate", "baseline", "holdout", "baseline_holdout"):
            raise InputError(f"release manifest.records[{index}].side is invalid")
        if (not isinstance(filename, str) or not filename or Path(filename).name != filename
                or "/" in filename or "\\" in filename or ":" in filename):
            raise InputError(f"release manifest.records[{index}].path must be a direct result filename")
        if not isinstance(entry.get("sha256"), str) or not SHA256.fullmatch(entry["sha256"]):
            raise InputError(f"release manifest.records[{index}].sha256 must identify the original record bytes")
        if version == 2:
            if not isinstance(entry.get("run_id"), str) or not SAFE_ID.fullmatch(entry["run_id"]):
                raise InputError(f"release manifest.records[{index}].run_id must bind an original run")
            root = entry.get("evidence_root")
            if (not isinstance(root, str) or not root or any(c in root for c in ("\\", ":", "\x00"))
                    or any(part in ("", ".", "..") for part in root.split("/"))):
                raise InputError(f"release manifest.records[{index}].evidence_root must be a canonical relative directory")
        elif "evidence_root" in entry or "run_id" in entry:
            raise InputError("per-record evidence_root and run_id require release manifest schema_version 2")
        key = (side, filename)
        if key in entries:
            detected.append(f"release manifest: duplicate binding for {side} {filename}")
        entries[key] = entry
    exposures = manifest.get("holdout_exposures")
    if not isinstance(exposures, list):
        insufficient.append("release manifest.holdout_exposures must explicitly list exposed inputs (or [])")
        exposures = []
    return target, entries, exposures, version


def collection_evidence_directories(entries, directories, detected):
    """Keep each immutable run's evidence namespace inside its result side."""
    roots, runs_by_root = {}, {}
    for key, entry in entries.items():
        side, filename = key
        directory = directories[side]
        try:
            root = (directory / entry["evidence_root"]).resolve()
            root.relative_to(directory.resolve())
        except (OSError, ValueError, RuntimeError) as error:
            raise InputError(f"{side} {filename}: evidence_root escapes or cannot be resolved") from error
        if not root.is_dir():
            raise InputError(f"{side} {filename}: evidence_root is not an existing directory")
        run_key = (side, root)
        if run_key in runs_by_root and runs_by_root[run_key] != entry["run_id"]:
            detected.append(f"{side} {filename}: evidence_root binds multiple run_id values")
        runs_by_root[run_key] = entry["run_id"]
        roots[key] = root
    return roots


def validate_assertion_shape(raw_assertion: Any, location: str) -> dict[str, Any]:
    assertion = require_object(raw_assertion, location)
    require_nonempty_string(required_field(assertion, "id", location), f"{location}.id")
    status = required_field(assertion, "status", location)
    if not isinstance(status, str) or status not in ("pass", "fail", "unknown"):
        raise InputError(f"{location}.status must be pass, fail, or unknown")
    if not isinstance(required_field(assertion, "evidence", location), list):
        raise InputError(f"{location}.evidence must be an array")
    return assertion


def check_reuse(reuse, record, entry, target, identity, directory, detected, insufficient):
    before = (len(detected), len(insufficient))
    if not isinstance(reuse, dict):
        insufficient.append(f"{identity}: old or unknown candidate source requires reviewed reuse")
        return False
    bindings = {"source_hash": record["subject_source"].get("hash"),
                "target_hash": target, "record_sha256": entry["sha256"]}
    for field, expected in bindings.items():
        if expected is None or reuse.get(field) != expected:
            insufficient.append(f"{identity}.reuse.{field}: exact source/target/record binding is required")
    claims = {
        validate_assertion_shape(item, f"{identity}.assertions[{index}]")["id"]
        for index, item in enumerate(record["assertions"])
    }
    if "loading" in record:
        claims.add("loading")
    scope = reuse.get("claim_scope")
    if not isinstance(scope, list) or any(not isinstance(x, str) for x in scope) or set(scope) != claims:
        insufficient.append(f"{identity}.reuse.claim_scope: must cover every assertion and loading claim")
    reviewer = reuse.get("reviewer")
    if (not isinstance(reviewer, dict) or not isinstance(reviewer.get("id"), str)
            or not reviewer["id"].strip() or reviewer["id"] == record["actor"]["id"]):
        insufficient.append(f"{identity}.reuse.reviewer: an identified reviewer distinct from actor is required")
    if not isinstance(reuse.get("justification"), str) or not reuse["justification"].strip():
        insufficient.append(f"{identity}.reuse.justification: dependency and claim validity reasoning is required")
    check_capture_list(reuse.get("evidence"), f"{identity}.reuse.evidence", directory, detected, insufficient)
    resources = reuse.get("resources")
    if not isinstance(resources, list) or not resources:
        insufficient.append(f"{identity}.reuse.resources: relevant source and target resource snapshots are required")
        resources = []
    seen = set()
    for index, resource in enumerate(resources):
        location = f"{identity}.reuse.resources[{index}]"
        if not isinstance(resource, dict):
            insufficient.append(f"{location}: resource must be an object")
            continue
        path = resource.get("path")
        if (not isinstance(path, str) or not path or Path(path).is_absolute()
                or ".." in Path(path).parts or "\\" in path or ":" in path):
            insufficient.append(f"{location}: canonical bundle-relative resource path is required")
        elif path in seen:
            detected.append(f"{location}: duplicate reuse resource {path}")
        seen.add(str(path))
        for side in ("source", "target"):
            check_capture_list([resource.get(side)], f"{location}.{side}", directory, detected, insufficient)
        source, destination = resource.get("source"), resource.get("target")
        if isinstance(source, dict) and isinstance(destination, dict) and source.get("sha256") != destination.get("sha256"):
            detected.append(f"{location}: changed relevant resource cannot support unchanged-source reuse")
    return before == (len(detected), len(insufficient))


def check_release_binding(entry, record, filename, side, directory, target, detected, insufficient,
                          evidence_directory):
    identity = f"{side} {filename}"
    before = (len(detected), len(insufficient))
    if entry is None:
        insufficient.append(f"{identity}: missing release manifest binding")
        return None, False
    if hashlib.sha256((directory / filename).read_bytes()).hexdigest() != entry["sha256"]:
        detected.append(f"{identity}: release manifest record hash mismatch")
    if "run_id" in entry and entry["run_id"] != record["run_id"]:
        detected.append(f"{identity}: run_id does not match original record")
    conditions = entry.get("conditions")
    values = {}
    if not isinstance(conditions, dict):
        insufficient.append(f"{identity}: explicit comparable conditions are required")
        conditions = {}
    if set(conditions) - set(COMPARABLE_FIELDS):
        detected.append(f"{identity}: conditions include fields outside the canonical comparison contract")
    for field in COMPARABLE_FIELDS:
        item = conditions.get(field)
        location = f"{identity}.conditions.{field}"
        if (not isinstance(item, dict) or "value" not in item or contains_unknown(item["value"])
                or item["value"] == {} or item["value"] == []):
            insufficient.append(f"{location}: a known explicit comparison value is required")
            continue
        values[field] = canonical_json(item["value"])
        check_capture_list(item.get("evidence"), f"{location}.evidence", evidence_directory, detected, insufficient)
    for field in ("model", "host"):
        value = record[field].get("id")
        if not isinstance(value, str) or contains_unknown(value):
            insufficient.append(f"{identity}.{field}.id: a non-empty known identity is required for release")
    source_hash = record["subject_source"].get("hash")
    if not isinstance(source_hash, str) or not SOURCE_HASH.fullmatch(source_hash):
        insufficient.append(f"{identity}.subject_source.hash: a lowercase Git SHA or SHA-256 is required")
    parameters = record["model"].get("parameters")
    if not isinstance(parameters, dict) or contains_unknown(parameters):
        insufficient.append(f"{identity}.model.parameters: an object without unknown values is required")
    source_valid = True
    if side in ("candidate", "holdout") and record["subject_source"].get("hash") != target:
        source_valid = check_reuse(entry.get("reuse"), record, entry, target, identity,
                                   evidence_directory, detected, insufficient)
    valid = before == (len(detected), len(insufficient))
    return values if valid else None, source_valid and valid


def holdout_input_identity(raw, location, directory, detected, insufficient):
    if not check_capture_list([raw], location, directory, detected, insufficient):
        return None
    value = read_json(directory / raw["path"], location)
    if not isinstance(value, dict):
        insufficient.append(f"{location}: blind input must be a JSON object")
        return None
    payload = {key: item for key, item in value.items() if key not in INPUT_LABELS}
    if not payload:
        insufficient.append(f"{location}: underlying input contains only identity labels")
        return None
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def validate_loading(raw: Any, location: str) -> dict[str, Any]:
    loading = require_object(raw, location)
    total_bytes = required_field(loading, "total_bytes", location)
    if total_bytes is not None and (isinstance(total_bytes, bool) or not isinstance(total_bytes, int) or total_bytes < 0):
        raise InputError(f"{location}.total_bytes must be a non-negative integer or null")
    entries = required_field(loading, "entries", location)
    if not isinstance(entries, list):
        raise InputError(f"{location}.entries must be an array")
    for index, raw_entry in enumerate(entries):
        entry = require_object(raw_entry, f"{location}.entries[{index}]")
        entry_location = f"{location}.entries[{index}]"
        require_nonempty_string(
            required_field(entry, "path", entry_location), f"{entry_location}.path"
        )
        entry_bytes = required_field(entry, "bytes", entry_location)
        if isinstance(entry_bytes, bool) or not isinstance(entry_bytes, int) or entry_bytes < 0:
            raise InputError(f"{entry_location}.bytes must be a non-negative integer")
    return loading


def validate_holdout_shape(record: Any, location: str, *, categories=HOLDOUT_CATEGORIES) -> dict[str, Any]:
    scenario = require_object(record, location)
    if type(scenario.get("schema_version")) is not int or scenario["schema_version"] != 1:
        raise InputError(f"{location}.schema_version must be the integer 1")
    scenario_id = require_nonempty_string(
        required_field(scenario, "scenario_id", location), f"{location}.scenario_id"
    )
    if not SAFE_ID.fullmatch(scenario_id):
        raise InputError(f"{location}.scenario_id is not an input-safe ID: {scenario_id!r}")
    category = required_field(scenario, "category", location)
    if not isinstance(category, str) or category not in categories:
        raise InputError(
            f"{location}.category must be one of {list(categories)}"
        )
    run_id = require_nonempty_string(required_field(scenario, "run_id", location), f"{location}.run_id")
    if not SAFE_ID.fullmatch(run_id):
        raise InputError(f"{location}.run_id is not an input-safe ID: {run_id!r}")
    if "trace" not in scenario:
        raise InputError(f"{location}.trace is required")
    # Historical schema-1 holdouts allow absent or structured target metadata.
    return validate_run_fields(scenario, location, require_action_target=False)


def load_holdout(directory: Path, *, categories=HOLDOUT_CATEGORIES) -> list[tuple[str, dict[str, Any]]]:
    if not directory.is_dir():
        raise InputError(f"holdout path is not a directory: {directory}")
    try:
        root = directory.resolve()
        paths = sorted(directory.glob("*.holdout.json"), key=lambda path: path.name)
    except (OSError, RuntimeError, ValueError) as error:
        raise InputError(f"cannot enumerate holdout directory {directory}: {error}") from error
    if not paths:
        raise InputError(f"holdout directory contains no *.holdout.json files: {directory}")
    scenarios = []
    for path in paths:
        try:
            path.resolve().relative_to(root)
        except ValueError as error:
            raise InputError(f"holdout file escapes holdout directory: {path.name}") from error
        except (OSError, RuntimeError) as error:
            raise InputError(f"invalid holdout file path {path.name!r}: {error}") from error
        scenarios.append((path.name, validate_holdout_shape(read_json(path, path.name), path.name,
                                                            categories=categories)))
    return scenarios


def walk_result_assertions(
    result: dict[str, Any],
    identity: str,
    expected_assertions: set[str],
    results_directory: Path,
    detected: list[str],
    insufficient: list[str],
    *,
    strict_statuses: bool,
    status_counts: dict[str, int],
) -> bool:
    """Walk one result's evidence and assertions; returns synthetic flag."""
    record_is_synthetic = False
    for index, reference in enumerate(result["actual_artifacts"]):
        provenance = check_evidence_reference(
            reference, f"{identity}.actual_artifacts[{index}]", results_directory,
            detected, insufficient,
        )
        record_is_synthetic |= provenance == "synthetic_unit_fixture"
    if "trace" not in result:
        insufficient.append(f"{identity}: trace is required")
    else:
        provenance = check_evidence_reference(
            result["trace"], f"{identity}.trace", results_directory, detected, insufficient
        )
        record_is_synthetic |= provenance == "synthetic_unit_fixture"
        if provenance == "subject_self_report":
            insufficient.append(f"{identity}: subject self-report cannot be the raw trace")
    seen_assertions: set[str] = set()
    for index, raw_assertion in enumerate(result["assertions"]):
        location = f"{identity}.assertions[{index}]"
        assertion = validate_assertion_shape(raw_assertion, location)
        assertion_id, status, evidence = assertion["id"], assertion["status"], assertion["evidence"]
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
            insufficient.append(
                f"{identity}: assertion '{assertion_id}' pass has no independent capture evidence"
            )
        if strict_statuses:
            if status == "fail":
                detected.append(f"{identity}: assertion '{assertion_id}' status is fail")
            elif status == "unknown":
                insufficient.append(f"{identity}: assertion '{assertion_id}' status is unknown")
    for assertion_id in sorted(expected_assertions - seen_assertions):
        insufficient.append(f"{identity}: missing required assertion '{assertion_id}'")
    return record_is_synthetic


def verify_release_command(arguments: argparse.Namespace) -> int:
    if arguments.ids:
        raise InputError("the release profile verifies the full scope; --ids is not accepted")
    missing = [
        "--" + field.replace("_", "-")
        for field in ("baseline", "holdout", "baseline_holdout")
        if not getattr(arguments, field, None)
    ]
    if missing:
        raise InputError(
            "the release profile requires " + " and ".join(missing)
        )

    cases, material_errors = load_cases(Path(arguments.cases))
    selected = select_cases(cases, None, material_errors)
    print(scope_line(None, selected, profile="release"))
    if material_errors:
        print_material_errors(material_errors)
        return 1

    results_directory = Path(arguments.results)
    candidate_items = load_results(results_directory)
    baseline_directory = Path(arguments.baseline)
    baseline_items = load_results(baseline_directory)
    holdout_items = load_holdout(Path(arguments.holdout))
    baseline_holdout_items = load_holdout(Path(arguments.baseline_holdout))

    expected_variants: dict[tuple[str, str], set[str]] = {}
    for case in selected:
        for variant in case["variants"]:
            expected_variants[(case["id"], variant["id"])] = {
                action["assertion_id"]
                for field in ("expected_actions", "forbidden_actions")
                for action in variant[field]
            }

    detected: list[str] = []
    insufficient: list[str] = []
    target_source, release_entries, exposures, manifest_version = load_release_manifest(arguments, detected, insufficient)
    directories = {"candidate": results_directory, "baseline": baseline_directory,
                   "holdout": Path(arguments.holdout), "baseline_holdout": Path(arguments.baseline_holdout)}
    evidence_directories = (collection_evidence_directories(release_entries, directories, detected)
                            if manifest_version == 2 else {})
    comparable = {"candidate": {}, "baseline": {}}
    valid_candidate_keys = set()
    used_bindings = set()
    synthetic_references = set()
    manifest_synthetic_references = set()
    fixture_mode = getattr(arguments, "allow_synthetic_fixtures", False)

    def record_synthetic(side, record, entry):
        raw_keys = synthetic_reference_keys(record)
        manifest_keys = synthetic_reference_keys(entry)
        synthetic_references.update((side, key) for key in raw_keys | manifest_keys)
        manifest_synthetic_references.update((side, key) for key in manifest_keys)
        return bool(raw_keys | manifest_keys)

    def process_side(items, directory, *, strict, run_label):
        status_counts = {"pass": 0, "fail": 0, "unknown": 0}
        runs: dict[tuple[str, str, int], dict[str, Any]] = {}
        synthetic = 0
        run_ids: set[str] = set()
        seen: set[tuple[str, str, int]] = set()
        variants_seen: set[tuple[str, str]] = set()
        for filename, result in items:
            identity = (
                f"{run_label} {filename} "
                f"({result['case_id']}/{result['variant_id']} repeat {result['repeat_index']})"
            )
            run_ids.add(result["run_id"])
            key = (result["case_id"], result["variant_id"], result["repeat_index"])
            variant_key = (result["case_id"], result["variant_id"])
            if variant_key not in expected_variants:
                detected.append(f"{identity}: result is outside the full AT-01..AT-40 scope")
            else:
                variants_seen.add(variant_key)
            if key in seen:
                detected.append(f"{identity}: duplicate case/variant/repeat result")
            seen.add(key)
            runs[key] = result
            binding_key = (run_label, filename)
            used_bindings.add(binding_key)
            evidence_directory = evidence_directories.get(binding_key, directory)
            values, source_valid = check_release_binding(
                release_entries.get(binding_key), result, filename, run_label, directory,
                target_source, detected, insufficient, evidence_directory,
            )
            is_synthetic = record_synthetic(run_label, result, release_entries.get(binding_key))
            if is_synthetic and not fixture_mode:
                values, source_valid = None, False
            comparable[run_label][key] = values
            if run_label == "candidate" and source_valid:
                valid_candidate_keys.add(key)
            if result["judge"]["id"] == result["actor"]["id"]:
                insufficient.append(f"{identity}: judge identity must be distinct from actor identity")
            source_unknown = (
                result["subject_source"]["version"] is None
                or result["subject_source"]["hash"] is None
            )
            model_unknown = result["model"]["id"] is None
            host_unknown = result["host"]["id"] is None
            if (source_unknown or model_unknown or host_unknown) and not result["evidence_limits"]:
                insufficient.append(f"{identity}: unknown source/model/host requires evidence_limits")
            raw_synthetic = walk_result_assertions(
                result, identity, expected_variants.get(variant_key, set()),
                evidence_directory, detected, insufficient,
                strict_statuses=strict, status_counts=status_counts,
            )
            synthetic += int(is_synthetic or raw_synthetic)
            if strict:
                if "loading" not in result:
                    insufficient.append(f"{identity}: release results require loading data")
                else:
                    try:
                        validate_loading(result["loading"], f"{identity}.loading")
                    except InputError as error:
                        insufficient.append(str(error))
        return status_counts, runs, synthetic, run_ids, variants_seen

    candidate_counts, candidate_runs, candidate_synthetic, candidate_run_ids, variants_seen = (
        process_side(candidate_items, results_directory, strict=True, run_label="candidate")
    )
    baseline_counts, baseline_runs, baseline_synthetic, baseline_run_ids, _ = process_side(
        baseline_items, baseline_directory, strict=False, run_label="baseline"
    )

    if manifest_version == 1 and len(candidate_run_ids) > 1:
        detected.append("candidate results directory contains multiple run_id values")
    if manifest_version == 1 and len(baseline_run_ids) > 1:
        detected.append("baseline results directory contains multiple run_id values")

    for case_id, variant_id in sorted(set(expected_variants) - variants_seen):
        insufficient.append(f"missing candidate result for {case_id}/{variant_id}")

    repeats_by_variant: dict[tuple[str, str], set[int]] = {}
    for case_id, variant_id in expected_variants:
        repeats_by_variant[(case_id, variant_id)] = set()
    for case_id, variant_id, repeat_index in valid_candidate_keys:
        repeats_by_variant.setdefault((case_id, variant_id), set()).add(repeat_index)
    for (case_id, variant_id), repeats in sorted(repeats_by_variant.items()):
        if case_id in KEY_RELEASE_CASES and len(repeats) < REQUIRED_KEY_REPEATS:
            insufficient.append(
                f"{case_id}/{variant_id}: key case requires {REQUIRED_KEY_REPEATS} repeats, "
                f"found {len(repeats)}"
            )

    valid_pair_keys = set()
    for key, candidate_result in sorted(candidate_runs.items()):
        baseline_result = baseline_runs.get(key)
        case_id, variant_id, repeat_index = key
        if baseline_result is None:
            insufficient.append(
                f"missing baseline run for {case_id}/{variant_id} repeat {repeat_index}"
            )
            continue
        baseline_metadata, candidate_metadata = release_metadata(baseline_result), release_metadata(candidate_result)
        metadata_known = baseline_metadata is not None and candidate_metadata is not None
        metadata_match = metadata_known and canonical_json(baseline_metadata) == canonical_json(candidate_metadata)
        if metadata_known and not metadata_match:
            detected.append(
                f"{key[0]}/{key[1]} repeat {repeat_index}: baseline conditions do not match "
                "candidate (model, host, or parameters differ)"
            )
        candidate_conditions = comparable["candidate"].get(key)
        baseline_conditions = comparable["baseline"].get(key)
        if candidate_conditions is not None and baseline_conditions is not None:
            differing = [field for field in COMPARABLE_FIELDS
                         if candidate_conditions[field] != baseline_conditions[field]]
            if differing:
                detected.append(f"{case_id}/{variant_id} repeat {repeat_index}: baseline conditions "
                                f"do not match candidate ({', '.join(differing)})")
            elif metadata_match and key in valid_candidate_keys:
                valid_pair_keys.add(key)

    category_counts: dict[str, int] = {}
    exposed_ids = set()
    holdout_directory = Path(arguments.holdout)
    holdout_sides = (
        ("holdout", holdout_items, holdout_directory),
        ("baseline_holdout", baseline_holdout_items, Path(arguments.baseline_holdout)),
    )
    exposure_synthetic = synthetic_reference_keys(exposures)
    synthetic_references.update(("holdout", key) for key in exposure_synthetic)
    manifest_synthetic_references.update(("holdout", key) for key in exposure_synthetic)
    for index, exposure in enumerate(exposures):
        location = f"holdout_exposures[{index}]"
        if not isinstance(exposure, dict):
            insufficient.append(f"{location}: exposure must be an object")
            continue
        input_id = holdout_input_identity(exposure.get("input"), f"{location}.input",
                                          holdout_directory, detected, insufficient)
        check_capture_list(exposure.get("evidence"), f"{location}.evidence", holdout_directory,
                           detected, insufficient)
        if input_id:
            exposed_ids.add(input_id)
    # Read all promoted identities before counting, regardless of filename order.
    for side, items, directory in holdout_sides:
        for filename, scenario in items:
            entry = release_entries.get((side, filename), {})
            evidence_directory = evidence_directories.get((side, filename), directory)
            holdout = entry.get("holdout")
            if isinstance(holdout, dict) and holdout.get("exposure") == "promoted_regression":
                input_id = holdout_input_identity(holdout.get("input"), f"{side} {filename}.holdout.input",
                                                  evidence_directory, detected, insufficient)
                if input_id:
                    exposed_ids.add(input_id)

    holdout_runs, holdout_statistics = {}, {}
    for side, items, directory in holdout_sides:
        runs, input_ids, run_ids = {}, set(), set()
        counts = {"pass": 0, "fail": 0, "unknown": 0}
        synthetic = 0
        for filename, scenario in items:
            scenario_id = scenario["scenario_id"]
            identity = f"{side} {filename} ({scenario_id})"
            if scenario_id in runs:
                detected.append(f"{identity}: duplicate scenario_id '{scenario_id}'")
            run_ids.add(scenario["run_id"])
            binding_key = (side, filename)
            used_bindings.add(binding_key)
            entry = release_entries.get(binding_key)
            evidence_directory = evidence_directories.get(binding_key, directory)
            values, source_valid = check_release_binding(entry, scenario, filename, side, directory,
                                                         target_source, detected, insufficient, evidence_directory)
            holdout = entry.get("holdout") if entry else None
            input_id, eligible = None, False
            if not isinstance(holdout, dict):
                insufficient.append(f"{identity}: holdout input identity and exposure evidence are required")
            else:
                input_id = holdout_input_identity(holdout.get("input"), f"{identity}.input",
                                                  evidence_directory, detected, insufficient)
                exposure_valid = check_capture_list(holdout.get("evidence"), f"{identity}.exposure.evidence",
                                                    evidence_directory, detected, insufficient)
                duplicate = input_id is not None and input_id in input_ids
                if duplicate:
                    detected.append(f"{identity}: duplicate underlying holdout input")
                if input_id:
                    input_ids.add(input_id)
                status = holdout.get("exposure")
                if status not in ("unexposed", "promoted_regression"):
                    insufficient.append(f"{identity}: holdout exposure is unknown or missing")
                if input_id in exposed_ids and status == "unexposed":
                    detected.append(f"{identity}: exposed input cannot be an unexposed holdout")
                eligible = bool(source_valid and exposure_valid and input_id and not duplicate
                                and status == "unexposed" and input_id not in exposed_ids)
            if scenario["judge"]["id"] == scenario["actor"]["id"]:
                insufficient.append(f"{identity}: judge identity must be distinct from actor identity")
            if not isinstance(scenario["model"].get("parameters"), dict):
                insufficient.append(f"{identity}: model parameters are required for holdout pairing")
                eligible = False
            raw_synthetic = walk_result_assertions(
                scenario, identity, set(), evidence_directory, detected, insufficient,
                strict_statuses=side == "holdout", status_counts=counts,
            )
            is_synthetic = record_synthetic(side, scenario, entry) or raw_synthetic
            synthetic += int(is_synthetic)
            if (is_synthetic or exposure_synthetic) and not fixture_mode:
                values, eligible = None, False
            runs[scenario_id] = {"record": scenario, "input_id": input_id,
                                 "conditions": values, "eligible": eligible}
        if manifest_version == 1 and len(run_ids) > 1:
            detected.append(f"{side} results directory contains multiple run_id values")
        holdout_runs[side] = runs
        holdout_statistics[side] = {"counts": counts, "synthetic": synthetic, "records": len(items)}

    baseline_used = set()
    for scenario_id, candidate in holdout_runs["holdout"].items():
        baseline_id = scenario_id
        baseline = holdout_runs["baseline_holdout"].get(baseline_id)
        if baseline is None and candidate["input_id"] is not None:
            matches = [(key, item) for key, item in holdout_runs["baseline_holdout"].items()
                       if item["input_id"] == candidate["input_id"]]
            if len(matches) == 1:
                baseline_id, baseline = matches[0]
        if baseline is None:
            insufficient.append(f"missing baseline holdout counterpart for {scenario_id}")
            continue
        if baseline_id in baseline_used:
            detected.append(f"{scenario_id}: baseline holdout counterpart is reused by another scenario")
        baseline_used.add(baseline_id)
        different = []
        if candidate["input_id"] is not None and baseline["input_id"] is not None:
            if candidate["input_id"] != baseline["input_id"]:
                different.append("underlying input")
        if candidate["record"]["category"] != baseline["record"]["category"]:
            different.append("category")
        for field in COMPARABLE_FIELDS:
            if candidate["conditions"] is not None and baseline["conditions"] is not None:
                if candidate["conditions"][field] != baseline["conditions"][field]:
                    different.append(field)
        left, right = release_metadata(candidate["record"]), release_metadata(baseline["record"])
        if left is not None and right is not None:
            for field in left:
                if canonical_json(left[field]) != canonical_json(right[field]):
                    different.append(field)
        if different:
            detected.append(f"{scenario_id}: baseline holdout conditions do not match candidate "
                            f"({', '.join(different)})")
        elif candidate["eligible"] and baseline["eligible"]:
            category = candidate["record"]["category"]
            category_counts[category] = category_counts.get(category, 0) + 1
    for scenario_id in sorted(set(holdout_runs["baseline_holdout"]) - baseline_used):
        insufficient.append(f"missing candidate holdout counterpart for {scenario_id}")
    for side, filename in sorted(set(release_entries) - used_bindings):
        insufficient.append(f"release manifest binding has no submitted record: {side} {filename}")
    if sum(category_counts.values()) < MIN_HOLDOUT_SCENARIOS:
        insufficient.append(
            f"holdout has {sum(category_counts.values())} scenario(s), requires {MIN_HOLDOUT_SCENARIOS}"
        )
    for category in HOLDOUT_CATEGORIES:
        count = category_counts.get(category, 0)
        if count < MIN_HOLDOUT_PER_CATEGORY:
            insufficient.append(
                f"holdout category '{category}' has {count} scenario(s), "
                f"requires {MIN_HOLDOUT_PER_CATEGORY}"
            )

    paired_loading = []
    for key, candidate_result in candidate_runs.items():
        if key not in valid_pair_keys:
            continue
        baseline_result = baseline_runs.get(key)
        if baseline_result is None or "loading" not in baseline_result:
            continue
        candidate_bytes = candidate_result.get("loading", {}).get("total_bytes")
        baseline_bytes = baseline_result["loading"].get("total_bytes")
        if candidate_bytes is not None and baseline_bytes is not None:
            paired_loading.append((baseline_bytes, candidate_bytes))

    def median(values: list[int]) -> int | None:
        if not values:
            return None
        ordered = sorted(values)
        middle = len(ordered) // 2
        if len(ordered) % 2:
            return ordered[middle]
        return (ordered[middle - 1] + ordered[middle]) // 2

    if not paired_loading:
        insufficient.append(
            "comparison has no paired loading data; the exploratory loading "
            "metric requires at least one baseline/candidate pair with recorded "
            "total_bytes (null loading data cannot support any loading claim)"
        )

    print(
        "RELEASE RESULT COUNTS: "
        f"candidate records={len(candidate_items)} "
        f"(pass={candidate_counts['pass']} fail={candidate_counts['fail']} "
        f"unknown={candidate_counts['unknown']}; synthetic={candidate_synthetic}); "
        f"baseline records={len(baseline_items)} "
        f"(pass={baseline_counts['pass']} fail={baseline_counts['fail']} "
        f"unknown={baseline_counts['unknown']}; synthetic={baseline_synthetic})"
    )
    for side, statistics in holdout_statistics.items():
        counts = statistics["counts"]
        print(f"{side} records={statistics['records']} (pass={counts['pass']} fail={counts['fail']} "
              f"unknown={counts['unknown']}; synthetic={statistics['synthetic']})")
    print(f"PROVENANCE DECLARATIONS: synthetic evidence references={len(synthetic_references)}; "
          f"manifest synthetic evidence references={len(manifest_synthetic_references)} "
          "(unique side/path/hash identities; any synthetic material is excluded from actual model acceptance)")
    print(
        f"holdout scenarios={sum(category_counts.values())} categories="
        + ",".join(f"{category}:{category_counts.get(category, 0)}" for category in HOLDOUT_CATEGORIES)
    )
    print(f"PAIRED COVERAGE: AT comparable pairs={len(valid_pair_keys)}; "
          f"holdout comparable unexposed pairs={sum(category_counts.values())} "
          "(assertion outcomes remain separate)")
    print(
        "COMPARISON: paired runs=" + str(len(paired_loading))
        + "; median loading baseline="
        + str(median([pair[0] for pair in paired_loading]))
        + " bytes candidate="
        + str(median([pair[1] for pair in paired_loading]))
        + " bytes (exploratory loading metric; cannot offset quality failures; "
        "unknown cost or tokens are not converted)"
    )
    if synthetic_references and not fixture_mode:
        insufficient.append("synthetic evidence cannot establish release acceptance; "
                            "use --allow-synthetic-fixtures only for mechanism tests")
    for error in detected:
        print(f"FAIL: {error}")
    for error in insufficient:
        print(f"INSUFFICIENT: {error}")
    print(
        "BOUNDARY: this checker verifies material shape, scope, hashes, target-source bindings, "
        "repeats, explicit comparison values, holdout input/exposure coverage and references; "
        "it cannot authenticate capture truth, complete attempt/exposure history or a reuse "
        "dependency review. An independent reviewer must inspect these. Synthetic fixtures "
        "are mechanism tests, never actual model or release acceptance evidence"
    )
    if detected:
        print(f"RELEASE FAILED: {len(detected)} detected failure(s)")
        return 1
    if insufficient:
        print(f"RELEASE INSUFFICIENT: {len(insufficient)} evidence gap(s)")
        return 2
    if fixture_mode:
        print("SYNTHETIC FIXTURE VERIFIED: mechanism checks passed; not release acceptance")
    else:
        print("RELEASE MATERIAL VERIFIED: structural release evidence is complete")
    return 0


def load_patch_scope(path: Path, target: str, cases: list[dict[str, Any]]):
    """Read the frozen selection; authoring material supplies every assertion ID."""
    scope = require_object(read_json(path, "patch scope"), "patch scope")
    if type(scope.get("schema_version")) is not int or scope["schema_version"] != 1:
        raise InputError("patch scope.schema_version must be the integer 1")
    if scope.get("target_candidate_source") != target:
        raise InputError("patch scope target_candidate_source must match explicit target")
    case_material = {case["id"]: {variant["id"]: variant for variant in case["variants"]}
                     for case in cases}
    selected = {}
    raw_cases = scope.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise InputError("patch scope.cases must be a non-empty array")
    for index, raw_case in enumerate(raw_cases):
        location = f"patch scope.cases[{index}]"
        item = require_object(raw_case, location)
        case_id = require_nonempty_string(required_field(item, "case_id", location), f"{location}.case_id")
        if case_id not in case_material or not CASE_ID.fullmatch(case_id):
            raise InputError(f"{location}.case_id is not present in case material")
        expected_case_hash = hashlib.sha256(canonical_json(
            next(case for case in cases if case["id"] == case_id)).encode("utf-8")).hexdigest()
        if item.get("case_sha256") != expected_case_hash:
            raise InputError(f"{location}: case material hash mismatch")
        variants = item.get("variants")
        if not isinstance(variants, list) or not variants or any(key[0] == case_id for key in selected):
            raise InputError(f"{location}.variants must be non-empty and case IDs unique")
        for variant_index, raw_variant in enumerate(variants):
            variant_location = f"{location}.variants[{variant_index}]"
            variant = require_object(raw_variant, variant_location)
            variant_id = require_nonempty_string(required_field(variant, "variant_id", variant_location),
                                                f"{variant_location}.variant_id")
            key = (case_id, variant_id)
            if variant_id not in case_material[case_id] or key in selected:
                raise InputError(f"{variant_location}: variant is missing from case material or duplicated")
            assertion_ids = require_string_array(variant.get("assertion_ids"),
                                                 f"{variant_location}.assertion_ids", nonempty=True)
            if len(set(assertion_ids)) != len(assertion_ids):
                raise InputError(f"{variant_location}.assertion_ids contains duplicates")
            authored = case_material[case_id][variant_id]
            authored_ids = {action["assertion_id"] for field in ("expected_actions", "forbidden_actions")
                            for action in authored[field]}
            if set(assertion_ids) != authored_ids:
                raise InputError(f"{variant_location}.assertion_ids must exactly match authored assertions")
            repeats = variant.get("repeats")
            if type(repeats) is not int or repeats < 1:
                raise InputError(f"{variant_location}.repeats must be a positive integer")
            selected[key] = {"assertions": authored_ids, "repeats": repeats,
                             "input": {field: authored[field] for field in
                                       ("given", "when", "allowed_capabilities")}}

    for case_id, variants in PATCH_REQUIRED_VARIANTS.items():
        for variant_id in variants:
            required_repeats = 3 if (case_id, variant_id) == ("AT-33", "complete-package-install") else 1
            item = selected.get((case_id, variant_id))
            if item is None or item["repeats"] < required_repeats:
                raise InputError(f"patch scope missing required {case_id}/{variant_id} "
                                 f"with {required_repeats} repeat(s)")

    raw_holdouts = scope.get("holdouts")
    if not isinstance(raw_holdouts, list) or len(raw_holdouts) != 2:
        raise InputError("patch scope.holdouts must contain exactly two sealed scenarios")
    holdouts, input_ids = {}, set()
    for index, raw_holdout in enumerate(raw_holdouts):
        location = f"patch scope.holdouts[{index}]"
        holdout = require_object(raw_holdout, location)
        scenario_id = require_nonempty_string(holdout.get("scenario_id"), f"{location}.scenario_id")
        if not SAFE_ID.fullmatch(scenario_id) or scenario_id in holdouts:
            raise InputError(f"{location}.scenario_id must be unique and input-safe")
        category = holdout.get("category")
        if not isinstance(category, str) or not SAFE_ID.fullmatch(category):
            raise InputError(f"{location}.category must be a frozen input-safe ID")
        input_id = holdout.get("input_sha256")
        if not isinstance(input_id, str) or not SHA256.fullmatch(input_id):
            raise InputError(f"{location}.input_sha256 must be lowercase SHA-256")
        if input_id in input_ids:
            raise InputError(f"{location}: duplicate underlying holdout input")
        input_ids.add(input_id)
        rubric_sha256 = holdout.get("rubric_sha256")
        if not isinstance(rubric_sha256, str) or not SHA256.fullmatch(rubric_sha256):
            raise InputError(f"{location}.rubric_sha256 must be lowercase SHA-256")
        assertions = require_string_array(holdout.get("assertion_ids"),
                                          f"{location}.assertion_ids", nonempty=True)
        if (len(assertions) != len(set(assertions))
                or any(not SAFE_ID.fullmatch(assertion) for assertion in assertions)):
            raise InputError(f"{location}.assertion_ids must be unique input-safe IDs")
        holdouts[scenario_id] = {"category": category, "input_sha256": input_id,
                                 "rubric_sha256": rubric_sha256, "assertions": set(assertions)}
    if {item["category"] for item in holdouts.values()} != PATCH_REQUIRED_HOLDOUT_CATEGORIES:
        raise InputError("patch scope requires one holdout in each required category: "
                         "install_authorization and observability_identity")
    return selected, holdouts


def load_patch_manifest(path: Path, scope_path: Path, target: str, detected: list[str]):
    manifest = require_object(read_json(path, "patch manifest"), "patch manifest")
    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 2:
        raise InputError("patch manifest.schema_version must be the integer 2")
    collection_id = manifest.get("collection_id")
    if not isinstance(collection_id, str) or not SAFE_ID.fullmatch(collection_id):
        raise InputError("patch manifest.collection_id must be an input-safe ID")
    if manifest.get("target_candidate_source") != target:
        detected.append("patch manifest target_candidate_source does not match explicit target")
    scope_hash = manifest.get("patch_scope_sha256")
    if not isinstance(scope_hash, str) or not SHA256.fullmatch(scope_hash):
        raise InputError("patch manifest.patch_scope_sha256 must be lowercase SHA-256")
    if hashlib.sha256(scope_path.read_bytes()).hexdigest() != scope_hash:
        detected.append("patch scope hash mismatch")
    records = manifest.get("records")
    if not isinstance(records, list) or not records:
        raise InputError("patch manifest.records must be a non-empty array")
    entries = {}
    for index, raw in enumerate(records):
        location = f"patch manifest.records[{index}]"
        entry = require_object(raw, location)
        side, filename = entry.get("side"), entry.get("path")
        if side not in ("candidate", "holdout"):
            raise InputError(f"{location}.side must be candidate or holdout")
        suffix = ".result.json" if side == "candidate" else ".holdout.json"
        if (not isinstance(filename, str) or not filename.endswith(suffix)
                or Path(filename).name != filename or "/" in filename or "\\" in filename or ":" in filename):
            raise InputError(f"{location}.path must be a direct {suffix} filename")
        if not isinstance(entry.get("sha256"), str) or not SHA256.fullmatch(entry["sha256"]):
            raise InputError(f"{location}.sha256 must be lowercase SHA-256")
        if not isinstance(entry.get("run_id"), str) or not SAFE_ID.fullmatch(entry["run_id"]):
            raise InputError(f"{location}.run_id must identify the original run")
        root = entry.get("evidence_root")
        if (not isinstance(root, str) or not root or any(c in root for c in ("\\", ":", "\x00"))
                or any(part in ("", ".", "..") for part in root.split("/"))):
            raise InputError(f"{location}.evidence_root must be a canonical relative directory")
        key = (side, filename)
        if key in entries:
            detected.append(f"patch manifest duplicate binding for {side} {filename}")
        entries[key] = entry
    if not isinstance(manifest.get("holdout_exposures"), list):
        raise InputError("patch manifest.holdout_exposures must explicitly list exposed inputs (or [])")
    return manifest, entries


def check_patch_authored_file(raw: Any, directory: Path, identity: str, kind: str,
                              detected: list[str], insufficient: list[str],
                              expected_hash: str | None = None) -> Path | None:
    """Bind a coordinator-authored file without pretending it is native capture."""
    if not isinstance(raw, dict):
        insufficient.append(f"{identity}: authored {kind} file reference is required")
        return None
    if raw.get("kind") != kind or "provenance" in raw:
        insufficient.append(f"{identity}: authored file kind must be {kind} without capture provenance")
        return None
    name, digest = raw.get("path"), raw.get("sha256")
    if (not isinstance(name, str) or not name or Path(name).name != name
            or "/" in name or "\\" in name or ":" in name):
        insufficient.append(f"{identity}: authored file path must be a direct filename in its root")
        return None
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        insufficient.append(f"{identity}: authored file sha256 must be lowercase SHA-256")
        return None
    if expected_hash is not None and digest != expected_hash:
        detected.append(f"{identity}: {kind} hash differs from frozen patch scope")
    try:
        root = directory.resolve()
        if (directory / name).is_symlink():
            insufficient.append(f"{identity}: authored file cannot be a symlink")
            return None
        path = (directory / name).resolve()
        path.relative_to(root)
        if not path.is_file() or path.name.lower().endswith((".result.json", ".holdout.json")):
            insufficient.append(f"{identity}: authored file is missing or is a declaration")
            return None
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, ValueError, RuntimeError) as error:
        insufficient.append(f"{identity}: authored file cannot be inspected: {error}")
        return None
    if actual != digest:
        detected.append(f"{identity}: {kind} file hash mismatch")
        return None
    return path


def patch_has_evaluator_key(value: Any) -> bool:
    if isinstance(value, dict):
        return bool(PATCH_FORBIDDEN_INPUT_KEYS & set(value)) or any(
            patch_has_evaluator_key(item) for item in value.values())
    if isinstance(value, list):
        return any(patch_has_evaluator_key(item) for item in value)
    return False


def patch_holdout_input_identity(value: Any, location: str, scenario_id: str, category: str,
                                 detected: list[str], insufficient: list[str]) -> str | None:
    if not isinstance(value, dict):
        insufficient.append(f"{location}: holdout input must be a JSON object")
        return None
    if set(value) != PATCH_HOLDOUT_PACKET_FIELDS or patch_has_evaluator_key(value):
        detected.append(f"{location}: holdout input requires exact field set without evaluator-only keys")
        return None
    if value["scenario_id"] != scenario_id or value["category"] != category:
        detected.append(f"{location}: scenario/category differs from frozen holdout")
    if not isinstance(value["task"], str) or not value["task"].strip():
        insufficient.append(f"{location}: task must be non-empty text")
    if not isinstance(value["initial_state"], dict):
        insufficient.append(f"{location}: initial_state must be an object")
    capabilities = value["allowed_capabilities"]
    if (not isinstance(capabilities, list) or any(not isinstance(item, str) or not item.strip()
                                                 for item in capabilities)):
        insufficient.append(f"{location}: allowed_capabilities must be an array of strings")
    payload = {key: item for key, item in value.items() if key != "scenario_id"}
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def patch_input_identity(path: Path, location: str, scenario_id: str, category: str,
                         detected: list[str], insufficient: list[str]) -> str | None:
    value = read_json(path, location)
    if not isinstance(value, dict):
        insufficient.append(f"{location}: sealed input must be a JSON object")
        return None
    return patch_holdout_input_identity(value, location, scenario_id, category, detected, insufficient)


def check_patch_scope_seal(raw: Any, directory: Path, scope_hash: str, target: str,
                           detected: list[str], insufficient: list[str]) -> None:
    path = check_patch_authored_file(raw, directory, "patch manifest.scope_seal",
                                     "coordinator_seal", detected, insufficient)
    if path is None:
        return
    seal = require_object(read_json(path, "patch scope seal"), "patch scope seal")
    if type(seal.get("schema_version")) is not int or seal["schema_version"] != 1:
        insufficient.append("patch scope seal.schema_version must be the integer 1")
    if seal.get("patch_scope_sha256") != scope_hash:
        detected.append("patch scope seal does not bind exact frozen scope hash")
    if seal.get("target_candidate_source") != target:
        detected.append("patch scope seal target source differs from candidate")
    if not isinstance(seal.get("sealed_at"), str) or not seal["sealed_at"].strip():
        insufficient.append("patch scope seal requires a pre-dispatch sealed_at declaration")


def patch_capture_json(raw: Any, location: str, directory: Path,
                       detected: list[str], insufficient: list[str]) -> dict[str, Any] | None:
    """Read a hashed native capture only after its reference is valid."""
    if not check_capture_list([raw], location, directory, detected, insufficient):
        return None
    if raw.get("provenance") != "host_capture":
        insufficient.append(f"{location}: native host_capture is required")
        return None
    value = read_json(directory / raw["path"], location)
    if not isinstance(value, dict):
        insufficient.append(f"{location}: native capture must be a JSON object")
        return None
    return value


def check_candidate_dispatch(entry: dict[str, Any] | None, record: dict[str, Any],
                             expected: dict[str, Any] | None, evidence_root: Path, identity: str,
                             detected: list[str], insufficient: list[str]) -> tuple[str | None, str | None, str | None]:
    """Bind dispatched task and native receipt to the actual result identity."""
    if entry is None:
        return None, None, None
    input_ref, receipt_ref = entry.get("dispatch_input"), entry.get("dispatch_receipt")
    dispatched = patch_capture_json(input_ref, f"{identity}.dispatch_input", evidence_root,
                                    detected, insufficient)
    receipt = patch_capture_json(receipt_ref, f"{identity}.dispatch_receipt", evidence_root,
                                 detected, insufficient)
    if dispatched is not None:
        if set(dispatched) != PATCH_CANDIDATE_DISPATCH_FIELDS:
            detected.append(f"{identity}: dispatch input requires exact field set without evaluator-only keys")
        expected_identity = {field: record[field] for field in ("case_id", "variant_id", "run_id")}
        if any(dispatched.get(field) != value for field, value in expected_identity.items()):
            detected.append(f"{identity}: dispatch input case/variant/run does not match result")
        if expected is not None and any(canonical_json(dispatched.get(field)) != canonical_json(value)
                                        for field, value in expected["input"].items()):
            detected.append(f"{identity}: dispatch input differs from frozen case variant packet")
    if receipt is not None:
        expected_receipt = {field: record[field] for field in ("case_id", "variant_id", "run_id")}
        expected_receipt["actor_id"] = record["actor"]["id"]
        if any(receipt.get(field) != value for field, value in expected_receipt.items()):
            detected.append(f"{identity}: dispatch receipt case/variant/run/actor does not match result")
        if (dispatched is None or receipt.get("dispatch_sha256") != input_ref["sha256"]
                or receipt.get("received") is not True):
            detected.append(f"{identity}: dispatch receipt does not prove the bound input was received")
        native_id = receipt.get("native_invocation_id")
        if not isinstance(native_id, str) or not SAFE_ID.fullmatch(native_id):
            insufficient.append(f"{identity}: dispatch receipt needs a native invocation ID")
            native_id = None
    else:
        native_id = None
    return native_id, input_ref.get("sha256") if dispatched else None, receipt_ref.get("sha256") if receipt else None


def check_patch_rubric(path: Path | None, scenario_id: str, spec: dict[str, Any] | None,
                       detected: list[str], insufficient: list[str]) -> None:
    if path is None or spec is None:
        return
    rubric = require_object(read_json(path, f"{scenario_id} rubric"), f"{scenario_id} rubric")
    if rubric.get("scenario_id") != scenario_id or rubric.get("category") != spec["category"]:
        detected.append(f"{scenario_id}: rubric scenario/category differs from frozen scope")
    assertions = rubric.get("assertions")
    if not isinstance(assertions, list) or not assertions:
        insufficient.append(f"{scenario_id}: rubric assertions must be non-empty")
        return
    ids = []
    for index, raw in enumerate(assertions):
        if not isinstance(raw, dict):
            insufficient.append(f"{scenario_id}: rubric assertions[{index}] must be an object")
            continue
        assertion_id = raw.get("id")
        if not isinstance(assertion_id, str) or not SAFE_ID.fullmatch(assertion_id):
            insufficient.append(f"{scenario_id}: rubric assertion ID is invalid")
        else:
            ids.append(assertion_id)
        if not isinstance(raw.get("criterion"), str) or not raw["criterion"].strip():
            insufficient.append(f"{scenario_id}: rubric criterion must be non-empty")
    if len(ids) != len(assertions) or len(ids) != len(set(ids)) or set(ids) != spec["assertions"]:
        detected.append(f"{scenario_id}: rubric assertion IDs differ from frozen scope")


def verify_patch_command(arguments: argparse.Namespace) -> int:
    if arguments.ids or arguments.baseline or arguments.baseline_holdout:
        raise InputError("patch profile uses frozen scope and candidate-only evidence; --ids/baseline are not accepted")
    if arguments.allow_synthetic_fixtures:
        raise InputError("synthetic fixtures cannot establish patch acceptance")
    for field in ("holdout", "target_candidate_source", "patch_scope", "release_manifest"):
        if not getattr(arguments, field, None):
            raise InputError(f"patch profile requires --{field.replace('_', '-')}")
    target = arguments.target_candidate_source
    if not SOURCE_HASH.fullmatch(target):
        raise InputError("patch target candidate source must be a Git SHA or SHA-256")
    cases, material_errors = load_cases(Path(arguments.cases))
    if material_errors:
        print_material_errors(material_errors)
        return 1
    scope_path = Path(arguments.patch_scope)
    selected, expected_holdouts = load_patch_scope(scope_path, target, cases)
    print(f"SCOPE: patch {len(selected)} selected variant(s), {len(expected_holdouts)} sealed holdout(s)")
    results_directory, holdout_directory = Path(arguments.results), Path(arguments.holdout)
    candidate_items = load_results(results_directory)
    holdout_items = load_holdout(holdout_directory,
                                 categories={item["category"] for item in expected_holdouts.values()})
    detected, insufficient = [], []
    manifest_path = Path(arguments.release_manifest)
    manifest, entries = load_patch_manifest(manifest_path, scope_path, target, detected)
    directories = {"candidate": results_directory, "holdout": holdout_directory}
    evidence_roots = collection_evidence_directories(entries, directories, detected)
    ledger = manifest.get("attempt_ledger")
    check_patch_authored_file(ledger, manifest_path.parent, "patch manifest.attempt_ledger",
                              "coordinator_index", detected, insufficient)
    check_patch_scope_seal(manifest.get("scope_seal"), manifest_path.parent,
                           manifest["patch_scope_sha256"], target, detected, insufficient)
    if synthetic_reference_keys(manifest):
        insufficient.append("synthetic evidence cannot establish patch acceptance")

    seen_keys, seen_holdouts, seen_inputs, used_entries = set(), set(), set(), set()
    actors, judges = set(), set()
    repeat_runs = {}
    counts = {"pass": 0, "fail": 0, "unknown": 0}
    for filename, record in candidate_items:
        key = (record["case_id"], record["variant_id"], record["repeat_index"])
        variant_key = key[:2]
        identity = f"candidate {filename} ({key[0]}/{key[1]} repeat {key[2]})"
        if key in seen_keys:
            detected.append(f"{identity}: duplicate case/variant/repeat result")
        seen_keys.add(key)
        actors.add(record["actor"]["id"])
        judges.add(record["judge"]["id"])
        if variant_key not in selected or key[2] > selected[variant_key]["repeats"]:
            detected.append(f"{identity}: extra or relabelled result outside frozen patch scope")
        binding_key = ("candidate", filename)
        used_entries.add(binding_key)
        entry = entries.get(binding_key)
        evidence_root = evidence_roots.get(binding_key, results_directory)
        if record["subject_source"]["hash"] != target or (entry is not None and "reuse" in entry):
            detected.append(f"{identity}: patch requires exact current source; reuse is not accepted")
        _, source_valid = check_release_binding(entry, record, filename, "candidate", results_directory,
                                                target, detected, insufficient, evidence_root)
        if not source_valid:
            insufficient.append(f"{identity}: target source is not established")
        if record["judge"]["id"] == record["actor"]["id"]:
            insufficient.append(f"{identity}: judge identity must differ from actor identity")
        if release_metadata(record) is None:
            insufficient.append(f"{identity}: actual model, host and parameters must be known")
        if "loading" not in record:
            insufficient.append(f"{identity}: loading data is required")
        else:
            validate_loading(record["loading"], f"{identity}.loading")
        expected = selected.get(variant_key, {}).get("assertions", set())
        native_id, dispatch_digest, receipt_digest = check_candidate_dispatch(
            entry, record, selected.get(variant_key), evidence_root, identity, detected, insufficient)
        trace = record.get("trace")
        repeat_runs.setdefault(variant_key, []).append({
            "run_id": record["run_id"], "evidence_root": entry.get("evidence_root") if entry else None,
            "actor_id": record["actor"]["id"], "native_id": native_id,
            "trace_digest": trace.get("sha256") if isinstance(trace, dict) else None,
            "dispatch_digest": dispatch_digest, "receipt_digest": receipt_digest,
        })
        synthetic = walk_result_assertions(record, identity, expected, evidence_root, detected,
                                           insufficient, strict_statuses=True, status_counts=counts)
        if synthetic or synthetic_reference_keys(entry or {}):
            insufficient.append(f"{identity}: synthetic evidence cannot establish patch acceptance")
    for (case_id, variant_id), spec in selected.items():
        for repeat in range(1, spec["repeats"] + 1):
            if (case_id, variant_id, repeat) not in seen_keys:
                insufficient.append(f"missing candidate result for {case_id}/{variant_id} repeat {repeat}")
        runs = repeat_runs.get((case_id, variant_id), [])
        if len(runs) != len({item["run_id"] for item in runs}) or len(runs) != len({item["evidence_root"] for item in runs}):
            detected.append(f"{case_id}/{variant_id}: independent repeats require distinct run_id and evidence_root")
        if (case_id, variant_id) == ("AT-33", "complete-package-install"):
            for field, label in (("actor_id", "independent native actor"),
                                 ("native_id", "native invocation"),
                                 ("trace_digest", "distinct raw trace"),
                                 ("dispatch_digest", "distinct dispatch input"),
                                 ("receipt_digest", "distinct dispatch receipt")):
                values = [item[field] for item in runs]
                if len(values) != len(set(values)):
                    detected.append(f"{case_id}/{variant_id}: repeats require {label} identity")

    exposures = set()
    for index, raw in enumerate(manifest["holdout_exposures"]):
        location = f"patch manifest.holdout_exposures[{index}]"
        exposure = require_object(raw, location)
        input_id = exposure.get("input_sha256")
        if not isinstance(input_id, str) or not SHA256.fullmatch(input_id):
            insufficient.append(f"{location}.input_sha256: lowercase SHA-256 is required")
            input_id = None
        check_capture_list(exposure.get("evidence"), f"{location}.evidence",
                           holdout_directory, detected, insufficient)
        if input_id:
            exposures.add(input_id)
    for filename, record in holdout_items:
        scenario_id = record["scenario_id"]
        identity = f"holdout {filename} ({scenario_id})"
        if scenario_id in seen_holdouts:
            detected.append(f"{identity}: duplicate scenario_id")
        seen_holdouts.add(scenario_id)
        actors.add(record["actor"]["id"])
        judges.add(record["judge"]["id"])
        spec = expected_holdouts.get(scenario_id)
        if spec is None:
            detected.append(f"{identity}: extra or relabelled holdout outside frozen patch scope")
        elif record["category"] != spec["category"]:
            detected.append(f"{identity}: category differs from frozen patch scope")
        binding_key = ("holdout", filename)
        used_entries.add(binding_key)
        entry = entries.get(binding_key)
        evidence_root = evidence_roots.get(binding_key, holdout_directory)
        if record["subject_source"]["hash"] != target or (entry is not None and "reuse" in entry):
            detected.append(f"{identity}: patch requires exact current source; reuse is not accepted")
        _, source_valid = check_release_binding(entry, record, filename, "holdout", holdout_directory,
                                                target, detected, insufficient, evidence_root)
        if not source_valid:
            insufficient.append(f"{identity}: target source is not established")
        holdout = entry.get("holdout") if entry else None
        if not isinstance(holdout, dict):
            insufficient.append(f"{identity}: sealed input and exposure evidence are required")
        else:
            sealed = check_patch_authored_file(holdout.get("input"), evidence_root,
                f"{identity}.input", "controller_sealed_input", detected, insufficient)
            input_id = (patch_input_identity(sealed, f"{identity}.input", scenario_id,
                record["category"], detected, insufficient) if sealed else None)
            dispatched = patch_capture_json(holdout.get("dispatch_input"),
                f"{identity}.dispatch_input", evidence_root, detected, insufficient)
            dispatched_id = (patch_holdout_input_identity(dispatched, f"{identity}.dispatch_input",
                scenario_id, record["category"], detected, insufficient) if dispatched is not None else None)
            if input_id is not None and dispatched_id != input_id:
                detected.append(f"{identity}: dispatched input differs from sealed input")
            receipts = holdout.get("dispatch_receipt")
            if not isinstance(receipts, list) or len(receipts) != 1:
                insufficient.append(f"{identity}.dispatch_receipt: exactly one native receipt capture is required")
                receipt = None
            else:
                receipt = patch_capture_json(receipts[0], f"{identity}.dispatch_receipt",
                                             evidence_root, detected, insufficient)
            if receipt is not None:
                if set(receipt) != PATCH_HOLDOUT_RECEIPT_FIELDS:
                    detected.append(f"{identity}: dispatch receipt requires exact field set")
                expected_receipt = {"scenario_id": scenario_id, "category": record["category"],
                                    "run_id": record["run_id"], "actor_id": record["actor"]["id"]}
                if any(receipt.get(field) != value for field, value in expected_receipt.items()):
                    detected.append(f"{identity}: dispatch receipt scenario/category/run/actor does not match result")
                dispatch_ref = holdout.get("dispatch_input")
                if (dispatched is None or not isinstance(dispatch_ref, dict)
                        or receipt.get("dispatch_sha256") != dispatch_ref.get("sha256")
                        or receipt.get("received") is not True):
                    detected.append(f"{identity}: dispatch receipt does not prove the bound input was received")
                native_id = receipt.get("native_invocation_id")
                if not isinstance(native_id, str) or not SAFE_ID.fullmatch(native_id):
                    insufficient.append(f"{identity}: dispatch receipt needs a native invocation ID")
            if input_id in seen_inputs:
                detected.append(f"{identity}: duplicate underlying holdout input")
            if input_id:
                seen_inputs.add(input_id)
            if spec is not None and input_id != spec["input_sha256"]:
                detected.append(f"{identity}: underlying input identity differs from frozen patch scope")
            if input_id in exposures or holdout.get("exposure") != "unexposed":
                detected.append(f"{identity}: exposed input cannot be an unexposed patch holdout")
            check_capture_list(holdout.get("evidence"), f"{identity}.exposure.evidence",
                               evidence_root, detected, insufficient)
            if spec is not None:
                rubric_path = check_patch_authored_file(holdout.get("rubric"), evidence_root,
                    f"{identity}.rubric", "controller_frozen_rubric", detected, insufficient,
                    expected_hash=spec["rubric_sha256"])
                check_patch_rubric(rubric_path, scenario_id, spec, detected, insufficient)
        if record["judge"]["id"] == record["actor"]["id"]:
            insufficient.append(f"{identity}: judge identity must differ from actor identity")
        if release_metadata(record) is None:
            insufficient.append(f"{identity}: actual model, host and parameters must be known")
        synthetic = walk_result_assertions(record, identity,
                                           spec["assertions"] if spec else set(), evidence_root,
                                           detected, insufficient, strict_statuses=True, status_counts=counts)
        if synthetic or synthetic_reference_keys(entry or {}):
            insufficient.append(f"{identity}: synthetic evidence cannot establish patch acceptance")
    for scenario_id in sorted(set(expected_holdouts) - seen_holdouts):
        insufficient.append(f"missing patch holdout {scenario_id}")
    for side, filename in sorted(set(entries) - used_entries):
        insufficient.append(f"patch manifest binding has no submitted record: {side} {filename}")
    if actors & judges:
        insufficient.append("patch collection reviewer independence: judge ID also appears as an actor ID")
    print(f"PATCH RESULT COUNTS: candidate={len(candidate_items)} holdout={len(holdout_items)} "
          f"pass={counts['pass']} fail={counts['fail']} unknown={counts['unknown']}")
    for issue in detected:
        print(f"FAIL: {issue}")
    for issue in insufficient:
        print(f"INSUFFICIENT: {issue}")
    print("BOUNDARY: patch exit 0 verifies frozen-scope structural evidence only; it cannot authenticate "
          "capture truth, seal timing, native invocation authenticity, complete attempt or exposure history, "
          "reviewer independence, or semantic judgments. "
          "An independent reviewer must inspect the attempt ledger and raw evidence. It does not establish "
          "the full paired release profile or V1.3.1 effect comparison")
    if detected:
        print(f"PATCH FAILED: {len(detected)} detected failure(s)")
        return 1
    if insufficient:
        print(f"PATCH INSUFFICIENT: {len(insufficient)} evidence gap(s)")
        return 2
    print("PATCH MATERIAL VERIFIED: 2.0.2 incremental structural evidence is complete")
    return 0


def verify_command(arguments: argparse.Namespace) -> int:
    if arguments.profile == "release":
        return verify_release_command(arguments)
    if arguments.profile == "patch":
        return verify_patch_command(arguments)
    if getattr(arguments, "allow_synthetic_fixtures", False):
        raise InputError("--allow-synthetic-fixtures is only valid with --profile release")
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
