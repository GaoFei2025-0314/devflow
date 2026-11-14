#!/usr/bin/env python3
"""Check plugin version, marketplace, and CHANGELOG consistency.

``consistency`` reports whether the working tree's version files agree.
``bump`` reports whether a change under the skill-content paths bumped the
plugin version and updated CHANGELOG relative to a base ref. The trigger
paths match the version-bump job: skills/, SKILL.md, AGENTS.md, templates/.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION_PATTERN = r"^\d+\.\d+\.\d+$"
HEADING_PATTERN = r"^## (\d+\.\d+\.\d+)(?: \((\d{4}-\d{2}-\d{2})[^)]*\))?\s*$"
VERSION_RE = re.compile(VERSION_PATTERN)
HEADING_RE = re.compile(HEADING_PATTERN)
PLUGIN_LABEL = ".claude-plugin/plugin.json"
MARKETPLACE_LABEL = ".claude-plugin/marketplace.json"
CHANGELOG_LABEL = "CHANGELOG.md"
# Same pathspec as .github/workflows/validate.yml version-bump, in that order.
TRIGGER_PATHS = ("skills/", "SKILL.md", "AGENTS.md", "templates/")


class InputError(Exception):
    """The checker could not interpret its input."""


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    consistency = subparsers.add_parser(
        "consistency",
        help="check that version files in one tree agree",
    )
    consistency.add_argument("--root", default=".", help="bundle root to check")
    consistency.add_argument(
        "--tag",
        help="release tag; must equal v plus the plugin.json version",
    )

    bump = subparsers.add_parser(
        "bump",
        help="check a version bump against a base ref",
    )
    bump.add_argument(
        "--base-ref",
        required=True,
        help="git ref of the baseline (for example origin/main)",
    )
    bump.add_argument("--root", default=".", help="bundle root to check")
    return parser.parse_args(argv)


def read_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeError as error:
        raise InputError(f"{label} is not valid UTF-8: {error}") from error
    except OSError as error:
        raise InputError(f"cannot read {label}: {error}") from error


def parse_json(text: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise InputError(
            f"invalid JSON in {label} at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error
    if not isinstance(value, dict):
        raise InputError(f"{label} must be a JSON object")
    return value


def require_version(document: dict[str, Any], label: str) -> str:
    if "version" not in document:
        raise InputError(
            f"{label} version is required and must match {VERSION_PATTERN}"
        )
    version = document["version"]
    if not isinstance(version, str):
        raise InputError(
            f"{label} version must be a string matching {VERSION_PATTERN}"
        )
    return version


def parse_version(value: str) -> tuple[int, int, int]:
    major, minor, patch = value.split(".")
    return int(major), int(minor), int(patch)


def valid_calendar_date(value: str) -> bool:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return False
    return parsed.strftime("%Y-%m-%d") == value


def check_version_pattern(version: str, errors: list[str]) -> None:
    if VERSION_RE.fullmatch(version) is None:
        errors.append(
            f"{PLUGIN_LABEL} version {version!r} does not match {VERSION_PATTERN}"
        )


def check_marketplace(document: dict[str, Any], version: str, errors: list[str]) -> None:
    plugins = document.get("plugins", [])
    if not isinstance(plugins, list):
        raise InputError(f"{MARKETPLACE_LABEL} plugins must be an array")
    for index, plugin in enumerate(plugins):
        location = f"{MARKETPLACE_LABEL} plugins[{index}]"
        if not isinstance(plugin, dict):
            raise InputError(f"{location} must be an object")
        if "version" not in plugin:
            continue
        found = plugin["version"]
        if found != version:
            errors.append(
                f"{location}.version is {found!r}; expected {version!r} "
                f"to match {PLUGIN_LABEL}"
            )


def check_changelog(text: str, version: str, errors: list[str]) -> None:
    headings: list[tuple[int, str, re.Match[str] | None]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.startswith("## "):
            headings.append((line_number, line, HEADING_RE.fullmatch(line)))
    if not headings:
        errors.append(
            f"{CHANGELOG_LABEL} has no '## ' heading; expected {HEADING_PATTERN}"
        )
        return

    parsed: list[tuple[int, str]] = []
    for index, (line_number, line, match) in enumerate(headings):
        if match is None:
            errors.append(
                f"{CHANGELOG_LABEL}:{line_number}: heading {line!r} "
                f"does not match {HEADING_PATTERN}"
            )
            continue
        heading_version = match.group(1)
        date = match.group(2)
        if index == 0 and heading_version != version:
            errors.append(
                f"{CHANGELOG_LABEL}:{line_number}: top version is {heading_version}; "
                f"expected {version} to match {PLUGIN_LABEL}"
            )
        if index == 0 and date is None:
            errors.append(
                f"{CHANGELOG_LABEL}:{line_number}: top heading must include a valid "
                f"calendar date; expected {HEADING_PATTERN}"
            )
        elif date is not None and not valid_calendar_date(date):
            errors.append(
                f"{CHANGELOG_LABEL}:{line_number}: date {date} is not a valid "
                f"calendar date; expected a real YYYY-MM-DD in {HEADING_PATTERN}"
            )
        parsed.append((line_number, heading_version))

    for (previous_line, previous), (line_number, heading_version) in zip(
        parsed, parsed[1:]
    ):
        if parse_version(heading_version) >= parse_version(previous):
            errors.append(
                f"{CHANGELOG_LABEL}:{line_number}: version {heading_version} is not "
                f"strictly less than {previous} at line {previous_line}; headings "
                "must be strictly decreasing with no duplicates"
            )


def check_tag(tag: str | None, version: str, errors: list[str]) -> None:
    if tag is None:
        return
    expected = "v" + version
    if tag != expected:
        errors.append(
            f"--tag {tag!r} does not equal v + {PLUGIN_LABEL} version; "
            f"expected {expected!r}"
        )


def consistency_command(arguments: argparse.Namespace) -> int:
    root = Path(arguments.root)
    if not root.is_dir():
        raise InputError(f"bundle root is not a directory: {root}")

    plugin = parse_json(read_text(root / PLUGIN_LABEL, PLUGIN_LABEL), PLUGIN_LABEL)
    version = require_version(plugin, PLUGIN_LABEL)
    marketplace = parse_json(
        read_text(root / MARKETPLACE_LABEL, MARKETPLACE_LABEL),
        MARKETPLACE_LABEL,
    )
    changelog = read_text(root / CHANGELOG_LABEL, CHANGELOG_LABEL)

    errors: list[str] = []
    check_version_pattern(version, errors)
    check_marketplace(marketplace, version, errors)
    check_changelog(changelog, version, errors)
    check_tag(arguments.tag, version, errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"VERSION CHECK FAILED: {len(errors)} error(s)")
        return 1

    print(f"VERSION CHECK PASSED: {version}")
    return 0


def run_git(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", "--no-pager", *arguments],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError as error:
        raise InputError("git is required for bump checks but was not found") from error


def require_commit(root: Path, revision: str, label: str) -> None:
    result = run_git(root, "rev-parse", "--verify", "--quiet", f"{revision}^{{commit}}")
    if result.returncode != 0:
        detail = result.stderr.strip()
        suffix = f": {detail}" if detail else ""
        raise InputError(f"cannot resolve {label} to a commit{suffix}")


def diff_quiet(root: Path, base_ref: str, *paths: str) -> bool:
    """Return True when the three-dot diff against base_ref has changes."""
    result = run_git(
        root,
        "diff",
        "--quiet",
        f"{base_ref}...HEAD",
        "--",
        *paths,
    )
    if result.returncode == 0:
        return False
    if result.returncode == 1:
        return True
    detail = result.stderr.strip() or f"exit {result.returncode}"
    raise InputError(f"git diff failed: {detail}")


def changed_trigger_paths(root: Path, base_ref: str) -> list[str]:
    result = run_git(
        root,
        "diff",
        "--name-only",
        f"{base_ref}...HEAD",
        "--",
        *TRIGGER_PATHS,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or f"exit {result.returncode}"
        raise InputError(f"git diff --name-only failed: {detail}")
    return [line for line in result.stdout.splitlines() if line.strip()]


def version_at_ref(root: Path, base_ref: str) -> str:
    spec = f"{base_ref}:{PLUGIN_LABEL}"
    result = run_git(root, "show", spec)
    if result.returncode != 0:
        detail = result.stderr.strip() or f"exit {result.returncode}"
        raise InputError(f"cannot read {spec}: {detail}")
    return require_version(parse_json(result.stdout, spec), spec)


def contains_version_heading(text: str, version: str) -> bool:
    if VERSION_RE.fullmatch(version) is None:
        return False
    for line in text.splitlines():
        match = HEADING_RE.fullmatch(line)
        if match is not None and match.group(1) == version:
            return True
    return False


def compare_versions(old: str, new: str, errors: list[str]) -> None:
    old_ok = VERSION_RE.fullmatch(old) is not None
    new_ok = VERSION_RE.fullmatch(new) is not None
    if not old_ok:
        errors.append(
            f"baseline {PLUGIN_LABEL} version {old!r} does not match {VERSION_PATTERN}"
        )
    if not new_ok:
        errors.append(
            f"{PLUGIN_LABEL} version {new!r} does not match {VERSION_PATTERN}"
        )
    if not old_ok or not new_ok:
        return
    if parse_version(new) > parse_version(old):
        return
    if new == old:
        errors.append(
            "Skill content changed but plugin version is still "
            f"{old} — bump it so installed plugins receive the update. "
            f"Expected a strictly greater version matching {VERSION_PATTERN}."
        )
        return
    errors.append(
        "Skill content changed but plugin version "
        f"{new} is not strictly greater than baseline {old}. "
        f"Expected a strictly greater version matching {VERSION_PATTERN}."
    )


def bump_command(arguments: argparse.Namespace) -> int:
    root = Path(arguments.root)
    if not root.is_dir():
        raise InputError(f"bundle root is not a directory: {root}")

    base_ref = arguments.base_ref
    require_commit(root, "HEAD", "HEAD")
    require_commit(root, base_ref, f"--base-ref {base_ref!r}")
    if not diff_quiet(root, base_ref, *TRIGGER_PATHS):
        print("No skill content changes — version bump not required.")
        return 0

    print("Skill content changed:")
    for relative in changed_trigger_paths(root, base_ref):
        print(f"  {relative}")

    old = version_at_ref(root, base_ref)
    new = require_version(
        parse_json(read_text(root / PLUGIN_LABEL, PLUGIN_LABEL), PLUGIN_LABEL),
        PLUGIN_LABEL,
    )
    changelog = read_text(root / CHANGELOG_LABEL, CHANGELOG_LABEL)
    errors: list[str] = []
    compare_versions(old, new, errors)
    if not diff_quiet(root, base_ref, CHANGELOG_LABEL):
        errors.append(
            f"{CHANGELOG_LABEL} has no changes relative to {base_ref}; expected a "
            f"change that includes a heading for version {new} matching {HEADING_PATTERN}"
        )
    elif not contains_version_heading(changelog, new):
        errors.append(
            f"{CHANGELOG_LABEL} does not include a heading for version {new}; "
            f"expected a heading matching {HEADING_PATTERN}"
        )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"VERSION BUMP CHECK FAILED: {len(errors)} error(s)")
        return 1

    print(f"Skill content changed and version bumped ({old} -> {new}) — OK.")
    print(f"CHANGELOG includes a heading for {new} — OK.")
    return 0


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    try:
        if arguments.command == "consistency":
            return consistency_command(arguments)
        if arguments.command == "bump":
            return bump_command(arguments)
        raise InputError(f"unknown command {arguments.command!r}")
    except InputError as error:
        print(f"INPUT ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
