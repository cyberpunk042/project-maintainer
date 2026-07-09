"""Regression tests for audit checks — precision matters before a real cleanup.

Builds throwaway fixture trees in a temp dir (no dependency on sibling repos
except an explicitly-injected siblings set). Stdlib unittest.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.audit import _frontmatter_exempt, audit_target
from tools.registry import Project


def _mk(root: Path, rel: str, content: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _checks(findings, check):
    return [f for f in findings if f.check == check]


class TestFrontmatterExempt(unittest.TestCase):
    def test_nav_files_exempt(self):
        self.assertTrue(_frontmatter_exempt("wiki/_index.md", "_index.md", []))
        self.assertTrue(_frontmatter_exempt("wiki/README.md", "README.md", []))
        self.assertTrue(_frontmatter_exempt("wiki/index.md", "index.md", []))

    def test_log_dirs_exempt(self):
        self.assertTrue(_frontmatter_exempt("wiki/log/2026-05-05-handoff.md", "2026-05-05-handoff.md", []))
        self.assertTrue(_frontmatter_exempt("wiki/logs/x.md", "x.md", []))

    def test_regular_page_not_exempt(self):
        self.assertFalse(_frontmatter_exempt("wiki/concepts/foo.md", "foo.md", []))

    def test_configurable_extra(self):
        self.assertTrue(_frontmatter_exempt("wiki/drafts/x.md", "x.md", ["drafts/"]))
        self.assertFalse(_frontmatter_exempt("wiki/drafts/x.md", "x.md", ["snapshots/"]))


class TestAuditFixture(unittest.TestCase):
    def _audit(self, root: Path, wiki="wiki", siblings=None, checks=None):
        entry = Project(name="fixture", path=str(root), docs=["wiki"], wiki=wiki)
        return audit_target(root, entry, checks=checks, siblings=siblings or set())

    def test_broken_link_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _mk(root, "wiki/a.md", "---\nt: x\n---\n[b](./missing.md)\n")
            findings = self._audit(root)
            self.assertEqual(len(_checks(findings, "broken-link")), 1)

    def test_valid_link_not_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _mk(root, "wiki/a.md", "---\nt: x\n---\n[b](./b.md)\n")
            _mk(root, "wiki/b.md", "---\nt: y\n---\nhi\n")
            self.assertEqual(_checks(self._audit(root), "broken-link"), [])

    def test_cross_repo_not_broken(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _mk(root, "wiki/a.md", "---\nt: x\n---\n[b](../selfdef/backlog/x.md)\n")
            # broken-link default: cross-repo link must NOT be flagged broken
            self.assertEqual(_checks(self._audit(root, siblings={"selfdef"}), "broken-link"), [])
            # opt-in cross-repo check: it IS surfaced separately
            cr = self._audit(root, siblings={"selfdef"}, checks={"cross-repo"})
            self.assertEqual(len(_checks(cr, "cross-repo")), 1)

    def test_frontmatter_flagged_and_exempted(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _mk(root, "wiki/concepts/page.md", "no frontmatter here\n")   # flagged
            _mk(root, "wiki/log/handoff.md", "chronological, no fm\n")     # exempt (log dir)
            _mk(root, "wiki/_index.md", "nav, no fm\n")                    # exempt (nav)
            fm = _checks(self._audit(root), "frontmatter")
            self.assertEqual([f.path for f in fm], ["wiki/concepts/page.md"])

    def test_link_inside_code_not_broken(self):
        # a markdown link written INSIDE a code fence or inline code span is a
        # syntax example, not a navigable link — it must not be flagged broken.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _mk(root, "wiki/a.md",
                "---\nt: x\n---\n"
                "Real broken: [x](./missing.md)\n"          # 1 genuine
                "Inline example: `[y](path/to/file.md)`\n"  # not a link
                "```\n[z](also/missing.md)\n```\n")          # not a link
            broken = _checks(self._audit(root), "broken-link")
            self.assertEqual([f.detail for f in broken], ["-> ./missing.md"])

    def test_language_inside_code_not_flagged(self):
        # a profanity token that appears only as a data literal inside a code
        # fence is not prose — flag-only audit must not surface it.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            entry = Project(name="fx", path=str(root), docs=["wiki"], wiki="wiki",
                            language_policy="flag-only")
            _mk(root, "wiki/dict.md",
                "---\nt: x\n---\n"
                "Clean prose line.\n"
                '```python\nterms = ["fucking", "bastard"]\n```\n')
            findings = audit_target(root, entry, siblings=set())
            self.assertEqual(_checks(findings, "vulgar"), [])
            # but the SAME token in prose IS flagged
            _mk(root, "wiki/prose.md", "---\nt: x\n---\nyou fucking wrote that\n")
            findings2 = audit_target(root, entry, siblings=set())
            self.assertEqual(len(_checks(findings2, "vulgar")), 1)

    def test_junk_and_conflict(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _mk(root, "wiki/.DS_Store", "junk")
            _mk(root, "wiki/c.md", "---\nt: x\n---\n<<<<<<< HEAD\na\n=======\nb\n>>>>>>> other\n")
            findings = self._audit(root)
            self.assertEqual(len(_checks(findings, "junk")), 1)
            self.assertEqual(len(_checks(findings, "conflict")), 1)


class TestDocsListFileEntries(unittest.TestCase):
    """A registry `docs:` entry may be a FILE (e.g. a top-level readme.md), not
    just a directory — the adaptation that lets non-wiki targets get covered."""

    def test_top_level_file_entry_is_scanned(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _mk(root, "docs/inner.md", "clean\n")
            _mk(root, "readme.md", "trailing here \n")   # root file a docs/-only scan misses
            entry = Project(name="fx", path=str(root), docs=["docs", "readme.md"])
            findings = audit_target(root, entry, siblings=set())
            tw = {f.path for f in _checks(findings, "trailing-ws")}
            self.assertIn("readme.md", tw)

    def test_dir_only_scan_misses_root_file(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _mk(root, "docs/inner.md", "clean\n")
            _mk(root, "readme.md", "trailing here \n")
            entry = Project(name="fx", path=str(root), docs=["docs"])   # dir only
            findings = audit_target(root, entry, siblings=set())
            self.assertEqual(_checks(findings, "trailing-ws"), [])

    def test_file_entry_not_double_counted(self):
        # a file that also lives under a scanned dir must be yielded once
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _mk(root, "docs/page.md", "dup \n")
            entry = Project(name="fx", path=str(root), docs=["docs", "docs/page.md"])
            findings = audit_target(root, entry, siblings=set())
            self.assertEqual(len(_checks(findings, "trailing-ws")), 1)

    def test_skip_dirs_still_excluded_for_file_entries(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _mk(root, "build/generated.md", "trailing \n")   # build is a SKIP_DIR
            entry = Project(name="fx", path=str(root), docs=["build/generated.md"])
            findings = audit_target(root, entry, siblings=set())
            self.assertEqual(_checks(findings, "trailing-ws"), [])


if __name__ == "__main__":
    unittest.main()
