"""Regression tests for the fix verb — conservative link repair."""
from __future__ import annotations

import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools import fix


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


if __name__ == "__main__":
    unittest.main()
