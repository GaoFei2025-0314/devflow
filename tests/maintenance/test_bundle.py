import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


CHECKER = Path(__file__).resolve().parents[2] / "scripts" / "check-bundle.py"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class BundleCheckerTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def write_skill(self, skill_id, *, frontmatter_name=None, support_files=()):
        skill_directory = self.root / "skills" / skill_id
        skill_directory.mkdir(parents=True)
        name = frontmatter_name or skill_id
        (skill_directory / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Test skill.\n---\n",
            encoding="utf-8",
        )
        for relative_path in support_files:
            path = self.root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("support\n", encoding="utf-8")

    def write_catalog(self, skills, **extra_fields):
        path = self.root / "skills" / "devflow" / "references" / "skill-catalog.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        catalog = {"schema_version": 1, "skills": skills}
        catalog.update(extra_fields)
        path.write_text(
            json.dumps(catalog, ensure_ascii=False),
            encoding="utf-8",
        )

    @staticmethod
    def catalog_skill(skill_id, *, aliases=None, required_resources=None):
        return {
            "id": skill_id,
            "entry": f"skills/{skill_id}/SKILL.md",
            "route_tags": ["test"],
            "required_resources": required_resources or [],
            "aliases": aliases or [],
        }

    def run_checker(self):
        return subprocess.run(
            [sys.executable, str(CHECKER), "--root", str(self.root)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def test_valid_small_unicode_bundle_passes_without_assuming_33_skills(self):
        self.write_skill("devflow")
        router = self.root / "skills" / "devflow" / "SKILL.md"
        router.write_text(
            router.read_text(encoding="utf-8")
            + f"\n- [文档-review](../文档-review/SKILL.md)\n",
            encoding="utf-8",
        )
        self.write_skill(
            "文档-review",
            support_files=("skills/文档-review/references/guide.md",),
        )
        self.write_catalog(
            [
                self.catalog_skill("devflow", aliases=["router"]),
                self.catalog_skill(
                    "文档-review",
                    required_resources=["skills/文档-review/references/guide.md"],
                ),
            ]
        )

        result = self.run_checker()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("2 skills", result.stdout)

    def test_name_directory_mismatch_identifies_entry(self):
        self.write_skill("devflow", frontmatter_name="different-name")
        self.write_catalog([self.catalog_skill("devflow")])

        result = self.run_checker()

        self.assertEqual(result.returncode, 1)
        self.assertIn("skills/devflow/SKILL.md", result.stdout)
        self.assertIn("name 'different-name' does not match directory 'devflow'", result.stdout)

    def test_body_name_does_not_substitute_for_opening_frontmatter(self):
        self.write_skill("devflow")
        entry = self.root / "skills" / "devflow" / "SKILL.md"
        entry.write_text("# Skill\n\nname: devflow\n", encoding="utf-8")
        self.write_catalog([self.catalog_skill("devflow")])

        result = self.run_checker()

        self.assertEqual(result.returncode, 1)
        self.assertIn("skills/devflow/SKILL.md", result.stdout)
        self.assertIn("missing name in opening YAML frontmatter", result.stdout)

    def test_alternate_entry_cannot_bypass_canonical_skill_file(self):
        self.write_skill("devflow", frontmatter_name="wrong-name")
        alternate = self.root / "skills" / "devflow" / "ALTERNATE.md"
        alternate.write_text(
            "---\nname: devflow\ndescription: Alternate.\n---\n",
            encoding="utf-8",
        )
        skill = self.catalog_skill("devflow")
        skill["entry"] = "skills/devflow/ALTERNATE.md"
        self.write_catalog([skill])

        result = self.run_checker()

        self.assertEqual(result.returncode, 1)
        self.assertIn("skills/devflow/ALTERNATE.md", result.stdout)
        self.assertIn("entry must be canonical path 'skills/devflow/SKILL.md'", result.stdout)

    def test_entry_uses_portable_posix_relative_path(self):
        self.write_skill("devflow")
        skill = self.catalog_skill("devflow")
        skill["entry"] = "skills\\devflow\\SKILL.md"
        self.write_catalog([skill])

        result = self.run_checker()

        self.assertEqual(result.returncode, 1)
        self.assertIn("entry must be canonical path 'skills/devflow/SKILL.md'", result.stdout)

    def test_missing_required_resource_identifies_resource(self):
        self.write_skill("devflow")
        missing = "skills/devflow/references/missing.md"
        self.write_catalog(
            [self.catalog_skill("devflow", required_resources=[missing])]
        )

        result = self.run_checker()

        self.assertEqual(result.returncode, 1)
        self.assertIn(missing, result.stdout)
        self.assertIn("required resource does not exist", result.stdout)

    def test_required_resource_outside_root_is_rejected(self):
        self.write_skill("devflow")
        escaped = "../outside.md"
        self.write_catalog(
            [self.catalog_skill("devflow", required_resources=[escaped])]
        )

        result = self.run_checker()

        self.assertEqual(result.returncode, 1)
        self.assertIn(escaped, result.stdout)
        self.assertIn("path escapes bundle root", result.stdout)

    def test_malformed_required_resource_path_has_diagnostic_without_traceback(self):
        self.write_skill("devflow")
        malformed = "bad\x00path"
        self.write_catalog(
            [self.catalog_skill("devflow", required_resources=[malformed])]
        )

        result = self.run_checker()

        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid declared path 'bad\\x00path'", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_duplicate_canonical_ids_identifies_id(self):
        self.write_skill("devflow")
        skill = self.catalog_skill("devflow")
        self.write_catalog([skill, skill])

        result = self.run_checker()

        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate canonical id 'devflow'", result.stdout)

    def test_alias_cycle_attempt_is_rejected_as_canonical_shadowing(self):
        self.write_skill("alpha")
        self.write_skill("beta")
        self.write_catalog(
            [
                self.catalog_skill("alpha", aliases=["beta"]),
                self.catalog_skill("beta", aliases=["alpha"]),
            ]
        )

        result = self.run_checker()

        self.assertEqual(result.returncode, 1)
        self.assertIn("alias 'beta' for 'alpha' shadows canonical id 'beta'", result.stdout)
        self.assertIn("alias 'alpha' for 'beta' shadows canonical id 'alpha'", result.stdout)

    def test_alias_collision_identifies_both_owners(self):
        self.write_skill("alpha")
        self.write_skill("beta")
        self.write_catalog(
            [
                self.catalog_skill("alpha", aliases=["shared"]),
                self.catalog_skill("beta", aliases=["shared"]),
            ]
        )

        result = self.run_checker()

        self.assertEqual(result.returncode, 1)
        self.assertIn("alias 'shared' is owned by both 'alpha' and 'beta'", result.stdout)

    def test_uncatalogued_skill_directory_is_identified(self):
        self.write_skill("devflow")
        self.write_skill("unlisted")
        self.write_catalog([self.catalog_skill("devflow")])

        result = self.run_checker()

        self.assertEqual(result.returncode, 1)
        self.assertIn("skills/unlisted/SKILL.md", result.stdout)
        self.assertIn("skill directory is missing from catalog", result.stdout)

    def test_nested_skill_entry_is_rejected(self):
        self.write_skill("alpha")
        nested = self.root / "skills" / "alpha" / "references" / "SKILL.md"
        nested.parent.mkdir(parents=True)
        nested.write_text("---\nname: alpha\ndescription: Shadow.\n---\n", encoding="utf-8")
        self.write_catalog([self.catalog_skill("alpha")])

        result = self.run_checker()

        self.assertEqual(result.returncode, 1)
        self.assertIn("skills/alpha/references/SKILL.md", result.stdout)
        self.assertIn("SKILL.md must sit directly in its skill directory", result.stdout)

    def test_oversized_entry_violates_line_budget(self):
        self.write_skill("alpha")
        entry = self.root / "skills" / "alpha" / "SKILL.md"
        entry.write_text("---\nname: alpha\ndescription: Big.\n---\n" + "line\n" * 311, encoding="utf-8")
        self.write_catalog([self.catalog_skill("alpha")])

        result = self.run_checker()

        self.assertEqual(result.returncode, 1)
        self.assertIn("skills/alpha/SKILL.md", result.stdout)
        self.assertIn("exceeds the 310-line entry budget", result.stdout)

    def write_template_pair(self, *, identical=True):
        self.write_skill("using-devflow")
        authoritative = (
            self.root / "skills" / "using-devflow" / "references" / "project-overrides.md"
        )
        authoritative.parent.mkdir(parents=True, exist_ok=True)
        authoritative.write_text("# Template\n\nRules here.\n", encoding="utf-8")
        mirror = self.root / "templates" / "project-overrides.md"
        mirror.parent.mkdir(parents=True, exist_ok=True)
        mirror.write_text(
            authoritative.read_text(encoding="utf-8") if identical else "# Diverged\n",
            encoding="utf-8",
        )
        self.write_catalog(
            [
                self.catalog_skill(
                    "using-devflow",
                    required_resources=[
                        "skills/using-devflow/references/project-overrides.md",
                        "templates/project-overrides.md",
                    ],
                )
            ]
        )

    def test_template_mirror_drift_is_rejected(self):
        self.write_template_pair(identical=False)

        result = self.run_checker()

        self.assertEqual(result.returncode, 1)
        self.assertIn("templates/project-overrides.md", result.stdout)
        self.assertIn("template copy is out of sync", result.stdout)

    def test_matching_template_mirror_passes(self):
        self.write_template_pair(identical=True)

        result = self.run_checker()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def write_router(self, links):
        self.write_skill("devflow")
        body = "\n".join(
            f"- [{name}](../{name}/SKILL.md)" for name in links
        )
        entry = self.root / "skills" / "devflow" / "SKILL.md"
        entry.write_text(
            f"---\nname: devflow\ndescription: Router.\n---\n\n{body}\n",
            encoding="utf-8",
        )

    def test_router_must_link_every_catalog_skill(self):
        self.write_router(["beta"])
        self.write_skill("beta")
        self.write_skill("gamma")
        self.write_catalog([self.catalog_skill("devflow"), self.catalog_skill("beta"), self.catalog_skill("gamma")])

        result = self.run_checker()

        self.assertEqual(result.returncode, 1)
        self.assertIn("gamma", result.stdout)
        self.assertIn("is not reachable from the router", result.stdout)

    def test_router_link_to_uncatalogued_skill_is_rejected(self):
        self.write_router(["beta", "ghost"])
        self.write_skill("beta")
        self.write_catalog([self.catalog_skill("devflow"), self.catalog_skill("beta")])

        result = self.run_checker()

        self.assertEqual(result.returncode, 1)
        self.assertIn("ghost", result.stdout)
        self.assertIn("router links 'ghost' which is not in the catalog", result.stdout)

    def test_malformed_catalog_is_invalid_input_without_traceback(self):
        path = self.root / "skills" / "devflow" / "references" / "skill-catalog.json"
        path.parent.mkdir(parents=True)
        path.write_text("{not json", encoding="utf-8")

        result = self.run_checker()

        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid JSON", result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_malformed_utf8_catalog_is_invalid_input_without_traceback(self):
        path = self.root / "skills" / "devflow" / "references" / "skill-catalog.json"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"\xff")

        result = self.run_checker()

        self.assertEqual(result.returncode, 2)
        self.assertIn("catalog is not valid UTF-8", result.stderr)
        self.assertIn("skills/devflow/references/skill-catalog.json", result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_unknown_catalog_field_is_invalid_input(self):
        self.write_skill("devflow")
        self.write_catalog(
            [self.catalog_skill("devflow")],
            self_hash="forbidden",
        )

        result = self.run_checker()

        self.assertEqual(result.returncode, 2)
        self.assertIn("catalog has undeclared field 'self_hash'", result.stderr)

    def test_unknown_skill_field_is_invalid_input(self):
        self.write_skill("devflow")
        skill = self.catalog_skill("devflow")
        skill["personal_path"] = "C:/Users/example"
        self.write_catalog([skill])

        result = self.run_checker()

        self.assertEqual(result.returncode, 2)
        self.assertIn("skills[0] has undeclared field 'personal_path'", result.stderr)

    def test_wrong_field_type_is_invalid_input_without_traceback(self):
        self.write_skill("devflow")
        skill = self.catalog_skill("devflow")
        skill["route_tags"] = "test"
        self.write_catalog([skill])

        result = self.run_checker()

        self.assertEqual(result.returncode, 2)
        self.assertIn("route_tags must be an array of strings", result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_repository_catalog_covers_all_33_current_skill_directories(self):
        result = subprocess.run(
            [sys.executable, str(CHECKER), "--root", str(REPOSITORY_ROOT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("BUNDLE CHECK PASSED: 33 skills", result.stdout)

    def test_using_devflow_declares_project_override_template(self):
        catalog_path = (
            REPOSITORY_ROOT
            / "skills"
            / "devflow"
            / "references"
            / "skill-catalog.json"
        )
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        using_devflow = next(
            skill for skill in catalog["skills"] if skill["id"] == "using-devflow"
        )

        self.assertIn(
            "templates/project-overrides.md",
            using_devflow["required_resources"],
        )

    def test_repository_declares_all_shared_contracts(self):
        catalog_path = (
            REPOSITORY_ROOT
            / "skills"
            / "devflow"
            / "references"
            / "skill-catalog.json"
        )
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        using_devflow = next(
            skill for skill in catalog["skills"] if skill["id"] == "using-devflow"
        )
        shared_contracts = [
            "skills/using-devflow/references/phase-contract.md",
            "skills/using-devflow/references/authorization-contract.md",
            "skills/using-devflow/references/evidence-contract.md",
            "skills/using-devflow/references/delivery-contract.md",
            "skills/using-devflow/references/host-contract.md",
            "skills/using-devflow/references/loading-recovery.md",
            "skills/using-devflow/references/project-commands.md",
            "skills/using-devflow/references/project-overrides.md",
        ]
        for resource in shared_contracts:
            self.assertIn(resource, using_devflow["required_resources"])

    def test_repository_declares_catalog_and_domain_references(self):
        catalog_path = (
            REPOSITORY_ROOT
            / "skills"
            / "devflow"
            / "references"
            / "skill-catalog.json"
        )
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        by_id = {skill["id"]: skill for skill in catalog["skills"]}
        self.assertIn(
            "skills/devflow/references/skill-catalog.json",
            by_id["devflow"]["required_resources"],
        )
        for resource in (
            "skills/documentation-and-adrs/references/user-acceptance.md",
            "skills/documentation-and-adrs/references/defect-records.md",
        ):
            self.assertIn(
                resource,
                by_id["documentation-and-adrs"]["required_resources"],
            )

    def test_repository_template_mirror_is_byte_identical(self):
        authoritative = (
            REPOSITORY_ROOT / "skills" / "using-devflow" / "references" / "project-overrides.md"
        )
        mirror = REPOSITORY_ROOT / "templates" / "project-overrides.md"
        self.assertEqual(
            authoritative.read_bytes(),
            mirror.read_bytes(),
            "templates/project-overrides.md must stay in sync with the authoritative copy",
        )


if __name__ == "__main__":
    unittest.main()
