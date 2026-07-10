"""Tests for the doctor verb — CI-command detection, classification, baseline.

Pure logic (classify / extract / derive_status) is tested hermetically; a real
red baseline is tested only when `ruff` is available locally.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.doctor import (Check, baseline, classify, derive_status,
                          extract_run_commands, preflight_advisory)


class TestClassify(unittest.TestCase):
    def test_ruff_check_is_static(self):
        self.assertEqual(classify("ruff check nnrt/ tests/").kind, "static")

    def test_ruff_format_would_modify(self):
        self.assertEqual(classify("ruff format .").kind, "modify")

    def test_black_needs_check_flag(self):
        self.assertEqual(classify("black .").kind, "modify")
        self.assertEqual(classify("black --check .").kind, "static")

    def test_pip_install_skipped(self):
        self.assertEqual(classify("pip install -e '.[dev]'").kind, "skip")

    def test_pytest_is_test(self):
        self.assertEqual(classify("pytest tests/ -v --tb=short").kind, "test")

    def test_python_m_mypy_unwrapped(self):
        c = classify("python -m mypy src/")
        self.assertEqual((c.tool, c.kind), ("mypy", "static"))

    def test_cargo_variants(self):
        self.assertEqual(classify("cargo clippy").kind, "static")
        self.assertEqual(classify("cargo fmt --check").kind, "static")
        self.assertEqual(classify("cargo fmt").kind, "modify")
        self.assertEqual(classify("cargo test").kind, "test")

    def test_unknown_command_skipped(self):
        self.assertEqual(classify("./deploy.sh --prod").kind, "skip")


class TestExtract(unittest.TestCase):
    def test_inline_and_block_run_steps(self):
        yml = (
            "jobs:\n  ci:\n    steps:\n"
            "      - run: pip install -e '.[dev]'\n"
            "      - name: lint\n        run: ruff check nnrt/ tests/\n"
            "      - run: |\n          black --check .\n          pytest tests/\n"
        )
        cmds = extract_run_commands(yml)
        self.assertIn("pip install -e '.[dev]'", cmds)
        self.assertIn("ruff check nnrt/ tests/", cmds)
        self.assertIn("black --check .", cmds)
        self.assertIn("pytest tests/", cmds)


class TestDeriveStatus(unittest.TestCase):
    def test_no_workflows(self):
        self.assertEqual(derive_status([], []), "no-ci")

    def test_unknown_when_nothing_ran(self):
        c = Check("ruff check .", "ruff", "static")     # never run
        self.assertEqual(derive_status(["wf"], [c]), "unknown")

    def test_red_on_failure(self):
        c = Check("ruff check .", "ruff", "static", ran=True, passed=False, rc=1)
        self.assertEqual(derive_status(["wf"], [c]), "red")

    def test_green_when_all_pass(self):
        c = Check("ruff check .", "ruff", "static", ran=True, passed=True, rc=0)
        self.assertEqual(derive_status(["wf"], [c]), "green")


class TestBaselineNoCI(unittest.TestCase):
    def test_target_without_ci_is_no_ci(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "README.md").write_text("hi\n", encoding="utf-8")
            result = baseline(root)
            self.assertEqual(result["status"], "no-ci")
            self.assertEqual(preflight_advisory(root), [])   # silent, no CI


@unittest.skipUnless(shutil.which("ruff"), "ruff not installed")
class TestBaselineRealRuff(unittest.TestCase):
    def _mk_project(self, root: Path, code: str) -> None:
        (root / ".github" / "workflows").mkdir(parents=True)
        (root / ".github" / "workflows" / "ci.yml").write_text(
            "jobs:\n  ci:\n    steps:\n      - run: ruff check .\n", encoding="utf-8")
        (root / "m.py").write_text(code, encoding="utf-8")

    def test_red_baseline_and_preflight_advisory(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._mk_project(root, "import os\nx=1\n")     # F401 unused import -> ruff fails
            result = baseline(root)
            self.assertEqual(result["status"], "red")
            self.assertTrue(preflight_advisory(root))       # warns

    def test_green_baseline(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._mk_project(root, "x = 1\n")               # clean
            self.assertEqual(baseline(root)["status"], "green")
            self.assertEqual(preflight_advisory(root), [])   # silent


if __name__ == "__main__":
    unittest.main()
