"""Regression tests for the clean verb — fixers, dry-run safety, --diff preview."""
from __future__ import annotations

import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools import clean


def _repo(root: Path) -> None:
    subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "t"], check=True)


def _run(argv) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        clean.main(argv)
    return buf.getvalue()


class TestClean(unittest.TestCase):
    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _repo(root)
            (root / "docs").mkdir()
            f = root / "docs" / "x.md"
            f.write_text("trailing \nok\n", encoding="utf-8")  # single trailing space
            out = _run(["--target", str(root)])
            self.assertIn("WOULD strip trailing-ws", out)
            self.assertEqual(f.read_text(), "trailing \nok\n")  # untouched

    def test_apply_writes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _repo(root)
            (root / "docs").mkdir()
            f = root / "docs" / "x.md"
            f.write_text("trailing \nok\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "seed"], check=True, capture_output=True)
            _run(["--target", str(root), "--apply"])
            self.assertEqual(f.read_text(), "trailing\nok\n")

    def test_diff_preview(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _repo(root)
            (root / "docs").mkdir()
            (root / "docs" / "x.md").write_text("trailing \nok\n", encoding="utf-8")
            out = _run(["--target", str(root), "--diff"])
            self.assertIn("--- a/docs/x.md", out)
            self.assertIn("+++ b/docs/x.md", out)
            self.assertIn("-trailing", out)

    def test_preserves_markdown_hard_break(self):
        # content line ending in >=2 spaces is a CommonMark hard break (<br>);
        # it must survive the cleaner. A whitespace-only line is still stripped.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _repo(root)
            (root / "docs").mkdir()
            f = root / "docs" / "x.md"
            f.write_text("line one  \nline two\n   \nend\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "seed"], check=True, capture_output=True)
            _run(["--target", str(root), "--apply"])
            # hard break "line one  " preserved; blank "   " collapsed to ""
            self.assertEqual(f.read_text(), "line one  \nline two\n\nend\n")

    def test_junk_deletion(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _repo(root)
            (root / "docs").mkdir()
            junk = root / "docs" / ".DS_Store"
            junk.write_text("x", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "-A", "-f"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "seed"], check=True, capture_output=True)
            _run(["--target", str(root), "--apply"])
            self.assertFalse(junk.exists())


if __name__ == "__main__":
    unittest.main()
