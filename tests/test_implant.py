"""Smoke tests for implant/upgrade/scaffold — additive stamping, idempotency.

Uses the real templates/ but a throwaway git target. Stdlib unittest.
"""
from __future__ import annotations

import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools import implant, scaffold, upgrade
from tools._paths import TEMPLATES_DIR


def _repo(root: Path) -> None:
    subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "t"], check=True)
    (root / "seed").write_text("x", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "init"], check=True, capture_output=True)


def _run(mod, argv) -> int:
    with contextlib.redirect_stdout(io.StringIO()):
        return mod.main(argv)


class TestManifest(unittest.TestCase):
    def test_manifest_templates_exist(self):
        for src in implant.MANIFEST:
            self.assertTrue((TEMPLATES_DIR / src).is_file(), f"missing template {src}")

    def test_substitute(self):
        self.assertEqual(implant.substitute("hi {{PROJECT}}", "acme"), "hi acme")


class TestImplantFunctional(unittest.TestCase):
    def test_implant_stamps_then_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _repo(root)
            _run(implant, ["--target", str(root), "--apply"])
            claude = root / "CLAUDE.md"
            self.assertTrue(claude.is_file())
            body = claude.read_text()
            # commit so the tree is clean for a second run
            subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "implant"], check=True, capture_output=True)
            _run(implant, ["--target", str(root), "--apply"])
            # identical content -> skipped, no .proposed sibling created
            self.assertFalse((root / "CLAUDE.md.proposed").exists())
            self.assertEqual(claude.read_text(), body)

    def test_upgrade_proposes_on_drift(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _repo(root)
            _run(implant, ["--target", str(root), "--apply"])
            # drift a stamped file
            (root / "CLAUDE.md").write_text("locally edited\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "drift"], check=True, capture_output=True)
            _run(upgrade, ["--target", str(root), "--apply"])
            # additive: never overwrites; proposes a sibling
            self.assertTrue((root / "CLAUDE.md.proposed").exists())
            self.assertEqual((root / "CLAUDE.md").read_text(), "locally edited\n")


class TestScaffold(unittest.TestCase):
    def test_scaffold_task_stamps(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _repo(root)
            _run(scaffold, ["backlog/task", "--name", "T001-demo", "--target", str(root), "--apply"])
            self.assertTrue((root / "wiki/backlog/tasks/T001-demo.md").is_file())


if __name__ == "__main__":
    unittest.main()
