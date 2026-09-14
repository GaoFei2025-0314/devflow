#!/usr/bin/env python3
"""Plan, stage, and verify Devflow skill-bundle installations.

Subcommands:
  plan    Read-only inventory of an install target: planned resources,
          conflicts, and unknown sources. Never writes.
  stage   Copy (or link) the bundle or a single-skill dependency closure
          into a brand-new destination directory.
  verify  Check a staged installation's entries, declared resources,
          references, and links against its own layout.

Exit codes: 0 pass, 1 check failure, 2 input or environment error.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

BUNDLE_CHECKER_PATH = Path(__file__).with_name("check-bundle.py")
DISTRIBUTION_ROOT_FILES = (
    "SKILL.md",
    "AGENTS.md",
    "README.md",
    "README.zh-CN.md",
    "CHANGELOG.md",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    "templates/project-overrides.md",
)
MANIFEST_NAME = "install-manifest.json"


def load_bundle_checker():
    spec = importlib.util.spec_from_file_location("check_bundle", BUNDLE_CHECKER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


CHECK_BUNDLE = load_bundle_checker()


class InputError(Exception):
    """The tool could not interpret its input."""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_catalog(bundle: Path) -> dict[str, Any]:
    return CHECK_BUNDLE.load_catalog(bundle)


def skill_owner(bundle: Path, relative: Path) -> str | None:
    parts = relative.parts
    if len(parts) >= 2 and parts[0] == "skills":
        return parts[1]
    return None


def extract_references(text: str) -> list[str]:
    """One definition of what counts as a reference, shared with the bundle checker."""
    return CHECK_BUNDLE.extract_references(text)


def resolve_closure(bundle: Path, catalog: dict[str, Any], requested: list[str]) -> list[str]:
    by_id = {skill["id"]: skill for skill in catalog["skills"]}
    for skill_id in requested:
        if skill_id not in by_id:
            raise InputError(f"unknown skill '{skill_id}'")
    closure: set[str] = set()
    queue = list(requested)
    while queue:
        skill_id = queue.pop()
        if skill_id in closure:
            continue
        skill = by_id.get(skill_id)
        if skill is None:
            raise InputError(
                f"reference points at unknown skill directory 'skills/{skill_id}'"
            )
        closure.add(skill_id)
        texts: list[tuple[Path, str]] = [
            (bundle / skill["entry"], "")
        ]
        for resource in skill["required_resources"]:
            texts.append((bundle / resource, ""))
        for path, _ in texts:
            if not path.is_file():
                continue
            for reference in extract_references(path.read_text(encoding="utf-8")):
                target = (path.parent / reference).resolve()
                relative = None
                try:
                    relative = target.relative_to(bundle.resolve())
                except ValueError:
                    continue
                owner = skill_owner(bundle, relative)
                if owner is not None and owner not in closure:
                    queue.append(owner)
    return sorted(closure)


def distribution_paths(bundle: Path, layout: str, skills: list[str]) -> list[str]:
    paths = []
    if layout == "full":
        for skill in skills:
            paths.append(f"skills/{skill}")
        paths.extend(
            name for name in DISTRIBUTION_ROOT_FILES if (bundle / name).is_file()
        )
    else:
        for skill_id in skills:
            paths.append(f"skills/{skill_id}")
        for name in DISTRIBUTION_ROOT_FILES:
            candidate = bundle / name
            if not candidate.is_file():
                continue
            if name.startswith("templates/"):
                paths.append(name)
    return paths


def stage(bundle: Path, layout: str, skill: str | None, destination: Path) -> int:
    if layout == "single" and not skill:
        print("INPUT ERROR: --skill is required for the single layout", file=sys.stderr)
        return 2
    if layout != "single" and skill:
        print(
            f"INPUT ERROR: --skill is only valid for the single layout, not {layout}",
            file=sys.stderr,
        )
        return 2
    if os.path.lexists(destination):
        print(
            f"INPUT ERROR: destination already exists: {destination}",
            file=sys.stderr,
        )
        return 2
    bundle_resolved = bundle.resolve()
    destination_resolved = destination.resolve()
    try:
        destination_resolved.relative_to(bundle_resolved)
    except ValueError:
        pass
    else:
        print(
            f"INPUT ERROR: destination is inside the bundle: {destination}",
            file=sys.stderr,
        )
        return 2

    try:
        catalog = load_catalog(bundle)
    except CHECK_BUNDLE.InputError as error:
        print(f"INPUT ERROR: {error}", file=sys.stderr)
        return 2

    if layout == "single":
        try:
            closure = resolve_closure(bundle, catalog, [skill])
        except InputError as error:
            print(f"INPUT ERROR: {error}", file=sys.stderr)
            return 2
    else:
        closure = [entry["id"] for entry in catalog["skills"]]

    paths = distribution_paths(bundle, layout, closure)

    destination.mkdir(parents=True)
    links: dict[str, str] = {}
    file_hashes: dict[str, str] = {}
    try:
        for relative in paths:
            source = bundle / relative
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if layout == "symlink":
                os.symlink(source.resolve(), target, target_is_directory=source.is_dir())
                links[relative] = str(source.resolve())
            elif source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)
            if layout != "symlink" and source.is_dir():
                for member in sorted(source.rglob("*")):
                    if member.is_file():
                        member_relative = (
                            Path(relative) / member.relative_to(source)
                        ).as_posix()
                        file_hashes[member_relative] = digest(member)
            elif layout != "symlink" and source.is_file():
                file_hashes[relative] = digest(source)
    except PermissionError as error:
        print(
            f"INPUT ERROR: permission denied while staging ({error}); "
            f"partial output remains at {destination}; remove it manually or "
            "choose a different destination",
            file=sys.stderr,
        )
        return 2
    except OSError as error:
        if layout == "symlink" and getattr(error, "winerror", None) in (1314, 1925):
            print(
                f"INPUT ERROR: creating symlinks requires elevated permission on "
                f"this system ({error}); partial output remains at {destination}; "
                "remove it manually or choose a different destination",
                file=sys.stderr,
            )
            return 2
        raise

    manifest = {
        "kind": "devflow-install-manifest",
        "schema_version": 1,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "layout": layout,
        "skills": closure,
        "source_bundle": str(bundle_resolved),
        "paths": paths,
        "links": links,
        "file_sha256": file_hashes,
    }
    (destination / MANIFEST_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"STAGED {layout} layout: {len(closure)} skills, "
        f"{len(paths)} distribution entries -> {destination}"
    )
    return 0


def verify(bundle: Path, install_root: Path) -> int:
    manifest_path = install_root / MANIFEST_NAME
    if not manifest_path.is_file():
        print(
            f"INPUT ERROR: {MANIFEST_NAME} not found under install root: {install_root}",
            file=sys.stderr,
        )
        return 2
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"INPUT ERROR: cannot read install manifest: {error}", file=sys.stderr)
        return 2
    try:
        catalog = load_catalog(bundle)
    except CHECK_BUNDLE.InputError as error:
        print(f"INPUT ERROR: {error}", file=sys.stderr)
        return 2
    by_id = {entry["id"]: entry for entry in catalog["skills"]}

    errors: list[str] = []
    for skill_id in manifest["skills"]:
        skill = by_id.get(skill_id)
        if skill is None:
            errors.append(f"skill '{skill_id}' is not in the source catalog")
            continue
        entry = install_root / skill["entry"]
        if not entry.is_file():
            errors.append(f"{skill['entry']}: missing from install")
        for resource in skill["required_resources"]:
            if not (install_root / resource).is_file():
                errors.append(f"{resource}: missing from install (declared by {skill_id})")

    mirror = "templates/project-overrides.md"
    authoritative = "skills/using-devflow/references/project-overrides.md"
    if "using-devflow" in manifest["skills"] and manifest["layout"] != "symlink":
        mirror_path = install_root / mirror
        authoritative_path = install_root / authoritative
        if mirror_path.is_file() and authoritative_path.is_file():
            if mirror_path.read_bytes() != authoritative_path.read_bytes():
                errors.append(f"{mirror}: template copy is out of sync in install")

    skills_root = install_root / "skills"
    if skills_root.is_dir():
        for path in sorted(skills_root.rglob("*.md")):
            text = path.read_text(encoding="utf-8", errors="replace")
            for reference in extract_references(text):
                if reference.startswith(("http", "mailto:")):
                    continue
                target = (path.parent / reference).resolve()
                if not target.exists():
                    relative = path.relative_to(install_root).as_posix()
                    try:
                        missing = target.relative_to(install_root.resolve()).as_posix()
                    except ValueError:
                        missing = reference.replace("\\", "/")
                    errors.append(
                        f"{relative}: broken reference -> {missing}"
                    )

    if manifest["layout"] == "symlink":
        for relative, recorded_target in manifest["links"].items():
            staged = install_root / relative
            if not staged.is_symlink():
                errors.append(f"{relative}: expected a symlink, found a copied path")
                continue
            actual_target = os.path.realpath(staged)
            recorded_normalized = os.path.normcase(
                os.path.normpath(str(Path(recorded_target)))
            )
            if os.path.normcase(actual_target) != recorded_normalized:
                errors.append(
                    f"{relative}: does not point at the recorded source {recorded_target}"
                )
            elif not Path(recorded_target).exists():
                errors.append(f"{relative}: link target no longer exists")
    else:
        for relative, recorded_hash in manifest["file_sha256"].items():
            staged = install_root / relative
            if not staged.is_file():
                errors.append(f"{relative}: missing from install")
            elif digest(staged) != recorded_hash:
                errors.append(f"{relative}: differs from staged source bytes")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"INSTALL VERIFY FAILED: {len(errors)} error(s)")
        return 1
    print(
        f"INSTALL VERIFY PASSED: layout={manifest['layout']}, "
        f"{len(manifest['skills'])} skills, references resolve"
    )
    return 0


def directory_state(bundle: Path, directory: Path) -> tuple[int, str | None]:
    """Return (file count, first differing relative path) versus the bundle."""
    count = 0
    for member in sorted(directory.rglob("*")):
        if not member.is_file():
            continue
        count += 1
        relative = member.relative_to(directory)
        source = bundle / relative
        if not source.is_file() or source.read_bytes() != member.read_bytes():
            return count, relative.as_posix()
    return count, None


def plan(bundle: Path, target: Path) -> int:
    try:
        catalog = load_catalog(bundle)
    except CHECK_BUNDLE.InputError as error:
        print(f"INPUT ERROR: {error}", file=sys.stderr)
        return 2
    catalog_ids = {entry["id"] for entry in catalog["skills"]}

    try:
        version = json.loads(
            (bundle / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        ).get("version")
    except (OSError, json.JSONDecodeError):
        version = None
    print(f"bundle version: {version if version is not None else 'unknown'}")

    if not target.exists():
        print(f"target does not exist: {target} (fresh install)")
        print("planned resources (full layout):")
        for skill_id in sorted(catalog_ids):
            print(f"  skills/{skill_id}")
        for name in DISTRIBUTION_ROOT_FILES:
            if (bundle / name).is_file():
                print(f"  {name}")
        return 0

    print(f"target: {target}")
    known_root = {name for name in DISTRIBUTION_ROOT_FILES if (bundle / name).is_file()}
    known_root_directories = {
        part for name in known_root for part in Path(name).parts[:-1]
    }

    for skill_id in sorted(catalog_ids):
        target_skill = target / "skills" / skill_id
        if not target_skill.is_dir():
            print(f"skills/{skill_id}: not installed")
            continue
        count, difference = directory_state(bundle / "skills" / skill_id, target_skill)
        if difference is None:
            print(f"skills/{skill_id}: matches bundle ({count} files)")
        else:
            print(f"skills/{skill_id}: differs from bundle at {difference}")

    if (target / "skills").is_dir():
        for entry in sorted((target / "skills").iterdir()):
            if entry.is_dir() and entry.name not in catalog_ids:
                print(f"{entry.relative_to(target).as_posix()}: unknown source")

    for entry in sorted(target.iterdir()):
        if entry.is_dir() and entry.name == "skills":
            continue
        relative = entry.relative_to(target).as_posix()
        if relative not in known_root and entry.name not in known_root_directories:
            print(f"{relative}: unknown source")

    target_version = None
    target_plugin = target / ".claude-plugin" / "plugin.json"
    if target_plugin.is_file():
        try:
            target_version = json.loads(target_plugin.read_text(encoding="utf-8")).get(
                "version"
            )
        except (OSError, json.JSONDecodeError):
            target_version = None
    if target_version != version:
        print(f"version differs: bundle={version} target={target_version}")
    print("planned resources (full layout):")
    for skill_id in sorted(catalog_ids):
        print(f"  skills/{skill_id}")
    for name in sorted(known_root):
        print(f"  {name}")
    print("recovery scope: bundle-named paths only; unknown sources and custom files are preserved")
    return 0


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    plan_parser = commands.add_parser("plan", help="read-only target inventory")
    plan_parser.add_argument("--bundle", required=True)
    plan_parser.add_argument("--target", required=True)

    stage_parser = commands.add_parser("stage", help="stage into a new destination")
    stage_parser.add_argument("--bundle", required=True)
    stage_parser.add_argument("--layout", choices=["full", "single", "symlink"], required=True)
    stage_parser.add_argument("--skill")
    stage_parser.add_argument("--dest", required=True)

    verify_parser = commands.add_parser("verify", help="verify a staged install")
    verify_parser.add_argument("--bundle", required=True)
    verify_parser.add_argument("--install-root", required=True)

    return parser.parse_args(argv)


def main() -> int:
    arguments = parse_arguments()
    bundle = Path(arguments.bundle)
    if not bundle.is_dir():
        print(f"INPUT ERROR: bundle root is not a directory: {bundle}", file=sys.stderr)
        return 2
    if arguments.command == "plan":
        return plan(bundle, Path(arguments.target))
    if arguments.command == "stage":
        return stage(bundle, arguments.layout, arguments.skill, Path(arguments.dest))
    if arguments.command == "verify":
        return verify(bundle, Path(arguments.install_root))
    raise AssertionError(f"unhandled command {arguments.command}")


if __name__ == "__main__":
    sys.exit(main())
