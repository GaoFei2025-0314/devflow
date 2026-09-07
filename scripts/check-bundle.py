#!/usr/bin/env python3
"""Validate the declared structure of the Devflow skill bundle."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


CATALOG_PATH = Path("skills/devflow/references/skill-catalog.json")
CATALOG_FIELDS = {"schema_version", "skills"}
SKILL_FIELD_ORDER = ("id", "entry", "route_tags", "required_resources", "aliases")
SKILL_FIELDS = set(SKILL_FIELD_ORDER)
FRONTMATTER_NAME = re.compile(r"^name:\s*[\"']?([^\"'\r\n]+?)[\"']?\s*$")


class InputError(Exception):
    """The checker could not interpret its input."""


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="bundle root to validate")
    return parser.parse_args()


def load_catalog(root: Path) -> dict[str, Any]:
    catalog_path = root / CATALOG_PATH
    try:
        text = catalog_path.read_text(encoding="utf-8")
    except UnicodeError as error:
        raise InputError(
            f"catalog is not valid UTF-8: {CATALOG_PATH.as_posix()}: {error}"
        ) from error
    except OSError as error:
        raise InputError(f"cannot read {CATALOG_PATH.as_posix()}: {error}") from error

    try:
        catalog = json.loads(text)
    except json.JSONDecodeError as error:
        raise InputError(
            f"invalid JSON in {CATALOG_PATH.as_posix()} at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error

    if not isinstance(catalog, dict):
        raise InputError("catalog must be a JSON object")
    extra_catalog_fields = sorted(set(catalog) - CATALOG_FIELDS)
    if extra_catalog_fields:
        raise InputError(f"catalog has undeclared field '{extra_catalog_fields[0]}'")
    if type(catalog.get("schema_version")) is not int or catalog["schema_version"] != 1:
        raise InputError("schema_version must be the integer 1")
    if not isinstance(catalog.get("skills"), list):
        raise InputError("skills must be an array")

    for index, skill in enumerate(catalog["skills"]):
        location = f"skills[{index}]"
        if not isinstance(skill, dict):
            raise InputError(f"{location} must be an object")
        extra_skill_fields = sorted(set(skill) - SKILL_FIELDS)
        if extra_skill_fields:
            raise InputError(
                f"{location} has undeclared field '{extra_skill_fields[0]}'"
            )
        for field in SKILL_FIELD_ORDER:
            if field not in skill:
                raise InputError(f"{location}.{field} is required")
        for field in ("id", "entry"):
            if not isinstance(skill[field], str) or not skill[field].strip():
                raise InputError(f"{location}.{field} must be a non-empty string")
        for field in ("route_tags", "required_resources", "aliases"):
            value = skill[field]
            if not isinstance(value, list) or any(
                not isinstance(item, str) or not item.strip() for item in value
            ):
                raise InputError(f"{location}.{field} must be an array of strings")

    return catalog


def resolve_declared_path(root: Path, value: str, identity: str, errors: list[str]) -> Path | None:
    try:
        declared = Path(value)
        if declared.is_absolute():
            errors.append(f"{identity}: path must be relative to bundle root: {value}")
            return None
        root_resolved = root.resolve()
        resolved = (root / declared).resolve()
    except (ValueError, OSError, RuntimeError) as error:
        errors.append(f"{identity}: invalid declared path {value!r}: {error}")
        return None
    try:
        resolved.relative_to(root_resolved)
    except ValueError:
        errors.append(f"{identity}: path escapes bundle root: {value}")
        return None
    return resolved


def read_frontmatter_name(entry: Path, display_path: str, errors: list[str]) -> str | None:
    try:
        text = entry.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        errors.append(f"{display_path}: cannot read entry: {error}")
        return None
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        errors.append(f"{display_path}: missing name in opening YAML frontmatter")
        return None
    try:
        closing_index = lines.index("---", 1)
    except ValueError:
        errors.append(f"{display_path}: missing name in opening YAML frontmatter")
        return None
    match = None
    for line in lines[1:closing_index]:
        match = FRONTMATTER_NAME.match(line)
        if match:
            break
    if not match:
        errors.append(f"{display_path}: missing name in opening YAML frontmatter")
        return None
    return match.group(1).strip()


def validate(root: Path, catalog: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    skills: list[dict[str, Any]] = catalog["skills"]

    canonical_positions: dict[str, int] = {}
    canonical_ids = {skill["id"] for skill in skills}
    for index, skill in enumerate(skills):
        skill_id = skill["id"]
        if skill_id in canonical_positions:
            errors.append(
                f"skills[{index}]: duplicate canonical id '{skill_id}' "
                f"(first declared at skills[{canonical_positions[skill_id]}])"
            )
        else:
            canonical_positions[skill_id] = index

    alias_owners: dict[str, str] = {}
    for skill in skills:
        skill_id = skill["id"]
        for alias in skill["aliases"]:
            if alias in canonical_ids:
                errors.append(
                    f"alias '{alias}' for '{skill_id}' shadows canonical id '{alias}'"
                )
            previous_owner = alias_owners.get(alias)
            if previous_owner is not None:
                errors.append(
                    f"alias '{alias}' is owned by both '{previous_owner}' and '{skill_id}'"
                )
            else:
                alias_owners[alias] = skill_id

    for index, skill in enumerate(skills):
        skill_id = skill["id"]
        entry_value = skill["entry"]
        identity = f"skills[{index}] '{skill_id}'"
        canonical_entry = f"skills/{skill_id}/SKILL.md"
        if entry_value != canonical_entry or "\\" in entry_value:
            errors.append(
                f"{entry_value}: entry must be canonical path '{canonical_entry}'"
            )
        entry = resolve_declared_path(root, canonical_entry, identity, errors)
        if entry is None:
            continue
        if not entry.is_file():
            errors.append(f"{canonical_entry}: entry does not exist or is not a file")
        else:
            directory_name = entry.parent.name
            if directory_name != skill_id:
                errors.append(
                    f"{canonical_entry}: canonical id '{skill_id}' does not match directory "
                    f"'{directory_name}'"
                )
            frontmatter_name = read_frontmatter_name(entry, canonical_entry, errors)
            if frontmatter_name is not None and frontmatter_name != directory_name:
                errors.append(
                    f"{canonical_entry}: name '{frontmatter_name}' does not match directory "
                    f"'{directory_name}'"
                )

        for resource_value in skill["required_resources"]:
            resource = resolve_declared_path(root, resource_value, identity, errors)
            if resource is not None and not resource.is_file():
                errors.append(f"{resource_value}: required resource does not exist or is not a file")

    skills_directory = root / "skills"
    try:
        actual_ids = {
            path.name
            for path in skills_directory.iterdir()
            if path.is_dir() and (path / "SKILL.md").is_file()
        }
    except OSError as error:
        errors.append(f"skills: cannot enumerate skill directories: {error}")
        actual_ids = set()

    declared_ids = set(canonical_positions)
    for skill_id in sorted(actual_ids - declared_ids):
        errors.append(f"skills/{skill_id}/SKILL.md: skill directory is missing from catalog")
    for skill_id in sorted(declared_ids - actual_ids):
        errors.append(f"canonical id '{skill_id}' has no matching skill directory")

    return errors


def main() -> int:
    arguments = parse_arguments()
    root = Path(arguments.root)
    if not root.is_dir():
        print(f"INPUT ERROR: bundle root is not a directory: {root}", file=sys.stderr)
        return 2

    try:
        catalog = load_catalog(root)
    except InputError as error:
        print(f"INPUT ERROR: {error}", file=sys.stderr)
        return 2

    errors = validate(root, catalog)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"BUNDLE CHECK FAILED: {len(errors)} error(s)")
        return 1

    print(f"BUNDLE CHECK PASSED: {len(catalog['skills'])} skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
