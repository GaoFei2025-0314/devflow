import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


CHECKER = Path(__file__).resolve().parents[2] / "scripts" / "check-version.py"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
VERSION_PATTERN = r"^\d+\.\d+\.\d+$"
HEADING_PATTERN = (
    r"^## (\d+\.\d+\.\d+)(?: \((\d{4}-\d{2}-\d{2})[^)]*\))?\s*$"
)
GIT = shutil.which("git")


def run_checker(*arguments):
    return subprocess.run(
        [sys.executable, str(CHECKER), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


class ConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)

    def write_bundle(self, *, version="1.2.3", changelog=None, marketplace=None, plugin=None):
        plugin_directory = self.root / ".claude-plugin"
        plugin_directory.mkdir(parents=True, exist_ok=True)
        if plugin is None:
            plugin = {"name": "demo", "version": version}
        (plugin_directory / "plugin.json").write_text(
            json.dumps(plugin), encoding="utf-8",
        )
        if marketplace is None:
            marketplace = {
                "name": "demo",
                "plugins": [{"name": "demo", "source": "./", "version": version}],
            }
        (plugin_directory / "marketplace.json").write_text(
            json.dumps(marketplace), encoding="utf-8",
        )
        if changelog is None:
            changelog = (
                "# Changelog\n\n"
                f"## {version} (2026-11-14)\n\n"
                "- note\n\n"
                "## 1.2.0 (2026-10-09 tag)\n\n"
                "## 1.0.2 (2026-09-30 tag, limited acceptance)\n\n"
                "## 1.0.0\n"
            )
        (self.root / "CHANGELOG.md").write_text(changelog, encoding="utf-8")

    def check(self, *arguments):
        return run_checker("consistency", "--root", str(self.root), *arguments)

    def test_consistent_versions_pass(self):
        self.write_bundle()

        result = self.check("--tag", "v1.2.3")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("VERSION CHECK PASSED: 1.2.3", result.stdout)

    def test_marketplace_without_version_passes(self):
        self.write_bundle(marketplace={
            "name": "demo",
            "plugins": [{"name": "demo", "source": "./"}],
        })

        result = self.check()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_crlf_changelog_passes(self):
        self.write_bundle()
        changelog = self.root / "CHANGELOG.md"
        changelog.write_bytes(changelog.read_bytes().replace(b"\n", b"\r\n"))

        result = self.check()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_plugin_and_changelog_mismatch_fails(self):
        self.write_bundle(changelog="## 1.2.2 (2026-11-14)\n\n## 1.0.0\n")

        result = self.check()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("1.2.2", result.stdout)
        self.assertIn("1.2.3", result.stdout)
        self.assertIn("CHANGELOG.md", result.stdout)

    def test_top_heading_requires_a_date(self):
        self.write_bundle(changelog="## 1.2.3\n\n## 1.0.0\n")

        result = self.check()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(HEADING_PATTERN, result.stdout)
        self.assertIn("date", result.stdout.lower())

    def test_invalid_calendar_date_fails(self):
        self.write_bundle(changelog="## 1.2.3 (2026-13-40)\n\n## 1.0.0\n")

        result = self.check()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("2026-13-40", result.stdout)
        self.assertIn("calendar", result.stdout.lower())

    def test_versions_must_strictly_decrease(self):
        self.write_bundle(
            changelog="## 1.2.3 (2026-11-14)\n\n## 1.2.4 (2026-01-01)\n",
        )

        result = self.check()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("strictly decreasing", result.stdout)
        self.assertIn("1.2.4", result.stdout)

    def test_duplicate_versions_fail(self):
        self.write_bundle(changelog="## 1.2.3 (2026-11-14)\n\n## 1.2.3\n")

        result = self.check()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("strictly decreasing", result.stdout)
        self.assertIn("duplicate", result.stdout)

    def test_non_semver_names_expected_pattern(self):
        self.write_bundle(version="1.2.3-rc1", changelog="## 1.0.0 (2026-11-14)\n")

        result = self.check()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(VERSION_PATTERN, result.stdout)
        self.assertIn("1.2.3-rc1", result.stdout)

    def test_marketplace_version_must_match_plugin(self):
        self.write_bundle(marketplace={
            "name": "demo",
            "plugins": [{"name": "demo", "source": "./", "version": "9.9.9"}],
        })

        result = self.check()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("marketplace.json", result.stdout)
        self.assertIn("9.9.9", result.stdout)
        self.assertIn("1.2.3", result.stdout)

    def test_tag_must_equal_v_plus_version(self):
        self.write_bundle()

        result = self.check("--tag", "v9.9.9")

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("v1.2.3", result.stdout)
        self.assertIn("v9.9.9", result.stdout)

    def test_nonmatching_heading_names_expected_pattern(self):
        self.write_bundle(changelog="## 1.2.3 (2026-11-14)\n\n## soon\n")

        result = self.check()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(HEADING_PATTERN, result.stdout)

    def test_invalid_plugin_json_is_input_error(self):
        self.write_bundle()
        (self.root / ".claude-plugin" / "plugin.json").write_text("{", encoding="utf-8")

        result = self.check()

        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("INPUT ERROR", result.stderr)

    def test_missing_root_is_input_error(self):
        result = run_checker("consistency", "--root", str(self.root / "missing"))

        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("INPUT ERROR", result.stderr)


class RepositoryConsistencyTests(unittest.TestCase):
    def test_repository_root_passes(self):
        result = run_checker("consistency", "--root", str(REPOSITORY_ROOT))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("VERSION CHECK PASSED", result.stdout)


@unittest.skipUnless(GIT, "git is required to test bump checks")
class VersionBumpTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.git_init()
        self.base = self.seed()

    def git(self, *arguments, check=True):
        result = subprocess.run(
            [GIT, *arguments],
            cwd=self.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if check and result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        return result

    def git_init(self):
        result = self.git("init", "-b", "main", check=False)
        if result.returncode != 0:
            self.git("init")
            self.git("symbolic-ref", "HEAD", "refs/heads/main")
        self.git("config", "user.email", "devflow-test@example.com")
        self.git("config", "user.name", "Devflow Test")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.autocrlf", "false")

    def write(self, relative_path, content):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def write_plugin(self, version):
        self.write(
            ".claude-plugin/plugin.json",
            json.dumps({"name": "demo", "version": version}) + "\n",
        )

    def write_changelog(self, content):
        self.write("CHANGELOG.md", content)

    def seed(self):
        self.write_plugin("1.0.0")
        self.write(
            ".claude-plugin/marketplace.json",
            json.dumps({"name": "demo", "plugins": [{"name": "demo", "source": "./"}]}) + "\n",
        )
        self.write_changelog("## 1.0.0 (2026-01-15)\n\n- initial\n")
        self.write("skills/example/SKILL.md", "# example\n")
        self.write("SKILL.md", "# root\n")
        self.write("AGENTS.md", "# agents\n")
        self.write("templates/note.md", "# template\n")
        self.write("README.md", "# readme\n")
        return self.commit("seed")

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-m", message)
        return self.git("rev-parse", "HEAD").stdout.strip()

    def reset(self):
        self.git("reset", "--hard", self.base)
        self.git("clean", "-fd")

    def bump(self, base_ref=None):
        return run_checker(
            "bump",
            "--base-ref",
            self.base if base_ref is None else base_ref,
            "--root",
            str(self.root),
        )

    def test_no_trigger_changes_pass(self):
        result = self.bump()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("version bump not required", result.stdout)

    def test_unrelated_change_does_not_require_a_bump(self):
        self.reset()
        self.write("docs-note.md", "note\n")
        self.commit("docs only")

        result = self.bump()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("version bump not required", result.stdout)

    def test_each_trigger_path_requires_a_bump(self):
        paths = (
            "skills/example/SKILL.md",
            "SKILL.md",
            "AGENTS.md",
            "templates/note.md",
        )
        for relative_path in paths:
            with self.subTest(relative_path=relative_path):
                self.reset()
                path = self.root / relative_path
                path.write_text(
                    path.read_text(encoding="utf-8") + "\n<!-- touch -->\n",
                    encoding="utf-8",
                )
                self.commit("touch trigger path")

                result = self.bump()

                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("still 1.0.0", result.stdout)
                self.assertIn(VERSION_PATTERN, result.stdout)

    def test_version_bump_without_changelog_fails(self):
        self.reset()
        self.write_plugin("1.1.0")
        self.write("skills/example/SKILL.md", "# example\n\n<!-- touch -->\n")
        self.commit("bump without changelog")

        result = self.bump()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("CHANGELOG.md", result.stdout)
        self.assertIn(HEADING_PATTERN, result.stdout)
        self.assertIn("1.1.0", result.stdout)

    def test_changelog_change_without_new_heading_fails(self):
        self.reset()
        self.write_plugin("1.1.0")
        self.write_changelog("## 1.0.0 (2026-01-15)\n\n- edited without a new heading\n")
        self.write("skills/example/SKILL.md", "# example\n\n<!-- touch -->\n")
        self.commit("changelog without new heading")

        result = self.bump()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("does not include a heading", result.stdout)
        self.assertIn(HEADING_PATTERN, result.stdout)
        self.assertIn("1.1.0", result.stdout)

    def test_downgrade_fails(self):
        self.reset()
        self.write_plugin("0.9.0")
        self.write_changelog("## 0.9.0 (2026-11-14)\n\n## 1.0.0 (2026-01-15)\n")
        self.write("skills/example/SKILL.md", "# example\n\n<!-- touch -->\n")
        self.commit("downgrade")

        result = self.bump()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("not strictly greater", result.stdout)
        self.assertIn("0.9.0", result.stdout)
        self.assertIn("1.0.0", result.stdout)
        self.assertIn(VERSION_PATTERN, result.stdout)

    def test_correct_bump_passes(self):
        self.reset()
        self.write_plugin("1.1.0")
        self.write_changelog(
            "## 1.1.0 (2026-11-14)\n\n- note\n\n## 1.0.0 (2026-01-15)\n",
        )
        self.write("skills/example/SKILL.md", "# example\n\n<!-- touch -->\n")
        self.commit("correct bump")

        result = self.bump()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("1.0.0 -> 1.1.0", result.stdout)

    def test_unknown_base_ref_is_input_error(self):
        result = self.bump("does-not-exist")

        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("INPUT ERROR", result.stderr)


if __name__ == "__main__":
    unittest.main()
