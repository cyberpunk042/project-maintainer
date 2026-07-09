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


class _Entry:
    """Minimal stand-in for a registry Project (only the fields implant reads)."""
    def __init__(self, name="fx", backlog_root="", log_root=""):
        self.name, self.backlog_root, self.log_root = name, backlog_root, log_root


class TestStructureAdvisory(unittest.TestCase):
    def test_warns_when_default_path_would_duplicate_root_backlog(self):
        # no backlog_root configured -> default wiki/backlog would be created
        # alongside the target's populated root backlog/.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _repo(root)
            (root / "backlog").mkdir()
            (root / "backlog" / "INDEX.md").write_text("x", encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                implant.main(["--target", str(root)])       # dry-run, no entry
            out = buf.getvalue()
            self.assertIn("ADVISORY", out)
            self.assertIn("'wiki/backlog/' does not exist", out)
            self.assertIn("backlog_root", out)

    def test_no_advisory_when_backlog_root_points_at_existing(self):
        # once the registry declares backlog_root: backlog, the existing dir is
        # reused and there is nothing to duplicate.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "backlog").mkdir()
            (root / "backlog" / "INDEX.md").write_text("x", encoding="utf-8")
            entry = _Entry(backlog_root="backlog", log_root="docs/log")
            (root / "docs" / "log").mkdir(parents=True)
            self.assertEqual(implant.structure_advisories(entry, root), [])


class TestLayoutAware(unittest.TestCase):
    def test_implant_uses_configured_backlog_and_log_roots(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _repo(root)
            entry = _Entry(name="rusty", backlog_root="backlog", log_root="docs/directives")
            dirs = implant.build_dirs(entry)
            self.assertIn("docs/directives", dirs)
            self.assertIn("backlog/epics", dirs)
            self.assertNotIn("wiki/log", dirs)
            # stamped content points at the real paths, not wiki/*
            man = implant.build_manifest(entry)
            self.assertEqual(man["backlog/task.md"], "backlog/tasks/_template.md")
            claude = implant.substitute(
                (implant.TEMPLATES_DIR / "brain/CLAUDE.project.md").read_text(), "rusty", entry
            )
            self.assertIn("backlog/", claude)
            self.assertIn("docs/directives/", claude)
            self.assertNotIn("wiki/backlog", claude)
            self.assertNotIn("wiki/log", claude)

    def test_default_layout_unchanged_for_wiki_projects(self):
        # a target with no path config keeps the ecosystem default wiki/ layout.
        self.assertEqual(implant.backlog_root(None), "wiki/backlog")
        self.assertEqual(implant.log_root(None), "wiki/log")
        self.assertEqual(implant.build_manifest(None)["backlog/epic.md"],
                         "wiki/backlog/epics/_template.md")


class TestProposeIdempotency(unittest.TestCase):
    """The .proposed conflict path must be idempotent AND never clobber an
    operator's in-progress .proposed (routing contract + Hard Rule 8)."""

    def _seed_conflict(self, root: Path) -> Path:
        """Implant, then drift CLAUDE.md so the next implant proposes a sibling."""
        _run(implant, ["--target", str(root), "--apply"])
        (root / "CLAUDE.md").write_text("locally edited\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "drift"], check=True, capture_output=True)
        _run(implant, ["--target", str(root), "--apply"])   # creates .proposed
        return root / "CLAUDE.md.proposed"

    def test_reproposing_identical_is_noop(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _repo(root)
            proposed = self._seed_conflict(root)
            self.assertTrue(proposed.exists())
            first = proposed.read_text()
            subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "proposed"], check=True, capture_output=True)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                implant.main(["--target", str(root), "--apply"])
            out = buf.getvalue()
            self.assertIn("already proposed (identical)", out)
            self.assertIn("0 change(s) applied", out)
            self.assertEqual(proposed.read_text(), first)      # unchanged

    def test_does_not_clobber_operator_edited_proposed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _repo(root)
            proposed = self._seed_conflict(root)
            # operator starts merging the .proposed
            proposed.write_text("MY MERGE IN PROGRESS\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "merge"], check=True, capture_output=True)
            _run(implant, ["--target", str(root), "--apply"])
            # re-running must NOT overwrite the operator's work
            self.assertEqual(proposed.read_text(), "MY MERGE IN PROGRESS\n")


class TestScaffold(unittest.TestCase):
    def test_scaffold_task_stamps(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _repo(root)
            _run(scaffold, ["backlog/task", "--name", "T001-demo", "--target", str(root), "--apply"])
            self.assertTrue((root / "wiki/backlog/tasks/T001-demo.md").is_file())

    def test_scaffold_conflict_proposes_then_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _repo(root)
            args = ["backlog/task", "--name", "T001-demo", "--target", str(root), "--apply"]

            def commit(msg):
                subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
                subprocess.run(["git", "-C", str(root), "commit", "-qm", msg], check=True, capture_output=True)

            _run(scaffold, args)
            commit("scaffold")
            _run(scaffold, args)                                # dest exists -> propose
            proposed = root / "wiki/backlog/tasks/T001-demo.md.proposed"
            self.assertTrue(proposed.exists())
            body = proposed.read_text()
            commit("proposed")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                scaffold.main(args)                             # .proposed identical -> noop
            self.assertIn("0 change(s) applied", buf.getvalue())
            self.assertEqual(proposed.read_text(), body)


if __name__ == "__main__":
    unittest.main()
