"""Regression tests for the mutation guard + clean fixers — the safety layer.

These are the invariants a real cleanup depends on: dry-run default, dirty-target
refusal, writable gating, idempotency. Stdlib unittest.
"""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tools._mutate import ChangeReport, git_dirty, guard
from tools.registry import Project


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True,
                   capture_output=True, text=True)


def _init_repo(root: Path) -> None:
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@t")
    _git(root, "config", "user.name", "t")


class TestGuard(unittest.TestCase):
    def test_non_writable_blocks(self):
        entry = Project(name="second-brain", writable=False)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit):
                guard(Path(d), entry, apply=True, allow_dirty=False)

    def test_dry_run_never_blocks(self):
        # apply=False must be a no-op even against a dirty repo.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _init_repo(root)
            (root / "x.txt").write_text("dirty", encoding="utf-8")
            guard(root, None, apply=False, allow_dirty=False)  # must not raise

    def test_dirty_target_refused_on_apply(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _init_repo(root)
            (root / "x.txt").write_text("dirty", encoding="utf-8")
            self.assertTrue(git_dirty(root))
            with self.assertRaises(SystemExit):
                guard(root, None, apply=True, allow_dirty=False)

    def test_clean_target_allows_apply(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _init_repo(root)
            (root / "x.txt").write_text("committed", encoding="utf-8")
            _git(root, "add", "-A")
            _git(root, "commit", "-qm", "init")
            self.assertFalse(git_dirty(root))
            guard(root, None, apply=True, allow_dirty=False)  # must not raise

    def test_allow_dirty_override(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _init_repo(root)
            (root / "x.txt").write_text("dirty", encoding="utf-8")
            guard(root, None, apply=True, allow_dirty=True)  # must not raise


class TestChangeReport(unittest.TestCase):
    def test_dry_run_says_would(self):
        r = ChangeReport(apply=False)
        r.act("delete", "a.txt")
        self.assertTrue(r.actions[0].strip().startswith("WOULD delete"))

    def test_apply_says_did(self):
        r = ChangeReport(apply=True)
        r.act("delete", "a.txt")
        self.assertTrue(r.actions[0].strip().startswith("DID delete"))


if __name__ == "__main__":
    unittest.main()
