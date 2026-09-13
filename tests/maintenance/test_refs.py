import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def find_bash():
    # Windows' System32 bash can be an unconfigured WSL launcher. Prefer
    # the Bash supplied by Git for Windows, which runs the repository checks.
    if os.name == "nt":
        git = shutil.which("git")
        if git:
            bundled_bash = Path(git).resolve().parents[1] / "bin" / "bash.exe"
            if bundled_bash.is_file():
                return str(bundled_bash)
    bash = shutil.which("bash")
    if bash:
        return bash
    raise RuntimeError("Bash is required to test scripts/check-refs.sh")


class ReferenceCheckerTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        scripts = self.root / "scripts"
        scripts.mkdir()
        for filename in ("check-refs.sh", "check-bundle.py"):
            shutil.copy2(REPOSITORY_ROOT / "scripts" / filename, scripts / filename)
        self.write("SKILL.md", "---\nname: devflow\ndescription: Root entry.\n---\n")
        self.write("skills/devflow/SKILL.md", "---\nname: devflow\ndescription: Router.\n---\n")
        self.write(
            "skills/devflow/references/skill-catalog.json",
            json.dumps({"schema_version": 1, "skills": [{
                "id": "devflow", "entry": "skills/devflow/SKILL.md",
                "route_tags": ["test"], "required_resources": [], "aliases": [],
            }]}),
        )

    def write(self, relative_path, content):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def run_checker(self):
        return subprocess.run(
            [find_bash(), "scripts/check-refs.sh"], cwd=self.root,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            check=False,
        )

    def test_nested_claude_worktree_is_outside_bundle_scan(self):
        # A host's nested checkout has its own root entry, references and
        # namespaces. None belong to the bundle being validated.
        self.write(
            ".claude/worktrees/agent-example/SKILL.md",
            "---\nname: devflow\ndescription: Nested entry.\n---\n"
            "superpowers:example\n`references/nested-missing.md`\n",
        )

        result = self.run_checker()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ALL CHECKS PASSED", result.stdout)

    def test_real_references_remain_checked_outside_host_worktree(self):
        for relative_path in (
            "README.md", "skills/devflow/references/guide.md",
            ".claude/notes.md", "docs/worktrees/guide.md",
        ):
            with self.subTest(relative_path=relative_path):
                self.write(relative_path, "`references/real-missing.md`\n")

                result = self.run_checker()

                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("BROKEN:", result.stdout)
                self.assertIn(relative_path.replace("/", os.sep), result.stdout)
                (self.root / relative_path).unlink()

    def test_real_namespace_remains_rejected(self):
        self.write("README.md", "superpowers:example\n")

        result = self.run_checker()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("README.md:1:superpowers:example", result.stdout)
        self.assertIn("FAILURES FOUND", result.stdout)


if __name__ == "__main__":
    unittest.main()
