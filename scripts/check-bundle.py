#!/usr/bin/env python3
"""Validate the declared structure and reference integrity of the Devflow skill bundle."""

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
ROUTER_ID = "devflow"
ROUTER_LINK = re.compile(r"\]\(\.\./([^)/\\]+)/SKILL\.md(?:#[^)\s]*)?\)")
ENTRY_LINE_BUDGET = 310
TEMPLATE_MIRROR = "templates/project-overrides.md"
TEMPLATE_AUTHORITATIVE = "skills/using-devflow/references/project-overrides.md"
# Authored instruction surfaces that ship with the bundle. Their cross-links are
# what routes a reader to the canonical contracts, so they are resolved here.
SCANNED_ROOT_FILES = (
    "SKILL.md", "AGENTS.md", "README.md", "README.zh-CN.md", "CHANGELOG.md",
)
# Captures the path and drops an optional #fragment, so an anchored link to a
# contract section is resolved rather than silently skipped.
MARKDOWN_LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)\s]*)?\)")
BACKTICK_PATH = re.compile(r"`([^`\s]+\.(?:md|sh|ts|txt|yaml|json|cjs|html))`")
# Generic document names and artifacts the skills instruct a reader to CREATE.
BACKTICK_PLACEHOLDERS = {
    "proposal.md", "design.md", "tasks.md", "project.md", "start-server.sh",
    "code-reviewer.md", "SKILL.md",
    "GEMINI.md", "AGENTS.md", "CLAUDE.md", "CLAUDE.local.md", "settings.json",
    "package.json", ".mcp.json", "bundlesize.config.json", "plugin.json",
    "package-lock.json", ".vscode/settings.json",
}


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


def extract_references(text: str) -> list[str]:
    """Bundle-relative file references a reader would be expected to follow."""
    references = []
    for match in MARKDOWN_LINK.findall(text):
        if match.startswith(("http://", "https://", "mailto:", "#", "/")):
            continue
        references.append(match)
    for match in BACKTICK_PATH.findall(text):
        if match in BACKTICK_PLACEHOLDERS or "{" in match or "<" in match:
            continue
        if "YYYY" in match or "/path/to/" in match:
            continue
        if match.endswith(".html") and "/" not in match:
            continue
        references.append(match)
    return references


def relative_display(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except (ValueError, OSError):
        return path.as_posix()


def scanned_documents(root: Path) -> list[Path]:
    documents: list[Path] = []
    for directory_name in ("skills", "templates"):
        directory = root / directory_name
        if directory.is_dir():
            documents.extend(sorted(directory.rglob("*.md")))
    for file_name in SCANNED_ROOT_FILES:
        path = root / file_name
        if path.is_file():
            documents.append(path)
    return documents


def validate_references(root: Path, errors: list[str]) -> int:
    """Resolve every bundle-relative reference; return how many were checked."""
    root_resolved = root.resolve()
    checked = 0
    for path in scanned_documents(root):
        display = relative_display(root, path)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append(f"{display}: cannot read document: {error}")
            continue
        for reference in extract_references(text):
            checked += 1
            try:
                target = (path.parent / reference).resolve()
            except (ValueError, OSError, RuntimeError) as error:
                errors.append(
                    f"{display}: invalid reference {reference!r}: {error}"
                )
                continue
            try:
                target.relative_to(root_resolved)
            except ValueError:
                errors.append(
                    f"{display}: reference escapes bundle root: {reference}"
                )
                continue
            if not target.exists():
                errors.append(
                    f"{display}: reference does not resolve: {reference}"
                )
    return checked


def validate(root: Path, catalog: dict[str, Any]) -> tuple[list[str], int]:
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

    expected_entries = {Path(skill_id) / "SKILL.md" for skill_id in declared_ids}
    try:
        nested_entries = [
            path
            for path in skills_directory.rglob("SKILL.md")
            if path.relative_to(skills_directory) not in expected_entries
        ]
    except OSError as error:
        errors.append(f"skills: cannot scan for nested SKILL.md files: {error}")
        nested_entries = []
    for path in sorted(nested_entries):
        display = path.relative_to(root).as_posix()
        errors.append(
            f"{display}: SKILL.md must sit directly in its skill directory"
        )

    for skill_id in sorted(declared_ids & actual_ids):
        entry = skills_directory / skill_id / "SKILL.md"
        try:
            line_count = len(entry.read_text(encoding="utf-8").splitlines())
        except (OSError, UnicodeError) as error:
            errors.append(f"skills/{skill_id}/SKILL.md: cannot count lines: {error}")
            continue
        if line_count > ENTRY_LINE_BUDGET:
            errors.append(
                f"skills/{skill_id}/SKILL.md: {line_count} lines "
                f"exceeds the {ENTRY_LINE_BUDGET}-line entry budget"
            )

    # Driven by which copies exist, never by the catalog entry this check guards:
    # dropping the mirror from required_resources must not switch the check off.
    mirror = root / TEMPLATE_MIRROR
    authoritative = root / TEMPLATE_AUTHORITATIVE
    if mirror.is_file() or authoritative.is_file():
        if not authoritative.is_file():
            errors.append(
                f"{TEMPLATE_AUTHORITATIVE}: authoritative template is missing "
                f"while {TEMPLATE_MIRROR} still ships"
            )
        elif not mirror.is_file():
            errors.append(
                f"{TEMPLATE_MIRROR}: template copy is missing; it must mirror "
                f"{TEMPLATE_AUTHORITATIVE}"
            )
        else:
            try:
                in_sync = mirror.read_bytes() == authoritative.read_bytes()
            except OSError as error:
                errors.append(
                    f"{TEMPLATE_MIRROR}: cannot compare template copies: {error}"
                )
                in_sync = True
            if not in_sync:
                errors.append(
                    f"{TEMPLATE_MIRROR}: template copy is out of sync with "
                    f"{TEMPLATE_AUTHORITATIVE}"
                )

    router_entry = root / "skills" / ROUTER_ID / "SKILL.md"
    if ROUTER_ID in declared_ids and router_entry.is_file():
        try:
            router_text = router_entry.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append(f"skills/{ROUTER_ID}/SKILL.md: cannot read router: {error}")
            router_text = ""
        linked_ids = set(ROUTER_LINK.findall(router_text))
        for skill_id in sorted(declared_ids - linked_ids - {ROUTER_ID}):
            errors.append(
                f"canonical id '{skill_id}' is not reachable from the router"
            )
        for skill_id in sorted(linked_ids - declared_ids):
            errors.append(
                f"skills/{ROUTER_ID}/SKILL.md: router links '{skill_id}' "
                f"which is not in the catalog"
            )

    reference_count = validate_references(root, errors)

    return errors, reference_count


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

    errors, reference_count = validate(root, catalog)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"BUNDLE CHECK FAILED: {len(errors)} error(s)")
        return 1

    print(
        f"BUNDLE CHECK PASSED: {len(catalog['skills'])} skills, "
        f"{reference_count} references"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
