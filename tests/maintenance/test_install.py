import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


INSTALLER = Path(__file__).resolve().parents[2] / "scripts" / "install-bundle.py"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def make_skill(root, skill_id, body="Guidance.\n", links=()):
    directory = root / "skills" / skill_id
    directory.mkdir(parents=True, exist_ok=True)
    link_text = "\n".join(f"- [{name}]({target})" for name, target in links)
    (directory / "SKILL.md").write_text(
        f"---\nname: {skill_id}\ndescription: Skill.\n---\n\n{body}\n{link_text}\n",
        encoding="utf-8",
    )
    return directory


def make_catalog(root, skills):
    path = root / "skills" / "devflow" / "references" / "skill-catalog.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    for skill_id, required_resources, aliases in skills:
        entries.append(
            {
                "id": skill_id,
                "entry": f"skills/{skill_id}/SKILL.md",
                "route_tags": ["test"],
                "required_resources": required_resources,
                "aliases": aliases,
            }
        )
    path.write_text(
        json.dumps({"schema_version": 1, "skills": entries}, ensure_ascii=False),
        encoding="utf-8",
    )


def make_bundle(root, *, mirror=True):
    make_skill(root, "devflow")
    authoritative = root / "skills" / "using-devflow" / "references" / "project-overrides.md"
    authoritative.parent.mkdir(parents=True, exist_ok=True)
    authoritative.write_text("# Template\n\nRules.\n", encoding="utf-8")
    make_skill(
        root,
        "using-devflow",
        links=[("template", "references/project-overrides.md")],
    )
    make_skill(
        root,
        "api-and-interface-design",
        links=[
            ("shared", "../using-devflow/references/project-overrides.md"),
            ("router", "../devflow/SKILL.md"),
        ],
    )
    make_skill(root, "isolated-skill")
    mirror_path = root / "templates" / "project-overrides.md"
    if mirror:
        mirror_path.parent.mkdir(parents=True, exist_ok=True)
        mirror_path.write_text("# Template\n\nRules.\n", encoding="utf-8")
    make_catalog(
        root,
        [
            ("devflow", ["skills/devflow/references/skill-catalog.json"], []),
            (
                "using-devflow",
                [
                    "skills/using-devflow/references/project-overrides.md",
                    "templates/project-overrides.md",
                ],
                [],
            ),
            ("api-and-interface-design", [], []),
            ("isolated-skill", [], []),
        ],
    )
    return root


class InstallToolTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary_directory.name)
        self.bundle = make_bundle(self.base / "bundle")
        self.work = self.base / "work"
        self.work.mkdir()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def run_installer(self, *arguments):
        return subprocess.run(
            [sys.executable, str(INSTALLER), *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def stage(self, layout, *extra, bundle=None):
        destination = self.work / f"stage-{layout}"
        return (
            self.run_installer(
                "stage",
                "--bundle",
                str(bundle or self.bundle),
                "--layout",
                layout,
                *extra,
                "--dest",
                str(destination),
            ),
            destination,
        )

    def verify(self, install_root, bundle=None):
        return self.run_installer(
            "verify",
            "--bundle",
            str(bundle or self.bundle),
            "--install-root",
            str(install_root),
        )

    def write_manifest(self, destination, manifest):
        (destination / "install-manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

    def read_manifest(self, destination):
        return json.loads((destination / "install-manifest.json").read_text(encoding="utf-8"))

    def assert_manifest_error(self, destination):
        result = self.verify(destination)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("INPUT ERROR:", result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        self.assertNotIn("INSTALL VERIFY PASSED", result.stdout)

    def test_verify_rejects_empty_and_malformed_manifest_objects(self):
        destination = self.work / "empty-install"
        destination.mkdir()
        for manifest in ({}, [], None, {"skills": [], "layout": "weird", "links": {}, "file_sha256": {}}):
            with self.subTest(manifest=manifest):
                self.write_manifest(destination, manifest)
                self.assert_manifest_error(destination)

    def test_verify_validates_manifest_fields_before_using_them(self):
        result, destination = self.stage("full")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        original = self.read_manifest(destination)
        invalid_values = {
            "kind": [None, "other-manifest"],
            "schema_version": [True, 2, "1"],
            "created_at": [None, "not-a-time"],
            "layout": ["weird", [], None],
            "skills": [[], "devflow", [{}], ["ghost"], ["devflow", "devflow"]],
            "source_bundle": [None, "relative/path"],
            "paths": [[], "skills/devflow", [{}]],
            "links": [[], {"skills/devflow": None}],
            "file_sha256": [[], {"skills/devflow/SKILL.md": None}, {"skills/devflow/SKILL.md": "invalid"}],
        }
        for field, values in invalid_values.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    self.write_manifest(destination, {**original, field: value})
                    self.assert_manifest_error(destination)
        for field in original:
            with self.subTest(missing=field):
                self.write_manifest(destination, {key: value for key, value in original.items() if key != field})
                self.assert_manifest_error(destination)

    def test_verify_rejects_undecodable_manifest_without_traceback(self):
        destination = self.work / "invalid-encoding"
        destination.mkdir()
        (destination / "install-manifest.json").write_bytes(b"\xff")
        self.assert_manifest_error(destination)

    def test_verify_requires_exact_full_skill_and_distribution_coverage(self):
        result, destination = self.stage("full")
        self.assertEqual(result.returncode, 0)
        original = self.read_manifest(destination)
        for field, value in (
            ("skills", original["skills"][:-1]),
            ("paths", original["paths"][:-1]),
            ("paths", original["paths"] + [original["paths"][0]]),
            ("paths", original["paths"] + ["unexpected.txt"]),
            ("file_sha256", {}),
            ("file_sha256", {**original["file_sha256"], "unexpected.txt": "0" * 64}),
            ("links", {"skills/devflow": str(self.bundle / "skills" / "devflow")}),
        ):
            with self.subTest(field=field, value=value):
                self.write_manifest(destination, {**original, field: value})
                self.assert_manifest_error(destination)

    def test_verify_rejects_escaping_or_noncanonical_path_declarations(self):
        result, destination = self.stage("full")
        self.assertEqual(result.returncode, 0)
        original = self.read_manifest(destination)
        for path in ("../outside.txt", "/outside.txt", "C:/outside.txt", "C:outside.txt", "skills\\devflow", "skills/./devflow", "skills//devflow", "skills/devflow/", "skills/devflow/../devflow", "bad\x00path"):
            for field in ("paths", "file_sha256", "links"):
                with self.subTest(path=path, field=field):
                    if field == "paths":
                        value = original[field] + [path]
                    else:
                        value = {**original[field], path: "0" * 64 if field == "file_sha256" else str(self.bundle)}
                    self.write_manifest(destination, {**original, field: value})
                    self.assert_manifest_error(destination)

    def test_verify_single_manifest_requires_one_complete_dependency_closure(self):
        result, destination = self.stage("single", "--skill", "api-and-interface-design")
        self.assertEqual(result.returncode, 0)
        original = self.read_manifest(destination)
        for skills in (["api-and-interface-design"], original["skills"] + ["isolated-skill"]):
            with self.subTest(skills=skills):
                # Keep the declared paths/hashes consistent with the false skill set.
                changed = {**original, "skills": skills}
                changed["paths"] = [f"skills/{skill}" for skill in skills] + ["templates/project-overrides.md"]
                changed["file_sha256"] = {
                    path: value for path, value in original["file_sha256"].items()
                    if not path.startswith("skills/") or path.split("/")[1] in skills
                }
                if "isolated-skill" in skills:
                    path = "skills/isolated-skill/SKILL.md"
                    changed["file_sha256"][path] = hashlib.sha256((self.bundle / path).read_bytes()).hexdigest()
                    shutil.copytree(self.bundle / "skills" / "isolated-skill", destination / "skills" / "isolated-skill")
                self.write_manifest(destination, changed)
                self.assert_manifest_error(destination)

    def test_verify_cannot_hide_modified_content_by_rewriting_manifest_hash(self):
        result, destination = self.stage("full")
        self.assertEqual(result.returncode, 0)
        path = "skills/isolated-skill/SKILL.md"
        (destination / path).write_text("Changed guidance.\n", encoding="utf-8")
        manifest = self.read_manifest(destination)
        manifest["file_sha256"][path] = hashlib.sha256((destination / path).read_bytes()).hexdigest()
        self.write_manifest(destination, manifest)

        result = self.verify(destination)

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(path, result.stdout)
        self.assertIn("source bundle", result.stdout)

    def test_verify_copied_install_is_bound_to_supplied_bundle_bytes(self):
        result, destination = self.stage("full")
        self.assertEqual(result.returncode, 0)
        (self.bundle / "skills" / "isolated-skill" / "SKILL.md").write_text("New source.\n", encoding="utf-8")

        result = self.verify(destination)

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("source bundle", result.stdout)

    def test_verify_symlink_manifest_requires_complete_link_coverage(self):
        result, destination = self.stage("symlink")
        if result.returncode == 2 and "permission" in result.stderr.lower():
            self.skipTest("symlink creation is unavailable on this host")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        original = self.read_manifest(destination)
        for field, value in (
            ("skills", original["skills"][:-1]),
            ("links", {}),
            ("links", {**original["links"], "unexpected.txt": str(self.bundle)}),
            ("file_sha256", {"skills/devflow/SKILL.md": "0" * 64}),
        ):
            with self.subTest(field=field, value=value):
                self.write_manifest(destination, {**original, field: value})
                self.assert_manifest_error(destination)

    def test_verify_cannot_hide_relinked_skill_by_rewriting_manifest_target(self):
        result, destination = self.stage("symlink")
        if result.returncode == 2 and "permission" in result.stderr.lower():
            self.skipTest("symlink creation is unavailable on this host")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        relative = "skills/isolated-skill"
        replacement = self.work / "replacement"
        shutil.copytree(self.bundle / relative, replacement)
        (destination / relative).unlink()
        (destination / relative).symlink_to(replacement, target_is_directory=True)
        manifest = self.read_manifest(destination)
        manifest["links"][relative] = str(replacement.resolve())
        self.write_manifest(destination, manifest)

        result = self.verify(destination)

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("source bundle", result.stdout)

    def make_directory_link(self, target, link):
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError as error:
            if isinstance(error, PermissionError) or getattr(error, "winerror", None) in (1314, 1925):
                self.skipTest("symlink creation is unavailable on this host")
            raise

    def test_source_directory_links_are_copied_and_fully_hashed(self):
        assets = self.bundle / "shared-assets"
        (assets / "nested").mkdir(parents=True)
        (assets / "nested" / "payload.json").write_text('{"version": 1}', encoding="utf-8")
        for name in ("assets", "assets-alias"):
            self.make_directory_link(assets, self.bundle / "skills" / "isolated-skill" / name)
        for layout, extra in (("full", ()), ("single", ("--skill", "isolated-skill"))):
            with self.subTest(layout=layout):
                result, destination = self.stage(layout, *extra)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                manifest = self.read_manifest(destination)
                for name in ("assets", "assets-alias"):
                    relative = f"skills/isolated-skill/{name}/nested/payload.json"
                    self.assertIn(relative, manifest["file_sha256"])
                    self.assertEqual((destination / relative).read_text(encoding="utf-8"), '{"version": 1}')
                    self.assertFalse((destination / "skills" / "isolated-skill" / name).is_symlink())
                clean = self.verify(destination)
                self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)
                payload = destination / "skills" / "isolated-skill" / "assets" / "nested" / "payload.json"
                payload.write_text('{"version": 2}', encoding="utf-8")
                changed = self.verify(destination)
                self.assertEqual(changed.returncode, 1, changed.stdout + changed.stderr)
                self.assertIn("skills/isolated-skill/assets/nested/payload.json", changed.stdout)

    def test_source_directory_link_file_hash_cannot_be_omitted(self):
        assets = self.bundle / "shared-assets"
        assets.mkdir()
        (assets / "payload.json").write_text("{}", encoding="utf-8")
        self.make_directory_link(assets, self.bundle / "skills" / "isolated-skill" / "assets")
        result, destination = self.stage("full")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = self.read_manifest(destination)
        manifest["file_sha256"].pop("skills/isolated-skill/assets/payload.json", None)
        self.write_manifest(destination, manifest)
        self.assert_manifest_error(destination)

    def test_source_directory_link_cycle_is_rejected_before_staging(self):
        skill = self.bundle / "skills" / "isolated-skill"
        self.make_directory_link(skill, skill / "cycle")
        for layout in ("full", "symlink"):
            with self.subTest(layout=layout):
                result, destination = self.stage(layout)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("cycle", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse(destination.exists())

    def test_source_directory_link_outside_bundle_is_rejected_before_staging(self):
        external = self.work / "external-assets"
        external.mkdir()
        (external / "payload.json").write_text("{}", encoding="utf-8")
        self.make_directory_link(external, self.bundle / "skills" / "isolated-skill" / "assets")
        for layout in ("full", "symlink"):
            with self.subTest(layout=layout):
                result, destination = self.stage(layout)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("escapes bundle", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse(destination.exists())

    def test_plan_on_absent_target_is_read_only(self):
        target = self.work / "absent-target"

        result = self.run_installer(
            "plan", "--bundle", str(self.bundle), "--target", str(target)
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("target does not exist", result.stdout)
        self.assertIn("planned resources", result.stdout)
        self.assertFalse(target.exists(), "plan must not create the target")

    def test_plan_reports_unknown_sources_conflicts_and_custom_files(self):
        target = self.work / "existing"
        target.mkdir()
        (target / "skills" / "using-devflow" / "SKILL.md").parent.mkdir(parents=True)
        (target / "skills" / "using-devflow" / "SKILL.md").write_text(
            "---\nname: using-devflow\ndescription: Old.\n---\n", encoding="utf-8"
        )
        (target / "skills" / "personal-notes" / "SKILL.md").parent.mkdir(parents=True)
        (target / "skills" / "personal-notes" / "SKILL.md").write_text(
            "---\nname: personal-notes\ndescription: Mine.\n---\n", encoding="utf-8"
        )
        (target / "user-config.json").write_text("{}", encoding="utf-8")

        result = self.run_installer(
            "plan", "--bundle", str(self.bundle), "--target", str(target)
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("skills/personal-notes: unknown source", result.stdout)
        self.assertIn("user-config.json: unknown source", result.stdout)
        self.assertIn("skills/using-devflow: differs from bundle", result.stdout)
        self.assertIn(
            (target / "user-config.json").read_text(encoding="utf-8"),
            "{}",
            "plan must not modify target content",
        )

    def test_stage_full_copies_distribution_and_verify_passes(self):
        result, destination = self.stage("full")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((destination / "skills" / "using-devflow" / "SKILL.md").is_file())
        self.assertTrue((destination / "templates" / "project-overrides.md").is_file())
        verification = self.verify(destination)
        self.assertEqual(verification.returncode, 0, verification.stdout + verification.stderr)

    def test_stage_single_resolves_dependency_closure(self):
        result, destination = self.stage("single", "--skill", "api-and-interface-design")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(
            (destination / "skills" / "api-and-interface-design" / "SKILL.md").is_file()
        )
        self.assertTrue(
            (destination / "skills" / "using-devflow" / "references" / "project-overrides.md").is_file()
        )
        self.assertTrue((destination / "templates" / "project-overrides.md").is_file())
        self.assertFalse(
            (destination / "skills" / "isolated-skill").exists(),
            "skills outside the closure must not be staged",
        )
        verification = self.verify(destination)
        self.assertEqual(verification.returncode, 0, verification.stdout + verification.stderr)

    def test_stage_single_requires_known_skill(self):
        result, _ = self.stage("single", "--skill", "ghost")

        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown skill 'ghost'", result.stderr)

    def test_stage_refuses_existing_destination(self):
        destination = self.work / "already-there"
        destination.mkdir()
        (destination / "keep.txt").write_text("mine", encoding="utf-8")

        result = self.run_installer(
            "stage",
            "--bundle",
            str(self.bundle),
            "--layout",
            "full",
            "--dest",
            str(destination),
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("already exists", result.stderr)
        self.assertEqual(
            (destination / "keep.txt").read_text(encoding="utf-8"), "mine"
        )

    def test_stage_refuses_destination_inside_bundle(self):
        destination = self.bundle / "skills" / "escaped"

        result = self.run_installer(
            "stage",
            "--bundle",
            str(self.bundle),
            "--layout",
            "full",
            "--dest",
            str(destination),
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("inside the bundle", result.stderr)
        self.assertFalse(destination.exists())

    def test_verify_reports_missing_template(self):
        result, destination = self.stage("full")
        self.assertEqual(result.returncode, 0)
        (destination / "templates" / "project-overrides.md").unlink()

        result = self.verify(destination)

        self.assertEqual(result.returncode, 1)
        self.assertIn("templates/project-overrides.md", result.stdout)
        self.assertIn("missing from install", result.stdout)

    def test_verify_reports_broken_link(self):
        result, destination = self.stage("single", "--skill", "using-devflow")
        self.assertEqual(result.returncode, 0)
        entry = destination / "skills" / "using-devflow" / "SKILL.md"
        entry.write_text(
            entry.read_text(encoding="utf-8").replace(
                "references/project-overrides.md", "references/vanished.md"
            ),
            encoding="utf-8",
        )

        result = self.verify(destination)

        self.assertEqual(result.returncode, 1)
        self.assertIn("skills/using-devflow/references/vanished.md", result.stdout)
        self.assertIn("broken reference", result.stdout)

    def test_verify_reports_unmet_dependency(self):
        result, destination = self.stage("single", "--skill", "api-and-interface-design")
        self.assertEqual(result.returncode, 0)
        entry = destination / "skills" / "api-and-interface-design" / "SKILL.md"
        entry.unlink()

        result = self.verify(destination)

        self.assertEqual(result.returncode, 1)
        self.assertIn("skills/api-and-interface-design/SKILL.md", result.stdout)
        self.assertIn("missing from install", result.stdout)

    def test_symlink_layout_uses_real_links_or_fails_honestly(self):
        probe = self.work / "probe"
        probe.mkdir()
        link = probe / "link"
        try:
            os.symlink(probe, link, target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            result, _ = self.stage("symlink")
            self.assertEqual(result.returncode, 2)
            self.assertIn("symlink", result.stderr.lower())
            self.assertIn("permission", (result.stderr + result.stdout).lower())
            return
        finally:
            if link.is_symlink():
                link.unlink()

        result, destination = self.stage("symlink")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        staged_skill = destination / "skills" / "using-devflow"
        self.assertTrue(staged_skill.is_symlink(), "skill directory must be a real symlink")
        verification = self.verify(destination)
        self.assertEqual(verification.returncode, 0, verification.stdout + verification.stderr)

        copied = self.work / "masquerade"
        copied.mkdir()
        shutil.copytree(staged_skill, copied / "using-devflow", symlinks=False)
        staged_skill.unlink()
        shutil.copytree(copied / "using-devflow", destination / "skills" / "using-devflow")
        plain_copy = self.verify(destination)
        self.assertEqual(plain_copy.returncode, 1)
        self.assertIn("expected a symlink, found a copied path", plain_copy.stdout)

        shutil.rmtree(destination / "skills" / "using-devflow")
        (destination / "skills" / "using-devflow").symlink_to(
            copied / "using-devflow", target_is_directory=True
        )
        relinked = self.verify(destination)
        self.assertEqual(relinked.returncode, 1)
        self.assertIn("does not point at the recorded source", relinked.stdout)

    def test_closure_survives_reference_cycles(self):
        make_skill(
            self.bundle,
            "cycler-a",
            links=[("b", "../cycler-b/SKILL.md")],
        )
        make_skill(
            self.bundle,
            "cycler-b",
            links=[("a", "../cycler-a/SKILL.md")],
        )
        catalog_path = self.bundle / "skills" / "devflow" / "references" / "skill-catalog.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        catalog["skills"].extend(
            [
                {
                    "id": "cycler-a",
                    "entry": "skills/cycler-a/SKILL.md",
                    "route_tags": ["test"],
                    "required_resources": [],
                    "aliases": [],
                },
                {
                    "id": "cycler-b",
                    "entry": "skills/cycler-b/SKILL.md",
                    "route_tags": ["test"],
                    "required_resources": [],
                    "aliases": [],
                },
            ]
        )
        catalog_path.write_text(json.dumps(catalog), encoding="utf-8")

        result, destination = self.stage("single", "--skill", "cycler-a")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((destination / "skills" / "cycler-a" / "SKILL.md").is_file())
        self.assertTrue((destination / "skills" / "cycler-b" / "SKILL.md").is_file())

    def test_switch_failure_drill_recovers_with_custom_content_preserved(self):
        """Simulated switch-over drill from docs/devflow/installation.md.

        Valid install -> valid candidate -> authorized switch fails with an
        interrupted first write -> bounded recovery from backup -> the
        install verifies again and custom content survives untouched.
        """
        result, candidate = self.stage("full")
        self.assertEqual(result.returncode, 0)

        active = self.work / "active"
        shutil.copytree(candidate, active)
        custom = active / "user-config.json"
        custom.write_text('{"theme": "dark"}', encoding="utf-8")
        personal = active / "skills" / "personal-notes" / "SKILL.md"
        personal.parent.mkdir(parents=True)
        personal.write_text(
            "---\nname: personal-notes\ndescription: Mine.\n---\n", encoding="utf-8"
        )
        plan_before = self.run_installer(
            "plan", "--bundle", str(self.bundle), "--target", str(active)
        )
        self.assertEqual(plan_before.returncode, 0)
        self.assertIn("skills/personal-notes: unknown source", plan_before.stdout)
        self.assertIn("user-config.json: unknown source", plan_before.stdout)

        manifest = json.loads(
            (candidate / "install-manifest.json").read_text(encoding="utf-8")
        )
        recovery = self.work / "recovery"
        recovery.mkdir()
        owned_paths = [path for path in manifest["paths"] if (active / path).exists()]
        self.assertGreater(len(owned_paths), 0)
        for relative in owned_paths:
            source = active / relative
            target = recovery / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)

        first_relative = owned_paths[0]
        interrupted = active / first_relative / "SKILL.md"
        interrupted.write_text(
            interrupted.read_text(encoding="utf-8")[:20], encoding="utf-8"
        )

        failed = self.verify(active)
        self.assertEqual(failed.returncode, 1)
        self.assertIn(first_relative, failed.stdout)

        for relative in owned_paths:
            target = recovery / relative
            if target.is_dir():
                shutil.rmtree(active / relative)
                shutil.copytree(target, active / relative)
            else:
                shutil.copy2(target, active / relative)

        restored = self.verify(active)
        self.assertEqual(restored.returncode, 0, restored.stdout + restored.stderr)
        self.assertEqual(custom.read_text(encoding="utf-8"), '{"theme": "dark"}')
        self.assertTrue(personal.is_file())
        plan_after = self.run_installer(
            "plan", "--bundle", str(self.bundle), "--target", str(active)
        )
        self.assertEqual(plan_after.returncode, 0)
        self.assertIn("skills/personal-notes: unknown source", plan_after.stdout)
        self.assertIn("user-config.json: unknown source", plan_after.stdout)

    def test_repository_bundle_full_layout_stages_and_verifies(self):
        destination = self.work / "repo-full"

        result = self.run_installer(
            "stage",
            "--bundle",
            str(REPOSITORY_ROOT),
            "--layout",
            "full",
            "--dest",
            str(destination),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        verification = self.verify(destination, bundle=REPOSITORY_ROOT)
        self.assertEqual(verification.returncode, 0, verification.stdout + verification.stderr)

    def test_repository_bundle_single_layout_stages_and_verifies(self):
        destination = self.work / "repo-single"

        result = self.run_installer(
            "stage",
            "--bundle",
            str(REPOSITORY_ROOT),
            "--layout",
            "single",
            "--skill",
            "security-and-hardening",
            "--dest",
            str(destination),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(
            (destination / "skills" / "using-devflow" / "references" / "phase-contract.md").is_file()
        )

        verification = self.verify(destination, bundle=REPOSITORY_ROOT)
        self.assertEqual(verification.returncode, 0, verification.stdout + verification.stderr)


if __name__ == "__main__":
    unittest.main()
