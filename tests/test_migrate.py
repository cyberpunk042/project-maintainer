"""Regression tests for the migration runner + the reference 0001 migration."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools._paths import MIGRATIONS_DIR
from tools.migrate import applied_ids, discover, load_migration, record_applied


class TestRunnerState(unittest.TestCase):
    def test_discover_finds_reference_migration(self):
        self.assertIn("0001-ensure-final-newline", discover())

    def test_applied_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.assertEqual(applied_ids(root), set())
            record_applied(root, "0001-ensure-final-newline")
            self.assertEqual(applied_ids(root), {"0001-ensure-final-newline"})
            # idempotent record
            record_applied(root, "0001-ensure-final-newline")
            self.assertEqual(applied_ids(root), {"0001-ensure-final-newline"})


class TestReferenceMigration(unittest.TestCase):
    def _mod(self):
        return load_migration(MIGRATIONS_DIR / "0001-ensure-final-newline.py")

    def test_plan_and_apply_and_idempotent(self):
        mod = self._mod()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "a.md").write_text("# no newline", encoding="utf-8")
            (root / "b.md").write_text("# extra\n\n\n", encoding="utf-8")
            (root / "c.md").write_text("# fine\n", encoding="utf-8")

            planned = mod.plan(root)
            self.assertEqual({r[1] for r in planned}, {"a.md", "b.md"})

            mod.apply(root)
            self.assertEqual((root / "a.md").read_text(), "# no newline\n")
            self.assertEqual((root / "b.md").read_text(), "# extra\n")
            self.assertEqual((root / "c.md").read_text(), "# fine\n")

            # idempotent: second plan is empty, second apply no-op
            self.assertEqual(mod.plan(root), [])
            mod.apply(root)
            self.assertEqual((root / "a.md").read_text(), "# no newline\n")

    def test_empty_file_untouched(self):
        mod = self._mod()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "empty.md").write_text("", encoding="utf-8")
            self.assertEqual(mod.plan(root), [])


if __name__ == "__main__":
    unittest.main()
