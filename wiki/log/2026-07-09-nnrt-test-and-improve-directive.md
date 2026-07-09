# 2026-07-09 — Operator directive: test + improve on NNRT

> Sacrosanct verbatim. Logged BEFORE acting (Hard Rule 1).

## Directive (verbatim)

"Lets test and imrove project-maintainer. we can try it on NNRT now. we will need to cycle and review to improve the project-maintainer"

## Reading

- Test the toolbelt against a first real, non-registered sister target: **NNRT**
  (`Narrative-to-Neutral-Report-Transformer`).
- **Cycle**: run verbs → observe findings → improve the tool from what surfaces.
- NNRT is the operator's canonical "unknown target — do not assume intentional
  mean words" example (content-policy.md). It is a tool that *detects and
  neutralizes loaded language*, so its docs/specs carry loaded/vulgar/slur terms
  **as data** (dictionaries, examples, test corpora). This makes it an excellent
  stress test of the language checker's false-positive behavior under
  `flag-only` (audit surfaces, fixer refuses — nothing destroyed).

## Actions this session

1. Register NNRT in `projects.yaml` (`flag-only`, doc roots = docs/ + top-level
   prose docs; `.agent/` + `.gemini/` excluded as agent scratch per the
   virus-block-mc precedent; LICENSE.md excluded as legal boilerplate).
2. Full audit → review findings.
3. Cycle: fix tool issues surfaced by the run.

## Cycle 1 — results (2026-07-09)

**Test run.** Registered NNRT (`flag-only`, 54 doc files scanned incl. 3
top-level prose docs). Audit was accurate:

- Structural checks (broken-link / conflict / empty / junk / cross-repo) = **0
  findings**. Verified NOT a false-negative: NNRT has 130 relative md links and
  they all resolve; every source file is scanned.
- Language: **1 vulgar** (`bastard`) — a term inside a *list of loaded terms*
  in `docs/specs/phase5_validation.md` (NNRT's own detection dictionary).
  `flag-only` surfaces it without redacting — exactly the intended behaviour for
  the operator's "don't assume intentional mean words" example.
- Trailing-ws: **28 files** (initial).

**Bug surfaced + fixed — trailing-ws cleaner was not fenced-code-block aware.**
The hard-break-safe cleaner applied the CommonMark "2+ trailing spaces = hard
break, preserve" rule *inside* fenced code blocks (where hard breaks don't
exist), while simultaneously stripping other whitespace inside those same fences
— inconsistent, and wrong for a tool that edits OTHER repos (a text-processing
project like NNRT can carry meaningful trailing whitespace in code/data
samples). Empirical on NNRT docs: 7 in-fence lines falsely treated as hard
breaks; 18 of the 28 flagged files were flagged *only* for in-fence whitespace.

Fix (`tools/audit.py::clean_trailing_ws`, used by both `audit` and `clean`):
prose is cleaned hard-break-safe; **fenced code content is left byte-exact**;
fence delimiter lines get the normal prose strip. +2 regression tests
(`test_preserves_fenced_code_bytes`, `test_fenced_code_is_idempotent_noop`).

Result: trailing-ws findings **28 → 10** (all 10 now genuine prose drift, e.g.
`### heading ` with a single trailing space). `selfcheck`: **63 tests pass**.

**Not applied.** No mutation run against NNRT — `clean --apply` awaits operator
"when appropriate" call. Preview available via
`bin/pm clean --project nnrt --fixers trailing-ws --diff`.

## Cycle 2 — code-aware checks (2026-07-09)

Ran `bin/pm report` across the whole registry (also exercised the report verb —
works, all 6 targets local). The sweep surfaced the SAME root cause as cycle 1
in two more checks: **code content was being scanned as prose.**

- **broken-link** flagged markdown links written inside code as if navigable —
  e.g. `` `[filename.md](path/to/file.md)` `` in second-brain's
  session-handoff-standards / model-wiki-design (docs that *teach* link syntax).
  7 of second-brain's 133 broken-link findings were such code examples.
- **language (vulgar/slur)** flagged tokens that live only as data literals —
  NNRT's lone `bastard` hit was inside a ```python``` dictionary
  (`terms = [..., "bastard", ...]`), not prose.

Fix: added `mask_code(text)` (`tools/audit.py`) — blanks fenced code blocks +
inline code spans, length-preserving. `audit` now runs broken-link / cross-repo
/ slur / vulgar over the masked text. Made `redact_text` (`tools/language.py`)
code-aware to match, so the `clean` profanity fixer would never corrupt a code
sample — `flag` and `clean` agree on what counts as prose. Structural checks
(conflict, frontmatter, trailing-ws) still run on raw text (trailing-ws has its
own fence-aware path from cycle 1). +4 regression tests (audit link-in-code,
audit language-in-code, redact fenced, redact inline).

Result: NNRT vulgar 1→0 (10 findings, all genuine prose drift); second-brain
broken-link 133→126 (report total 183→176). Genuine broken links + prose
profanity still flagged (tested). `selfcheck`: **67 tests pass**.

The remaining 126 second-brain broken-links are genuine (repo-root-relative
links written as file-relative, links into `.claude/` / sibling repos) — but
second-brain is READ-ONLY from here; we surface, its own session fixes them.

## Cycle 3 — the thin verbs (implant/upgrade/scaffold/migrate) on a fixture

Drove the whole lifecycle against a throwaway git fixture (the least-tested
scaffold-tier code). `implant` stamp + `{{PROJECT}}` substitution + idempotency
+ conflict→`.proposed`, `upgrade` up-to-date, `scaffold` stamp/propose,
`migrate` list/apply/idempotent-replay + the `0001-ensure-final-newline`
migration all verified working (migrate correctly plans a fix for a file with no
final newline — the earlier "0 changes" was a genuinely-clean fixture, not a
no-op bug).

**Bug found + fixed — the `.proposed` conflict path was not idempotent and
could clobber operator work.** `implant`, `upgrade`, and `scaffold` each wrote
`<name>.proposed` *unconditionally* when the destination existed + differed. So:
(1) re-running the verb re-proposed every time — "1 change" on every run, a
routing-contract idempotency violation ("second `--apply` reports 0 changes");
and (2) worse, if the operator had started merging/editing the `.proposed`, the
next run silently **overwrote their in-progress merge** — a data-loss risk in
the additive-review workflow that Hard Rule 8 exists to prevent.

Fix: one shared `propose()` helper in `tools/_mutate.py` used by all three
verbs. It stages `<dst>.proposed` additively:

- absent → propose (WOULD/DID)
- present + identical → SKIP "already proposed (identical)" — idempotent no-op
- present + differs → SKIP "resolve/remove it before re-proposing" — never
  clobbers the operator's file

+3 regression tests (re-propose-identical no-op, no-clobber-operator-edit,
scaffold conflict idempotency). `selfcheck`: **70 tests pass**.

All four thin verbs now honour the full mutating-verb contract (dry-run default,
dirty-refusal, writable gating, additive `.proposed`, idempotency) end-to-end.
