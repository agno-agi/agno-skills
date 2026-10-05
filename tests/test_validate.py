"""Regression fixtures for the offline documentation validator."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validate import validate


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skill = self.root / "plugins/demo/skills/demo/SKILL.md"
        self.reference = self.skill.parent / "references/start.md"
        self.manifest = self.root / "plugins/demo/.claude-plugin/plugin.json"
        self.marketplace = self.root / ".claude-plugin/marketplace.json"
        self.skill_text = "---\nname: demo\ndescription: Build a demo.\n---\n[Start](references/start.md#setup)\n"
        self.entry = {"name": "demo", "version": "1.1.0", "source": "./plugins/demo"}
        self.write(self.skill, self.skill_text)
        self.write(self.reference, "# Setup\n\n```python\nvalue = 1\n```\n")
        self.write(self.manifest, json.dumps({"name": "demo", "version": "1.1.0"}))
        self.write(
            self.marketplace,
            json.dumps({"name": "demo-skills", "plugins": [self.entry]}),
        )

    def write(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def assert_invalid(self, message):
        self.assertTrue(
            any(message in error for error in validate(self.root)), validate(self.root)
        )

    def test_clean_fixture(self):
        self.assertEqual(validate(self.root), [])

    def test_frontmatter_failures(self):
        replacements = [
            ("name: demo", "name: Other"),
            ("name: demo", "name: other"),
            ("name: demo", "name: a--b"),
            ("name: demo", "name: " + "a" * 65),
            ("description: Build a demo.", "description: 42"),
            ("description: Build a demo.", 'description: " "'),
            ("description: Build a demo.", "description: " + "x" * 1025),
            ("name: demo", "name: [broken"),
            (
                "---\n",
                "",
            ),
        ]
        for old, new in replacements:
            with self.subTest(new=new[:40]):
                self.skill.write_text(self.skill_text.replace(old, new, 1))
                self.assert_invalid("frontmatter")

    def test_missing_anchor_target_and_escape(self):
        for link, message in [
            ("absent.md", "missing link target"),
            (
                "plugins/demo/skills/demo/references/start.md#absent",
                "missing heading anchor",
            ),
            ("../outside.md", "link escapes repository"),
        ]:
            with self.subTest(link=link):
                self.write(self.root / "README.md", f"[Link]({link})")
                self.assert_invalid(message)

    def test_link_syntax_and_masked_code(self):
        self.write(self.root / "a (b).md", "# Repeated\n# Repeated\n")
        self.write(
            self.root / "README.md",
            "[A](a%20(b).md#repeated-1)\n[B][ref]\n[ref]: <a (b).md>\n"
            "`[ignored](absent.md)`\n~~~~text\n[ignored](absent.md)\n~~~~\n",
        )
        self.assertEqual(validate(self.root), [])

    def test_orphan_reference(self):
        self.write(self.reference.parent / "orphan.md", "# Unlinked")
        self.assert_invalid("orphan reference")

    def test_missing_skill_directory(self):
        shutil.rmtree(self.skill.parent.parent)
        self.assert_invalid("at least one SKILL.md")

    def test_unclosed_code_fence(self):
        self.write(self.reference, "# Setup\n```python\nvalue = 1\n")
        self.assert_invalid("unclosed code fence")

    def test_invalid_python_and_top_level_await(self):
        for code in ["if :", "await operation()"]:
            with self.subTest(code=code):
                self.write(self.reference, f"# Setup\n```python\n{code}\n```\n")
                self.assert_invalid("invalid Python")

    def test_obsolete_examples_not_prose_or_comments(self):
        for code in [
            "from agno.tools.mcp import MultiMCPTools",
            "from agno.models.openai import OpenAIChat",
            "from agno.tools.mcp import MCPToolbox",
            'model = "gpt-4o-mini"',
        ]:
            with self.subTest(code=code):
                self.write(self.reference, f"# Setup\n```python\n{code}\n```\n")
                self.assertTrue(validate(self.root))
        self.write(
            self.reference,
            "# Setup\nHistorical OpenAIChat and gpt-4o.\n```python\n# MultiMCPTools\n```\n",
        )
        self.assertEqual(validate(self.root), [])

    def test_manifest_failures(self):
        for content in ["{", "[]", json.dumps({"name": "demo", "version": "2.0.0"})]:
            with self.subTest(content=content):
                self.write(self.manifest, content)
                self.assert_invalid("manifest")

    def test_marketplace_source_and_duplicates(self):
        for entries in [
            [{**self.entry, "source": "../outside"}],
            [self.entry, self.entry],
            [None],
        ]:
            with self.subTest(entries=entries):
                self.write(
                    self.marketplace,
                    json.dumps({"name": "demo-skills", "plugins": entries}),
                )
                self.assert_invalid("manifest")

    def test_symlink_escape(self):
        with tempfile.TemporaryDirectory() as outside:
            other = Path(outside) / "outside.md"
            other.write_text("# Outside")
            self.reference.unlink()
            self.reference.symlink_to(other)
            self.assert_invalid("escapes repository")


if __name__ == "__main__":
    unittest.main()
