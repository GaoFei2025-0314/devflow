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
        subprocess.run(
            ["cp", "-r", str(staged_skill) + "/", str(copied / "using-devflow")],
            check=True,
        )
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
