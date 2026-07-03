"""Regression tests for the fix verb — conservative link repair."""
from __future__ import annotations

import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools import fix
from tools._mutate import ChangeReport
from tools.registry import Project


def _repo(root: Path) -> None:
    subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "t"], check=True)


def _run(argv) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fix.main(argv)
    return buf.getvalue()


class TestFixLinks(unittest.TestCase):
    def test_unique_match_repaired(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _repo(root)
            (root / "docs" / "sub").mkdir(parents=True)
            (root / "docs" / "a.md").write_text("[x](./moved.md)\n", encoding="utf-8")
            (root / "docs" / "sub" / "moved.md").write_text("hi\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "s"], check=True, capture_output=True)
            _run(["--target", str(root), "--apply"])
            self.assertEqual((root / "docs" / "a.md").read_text(), "[x](sub/moved.md)\n")

    def test_ambiguous_not_touched(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _repo(root)
            (root / "docs" / "one").mkdir(parents=True)
            (root / "docs" / "two").mkdir(parents=True)
            (root / "docs" / "a.md").write_text("[x](./dup.md)\n", encoding="utf-8")
            (root / "docs" / "one" / "dup.md").write_text("1\n", encoding="utf-8")
            (root / "docs" / "two" / "dup.md").write_text("2\n", encoding="utf-8")
            out = _run(["--target", str(root)])
            self.assertIn("not auto-fixable", out)
            self.assertIn("2 candidate(s)", out)
            self.assertEqual((root / "docs" / "a.md").read_text(), "[x](./dup.md)\n")

    def test_missing_file_reported_not_guessed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _repo(root)
            (root / "docs").mkdir()
            (root / "docs" / "a.md").write_text("[x](./gone.md)\n", encoding="utf-8")
            out = _run(["--target", str(root)])
            self.assertIn("0 candidate(s)", out)

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _repo(root)
            (root / "docs" / "sub").mkdir(parents=True)
            (root / "docs" / "a.md").write_text("[x](./moved.md)\n", encoding="utf-8")
            (root / "docs" / "sub" / "moved.md").write_text("hi\n", encoding="utf-8")
            out = _run(["--target", str(root), "--diff"])
            self.assertIn("fix link", out)
            self.assertEqual((root / "docs" / "a.md").read_text(), "[x](./moved.md)\n")


class TestFixWikilinks(unittest.TestCase):
    def _vault(self, root: Path) -> None:
        _repo(root)
        (root / "epics").mkdir()
        (root / "lessons" / "02_synth").mkdir(parents=True)
        (root / "lessons" / "02_synth" / "moved-note.md").write_text("hi\n", encoding="utf-8")

    def test_moved_note_becomes_wikilink(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._vault(root)
            f = root / "epics" / "e.md"
            f.write_text("see [Nice Lesson](../lessons/01_drafts/moved-note.md) here\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "s"], check=True, capture_output=True)
            _run(["--target", str(root), "--fixers", "wikilinks", "--apply"])
            self.assertEqual(f.read_text(), "see [[moved-note|Nice Lesson]] here\n")

    def test_display_equals_stem_bare_wikilink(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._vault(root)
            f = root / "epics" / "e.md"
            f.write_text("[moved-note](../old/moved-note.md)\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "s"], check=True, capture_output=True)
            _run(["--target", str(root), "--fixers", "wikilinks", "--apply"])
            self.assertEqual(f.read_text(), "[[moved-note]]\n")

    def test_anchor_link_not_corrupted(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._vault(root)
            f = root / "epics" / "e.md"
            original = "[x](../old/moved-note.md#some-section)\n"
            f.write_text(original, encoding="utf-8")
            out = _run(["--target", str(root), "--fixers", "wikilinks"])
            self.assertIn("anchor/query", out)
            self.assertEqual(f.read_text(), original)  # untouched

    def test_working_link_untouched(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._vault(root)
            f = root / "epics" / "e.md"
            (root / "epics" / "sibling.md").write_text("s\n", encoding="utf-8")
            original = "[ok](./sibling.md)\n"
            f.write_text(original, encoding="utf-8")
            _run(["--target", str(root), "--fixers", "wikilinks"])
            self.assertEqual(f.read_text(), original)

    def test_ambiguous_note_not_converted(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._vault(root)
            (root / "lessons" / "01_drafts").mkdir(parents=True)
            (root / "lessons" / "01_drafts" / "moved-note.md").write_text("dup\n", encoding="utf-8")
            f = root / "epics" / "e.md"
            f.write_text("[x](../gone/moved-note.md)\n", encoding="utf-8")
            out = _run(["--target", str(root), "--fixers", "wikilinks"])
            self.assertIn("not convertible", out)

    def test_md_stripped_from_display(self):
        # display carrying a .md extension must not leak into the alias.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._vault(root)
            f = root / "epics" / "e.md"
            f.write_text("[moved-note.md](../old/moved-note.md) and [Cool Title.md](../x/moved-note.md)\n",
                         encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "s"], check=True, capture_output=True)
            _run(["--target", str(root), "--fixers", "wikilinks", "--apply"])
            self.assertEqual(f.read_text(), "[[moved-note]] and [[moved-note|Cool Title]]\n")

    def test_path_display_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._vault(root)
            f = root / "epics" / "e.md"
            original = "[docs/moved-note.md](../old/moved-note.md)\n"
            f.write_text(original, encoding="utf-8")
            out = _run(["--target", str(root), "--fixers", "wikilinks"])
            self.assertIn("display is a path", out)
            self.assertEqual(f.read_text(), original)

    def test_template_config_asset_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _repo(root)
            (root / "epics").mkdir()
            (root / "config" / "templates").mkdir(parents=True)
            (root / "config" / "templates" / "decision.md").write_text("t\n", encoding="utf-8")
            f = root / "epics" / "e.md"
            original = "[decision.md](../old/decision.md)\n"  # broken; unique note under config/templates
            f.write_text(original, encoding="utf-8")
            out = _run(["--target", str(root), "--fixers", "wikilinks"])
            self.assertIn("template/config asset", out)
            self.assertEqual(f.read_text(), original)

    def test_target_outside_vault_skipped(self):
        # linking file under wiki/, target resolves into repo-root docs/ (outside vault)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _repo(root)
            (root / "wiki" / "spine").mkdir(parents=True)
            (root / "docs").mkdir()
            (root / "docs" / "handoff.md").write_text("h\n", encoding="utf-8")
            f = root / "wiki" / "spine" / "std.md"
            original = "[handoff](./handoff.md)\n"  # broken here; unique note lives in docs/ (outside vault)
            f.write_text(original, encoding="utf-8")
            entry = Project(name="fixture", path=str(root), docs=["wiki"], wiki="wiki")
            report = ChangeReport(apply=False)
            fix.fix_wikilinks(root, entry, report, False)
            self.assertTrue(any("outside vault" in s for s in report.skips))


if __name__ == "__main__":
    unittest.main()
