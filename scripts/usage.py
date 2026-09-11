#!/usr/bin/env python3
"""Local minimal event recording for Devflow usage. Default OFF.

Subcommands:
  status   Show whether recording is enabled. Never creates anything.
  enable   Create/enable the store (opt-in only).
  disable  Stop recording. Existing events are kept.
  append   Validate and append canonical JSONL events to an enabled store.
  export   Copy stored events to a new output file (never overwrites).

The store is a directory the caller names explicitly. No background
process, no host-directory scanning, no network. Structural field limits
are not an intelligent privacy filter; they only enforce this schema.

Exit codes: 0 pass, 1 validation failure, 2 input or environment error.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

SCHEMA_VERSION = 1
STATE_FILE = "state.json"
EVENTS_FILE = "events.jsonl"
CATEGORIES = {
    "select",
    "request",
    "partial_return",
    "full_return",
    "reuse",
    "follow",
    "result",
    "authorization",
}
STATUSES = {"ok", "unknown", "not_applicable", "failed"}
IDENTIFIER = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")
ISO8601 = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")

REQUIRED_FIELDS = ("schema_version", "event_id", "task_id", "occurred_at", "category", "status")
OPTIONAL_FIELDS = {
    "parent_task_id": "identifier_or_null",
    "turn_id": "identifier_or_null",
    "skill_id": "identifier_or_null",
    "source": "short_string_or_null",
    "value": "number_or_null",
    "unit": "unit_or_null",
    "reason": "short_string_or_null",
    "action_category": "identifier_or_null",
    "evidence_id": "evidence_or_null",
}
FORBIDDEN_FIELDS = {
    "content", "command", "prompt", "dialogue", "message", "text",
    "api_key", "password", "secret", "token", "credential", "key",
    "raw_dialogue", "transcript",
}


class InputError(Exception):
    """The tool could not interpret its input."""


class ValidationError(Exception):
    """An event failed schema validation."""


def identifier(value: object) -> bool:
    return isinstance(value, str) and bool(IDENTIFIER.match(value))


def validate_event(event: object, line_number: int) -> dict:
    if not isinstance(event, dict):
        raise ValidationError(f"line {line_number}: event must be a JSON object")
    for field in REQUIRED_FIELDS:
        if field not in event:
            raise ValidationError(f"line {line_number}: missing required field '{field}'")
    unknown = sorted(set(event) - set(REQUIRED_FIELDS) - set(OPTIONAL_FIELDS))
    if unknown:
        raise ValidationError(f"line {line_number}: unknown field '{unknown[0]}'")
    forbidden = sorted(set(event) & FORBIDDEN_FIELDS)
    if forbidden:
        raise ValidationError(
            f"line {line_number}: field '{forbidden[0]}' is not accepted by the "
            "minimal recording schema"
        )
    if type(event["schema_version"]) is not int or event["schema_version"] != SCHEMA_VERSION:
        raise ValidationError(
            f"line {line_number}: schema_version must be the integer {SCHEMA_VERSION}"
        )
    for field in ("event_id", "task_id"):
        if not identifier(event[field]):
            raise ValidationError(
                f"line {line_number}: {field} must be an identifier string "
                "(up to 64 chars of A-Z a-z 0-9 . _ : -)"
            )
    if event["category"] not in CATEGORIES:
        raise ValidationError(
            f"line {line_number}: category must be one of {sorted(CATEGORIES)}"
        )
    if event["status"] not in STATUSES:
        raise ValidationError(
            f"line {line_number}: status must be one of {sorted(STATUSES)}"
        )
    if not isinstance(event["occurred_at"], str) or not ISO8601.match(
        event["occurred_at"]
    ):
        raise ValidationError(
            f"line {line_number}: occurred_at must be an ISO-8601 timestamp string"
        )
    for field, kind in OPTIONAL_FIELDS.items():
        value = event.get(field)
        if value is None:
            continue
        if kind == "identifier_or_null" and not identifier(value):
            raise ValidationError(
                f"line {line_number}: {field} must be an identifier string or null"
            )
        if kind == "short_string_or_null":
            if (
                not isinstance(value, str)
                or not value
                or len(value) > 256
                or any(ord(character) < 32 for character in value)
            ):
                raise ValidationError(
                    f"line {line_number}: {field} must be a printable non-empty "
                    "string of at most 256 characters or null"
                )
        if kind == "unit_or_null":
            if (
                not isinstance(value, str)
                or not value
                or len(value) > 16
                or any(ord(character) < 32 for character in value)
            ):
                raise ValidationError(
                    f"line {line_number}: {field} must be a printable unit string "
                    "of at most 16 characters or null"
                )
        if kind == "evidence_or_null":
            if (
                not isinstance(value, str)
                or not value
                or len(value) > 128
                or any(ord(character) < 32 for character in value)
            ):
                raise ValidationError(
                    f"line {line_number}: {field} must be a printable string of at "
                    "most 128 characters or null"
                )
        if kind == "number_or_null":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValidationError(
                    f"line {line_number}: {field} must be a number or null"
                )
    if event["category"] == "authorization":
        for field in ("action_category", "evidence_id"):
            if event.get(field) is None:
                raise ValidationError(
                    f"line {line_number}: authorization events require '{field}'"
                )
    return event


def read_state(store: Path) -> dict | None:
    state_path = store / STATE_FILE
    if not state_path.is_file():
        return None
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InputError(f"cannot read store state: {error}") from error
    if not isinstance(state, dict) or not isinstance(state.get("enabled"), bool):
        raise InputError("store state is malformed")
    return state


def command_status(store: Path) -> int:
    state = read_state(store)
    if state is not None and state["enabled"]:
        events_path = store / EVENTS_FILE
        count = 0
        if events_path.is_file():
            count = sum(
                1 for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()
            )
        print(f"recording: on ({count} events stored)")
        print("host application logs are managed by the host, not by this tool")
    else:
        print("recording: off (disabled by default; enable is opt-in)")
    return 0


def write_state(store: Path, enabled: bool) -> None:
    with (store / STATE_FILE).open("w", encoding="utf-8", newline="\n") as sink:
        sink.write(json.dumps({"schema_version": 1, "enabled": enabled}, indent=2) + "\n")


def command_enable(store: Path) -> int:
    if store.exists() and not store.is_dir():
        print(
            f"INPUT ERROR: store path exists and is not a directory: {store}",
            file=sys.stderr,
        )
        return 2
    store.mkdir(parents=True, exist_ok=True)
    write_state(store, True)
    print(f"recording enabled for store {store}")
    print(
        "enablement only affects this tool's explicit store; host application "
        "logs remain managed by the host"
    )
    return 0


def command_disable(store: Path) -> int:
    state = read_state(store)
    if state is None:
        print("recording: off (store was never initialized)")
        return 0
    write_state(store, False)
    print("recording disabled; existing events are kept and can still be exported")
    return 0


def command_append(store: Path, input_path: Path) -> int:
    state = read_state(store)
    if state is None or not state["enabled"]:
        print(
            "INPUT ERROR: recording is disabled; run `enable` first (recording is "
            "opt-in and off by default)",
            file=sys.stderr,
        )
        return 2
    if not input_path.is_file():
        print(f"INPUT ERROR: input file not found: {input_path}", file=sys.stderr)
        return 2
    try:
        lines = input_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        print(f"INPUT ERROR: cannot read input: {error}", file=sys.stderr)
        return 2

    events = []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as error:
            print(f"ERROR: line {number}: invalid JSON: {error.msg}")
            return 1
        try:
            events.append(validate_event(parsed, number))
        except ValidationError as error:
            print(f"ERROR: {error}")
            print("USAGE APPEND REJECTED: the whole batch is rejected; nothing stored")
            return 1

    with (store / EVENTS_FILE).open("a", encoding="utf-8", newline="\n") as sink:
        for event in events:
            sink.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(f"appended {len(events)} event(s)")
    return 0


def command_export(store: Path, output: Path) -> int:
    if output.exists():
        print(f"INPUT ERROR: output already exists: {output}", file=sys.stderr)
        return 2
    events_path = store / EVENTS_FILE
    if not store.is_dir() or not events_path.is_file():
        print(
            f"INPUT ERROR: store has no events to export: {store}", file=sys.stderr
        )
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(events_path.read_bytes())
    count = sum(
        1 for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()
    )
    print(f"exported {count} event(s) -> {output}")
    return 0


def identity_of(event: dict) -> tuple:
    return (event.get("task_id"), event.get("event_id"))


def command_report(store: Path, output: Path) -> int:
    if output.exists():
        print(f"INPUT ERROR: output already exists: {output}", file=sys.stderr)
        return 2
    events_path = store / EVENTS_FILE
    if not store.is_dir() or not events_path.is_file():
        print(
            f"INPUT ERROR: store has no events to report: {store}", file=sys.stderr
        )
        return 2
    events = []
    for number, line in enumerate(
        events_path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip():
            continue
        try:
            events.append(validate_event(json.loads(line), number))
        except (ValidationError, json.JSONDecodeError) as error:
            print(f"ERROR: stored event failed schema validation: {error}")
            print("USAGE REPORT REJECTED: fix the store before reporting")
            return 1

    total = len(events)
    unique: dict[tuple, dict] = {}
    conflicts: list[dict] = []
    exact_duplicates_collapsed = 0
    for event in events:
        identity = identity_of(event)
        previous = unique.get(identity)
        if previous is None:
            unique[identity] = event
        elif previous == event:
            exact_duplicates_collapsed += 1
        else:
            differing = sorted(
                key
                for key in set(previous) | set(event)
                if previous.get(key) != event.get(key)
            )
            conflicts.append(
                {
                    "event_id": event["event_id"],
                    "task_id": event["task_id"],
                    "differing_fields": differing,
                    "resolution": "excluded from statistics; kept in store",
                }
            )

    counted = list(unique.values())
    conflicting_identities = {
        (conflict["task_id"], conflict["event_id"]) for conflict in conflicts
    }
    counted = [
        event
        for event in counted
        if identity_of(event) not in conflicting_identities
    ]

    timestamps = sorted(event["occurred_at"] for event in counted)

    counts_by_category: dict[str, int] = {}
    counts_by_status: dict[str, int] = {}
    units_present: set[str] = set()
    events_without_value = 0
    tasks: dict[str, dict] = {}
    for event in counted:
        category = event["category"]
        status = event["status"]
        counts_by_category[category] = counts_by_category.get(category, 0) + 1
        counts_by_status[status] = counts_by_status.get(status, 0) + 1
        if event.get("unit") is not None:
            units_present.add(event["unit"])
        if event.get("value") is None:
            events_without_value += 1
        task_id = event["task_id"]
        task = tasks.setdefault(
            task_id,
            {
                "task_id": task_id,
                "parent_task_id": event.get("parent_task_id"),
                "is_subagent_task": event.get("parent_task_id") is not None,
                "events": 0,
                "categories": {},
                "statuses": {},
            },
        )
        task["events"] += 1
        task["categories"][category] = task["categories"].get(category, 0) + 1
        task["statuses"][status] = task["statuses"].get(status, 0) + 1

    applicable = not_applicable = unknown = 0
    for task in tasks.values():
        statuses = set(task["statuses"])
        if statuses == {"not_applicable"}:
            not_applicable += 1
        elif "unknown" in statuses:
            unknown += 1
        elif task["categories"].get("select", 0) > 0:
            applicable += 1
        else:
            unknown += 1

    report = {
        "kind": "devflow-usage-report",
        "schema_version": 1,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "store": str(store),
        "events_input": {
            "total": total,
            "unique": len(unique),
            "excluded_conflicting": len(conflicting_identities),
        },
        "deduplication": {
            "identity": "task_id + event_id; value-equal duplicates collapse, "
            "similar titles or close timestamps are NOT merged",
            "exact_duplicates_collapsed": exact_duplicates_collapsed,
        },
        "conflicts": conflicts,
        "events_time_range": {
            "first": timestamps[0] if timestamps else None,
            "last": timestamps[-1] if timestamps else None,
            "note": "ISO-8601 timestamps as recorded; null when no counted events",
        },
        "sources_present": sorted(
            {
                event["source"]
                for event in counted
                if event.get("source") is not None
            }
        ),
        "skills_present": sorted(
            {
                event["skill_id"]
                for event in counted
                if event.get("skill_id") is not None
            }
        ),
        "counts_by_category": dict(sorted(counts_by_category.items())),
        "counts_by_status": dict(sorted(counts_by_status.items())),
        "task_groups": [tasks[key] for key in sorted(tasks)],
        "measurement": {
            "units_present": sorted(units_present),
            "events_without_value": events_without_value,
            "note": "values are reported in their recorded units only; unknown "
            "values are not estimated or converted",
        },
        "applicability": {
            "applicable_tasks": applicable,
            "not_applicable_tasks": not_applicable,
            "unknown_applicability_tasks": unknown,
            "method": "explicit event statuses per task; a task with no explicit "
            "applicability signal is counted as unknown, never as zero",
        },
        "limits": [
            "This report counts recorded events only; absence of events is "
            "absence of evidence, not evidence of absence.",
            "Unknown cost or token figures are not converted into monetary or "
            "usage claims.",
            "Recorded wording is not converted into satisfaction or sentiment "
            "scores.",
            "Low event frequency does not generate deletion or deprecation "
            "suggestions.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as sink:
        sink.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        f"reported {len(counted)} event(s) across {len(tasks)} task(s) -> {output}"
    )
    return 0


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("status", "enable", "disable"):
        sub = commands.add_parser(name)
        sub.add_argument("--store", required=True)
    append = commands.add_parser("append")
    append.add_argument("--store", required=True)
    append.add_argument("--input", required=True)
    export = commands.add_parser("export")
    export.add_argument("--store", required=True)
    export.add_argument("--out", required=True)
    report = commands.add_parser("report")
    report.add_argument("--store", required=True)
    report.add_argument("--out", required=True)
    return parser.parse_args(argv)


def main() -> int:
    arguments = parse_arguments()
    store = Path(arguments.store)
    if not str(arguments.store).strip():
        print("INPUT ERROR: --store must name an explicit directory", file=sys.stderr)
        return 2
    try:
        if arguments.command == "status":
            return command_status(store)
        if arguments.command == "enable":
            return command_enable(store)
        if arguments.command == "disable":
            return command_disable(store)
        if arguments.command == "append":
            return command_append(store, Path(arguments.input))
        if arguments.command == "export":
            return command_export(store, Path(arguments.out))
        if arguments.command == "report":
            return command_report(store, Path(arguments.out))
    except InputError as error:
        print(f"INPUT ERROR: {error}", file=sys.stderr)
        return 2
    raise AssertionError(f"unhandled command {arguments.command}")


if __name__ == "__main__":
    sys.exit(main())
