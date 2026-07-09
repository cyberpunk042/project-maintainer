"""Regression tests for the language cleanup engine + policy gating.

Run: python3 -m tests.test_language   (or: python3 -m unittest -v)
Stdlib unittest — no third-party deps.
"""
from __future__ import annotations

import unittest

from tools.language import (
    DEFAULT_POLICY,
    load_config,
    redact_text,
    scan,
    tiers_for_policy,
)

CFG = load_config()


class TestPolicyMatrix(unittest.TestCase):
    def test_flag_tiers(self):
        self.assertEqual(tiers_for_policy("clean", action="flag"), {"vulgar", "slur"})
        self.assertEqual(tiers_for_policy("flag-only", action="flag"), {"vulgar", "slur"})
        self.assertEqual(tiers_for_policy("preserve", action="flag"), {"slur"})
        self.assertEqual(tiers_for_policy("preserve-all", action="flag"), set())

    def test_clean_tiers_only_under_clean(self):
        self.assertEqual(tiers_for_policy("clean", action="clean"), {"vulgar", "slur"})
        for p in ("flag-only", "preserve", "preserve-all"):
            self.assertEqual(tiers_for_policy(p, action="clean"), set(),
                             f"{p} must not authorize mutation")

    def test_unknown_policy_falls_back_to_default(self):
        self.assertEqual(
            tiers_for_policy("nonsense", action="flag"),
            tiers_for_policy(DEFAULT_POLICY, action="flag"),
        )


class TestScan(unittest.TestCase):
    def test_detects_both_tiers(self):
        text = "This is fucking broken you retard."
        vulgar = scan(text, CFG, {"vulgar"})
        slur = scan(text, CFG, {"slur"})
        self.assertEqual([m.word.lower() for m in vulgar], ["fucking"])
        self.assertEqual([m.word.lower() for m in slur], ["retard"])

    def test_case_insensitive(self):
        self.assertTrue(scan("FUCK this", CFG, {"vulgar"}))

    def test_no_substring_false_positive(self):
        # Scunthorpe problem: innocent words containing a bad substring must NOT match.
        for innocent in ("assessment", "classic", "shitake_is_not_listed", "scunthorpe", "pistachio"):
            self.assertEqual(scan(innocent, CFG, {"vulgar", "slur"}), [],
                             f"false positive on '{innocent}'")

    def test_line_numbers(self):
        text = "clean line\nfucking here\n"
        hits = scan(text, CFG, {"vulgar"})
        self.assertEqual(hits[0].line_no, 2)


class TestRedact(unittest.TestCase):
    def test_redact_keeps_first_char(self):
        out, n = redact_text("you fucking retard", CFG, {"vulgar", "slur"})
        self.assertEqual(out, "you f****** r*****")
        self.assertEqual(n, 2)

    def test_redact_only_selected_tier(self):
        out, n = redact_text("fucking retard", CFG, {"slur"})
        self.assertEqual(out, "fucking r*****")  # vulgar untouched
        self.assertEqual(n, 1)

    def test_empty_tiers_no_change(self):
        text = "fucking retard"
        out, n = redact_text(text, CFG, set())
        self.assertEqual((out, n), (text, 0))

    def test_idempotent(self):
        once, _ = redact_text("fucking retard", CFG, {"vulgar", "slur"})
        twice, n = redact_text(once, CFG, {"vulgar", "slur"})
        self.assertEqual(once, twice)
        self.assertEqual(n, 0)

    def test_redact_skips_fenced_code(self):
        # a slur/vulgar token inside a code fence is a data literal, not prose —
        # redaction must leave it byte-exact and only touch prose.
        src = 'the fucking prose\n```python\nterms = ["fucking", "retard"]\n```\ntail retard\n'
        out, n = redact_text(src, CFG, {"vulgar", "slur"})
        self.assertIn('terms = ["fucking", "retard"]', out)   # code untouched
        self.assertNotIn("fucking prose", out)                 # prose redacted
        self.assertNotIn("tail retard", out)
        self.assertEqual(n, 2)                                 # only the 2 prose tokens

    def test_redact_skips_inline_code(self):
        out, n = redact_text("run `grep fucking file` now, fucking", CFG, {"vulgar"})
        self.assertIn("`grep fucking file`", out)              # inline code untouched
        self.assertEqual(n, 1)                                 # only the trailing prose token


if __name__ == "__main__":
    unittest.main()
