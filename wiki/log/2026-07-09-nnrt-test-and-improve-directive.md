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

## Cycle 4 — M003 manifest review (dry-run implant on real brainless targets)

Reviewed the implant manifest against the two genuinely-brainless registered
targets, sovereign-os and selfdef (both Rust; `brain: none`). Dry-run only.

Manifest is sound: no AGENTS/CLAUDE conflict on either (clean stamps),
`{{PROJECT}}` substitution correct, the rendered CLAUDE.md/AGENTS.md are generic
ADAPT-marked scaffolds (TODO placeholders, no fabricated identity), and every
internal link (`AGENTS.md`, `.claude/rules/work-mode.md`, `wiki/backlog/`,
`wiki/log/`) resolves to something the same implant creates.

**Finding — layout mismatch.** Both targets already keep a populated root
`backlog/` (INDEX.md, SHIPPED.md, epics/) and have NO `wiki/`. The manifest
hardcodes the second-brain greenfield layout (`wiki/backlog/`, `wiki/log/`), so
implanting would create a `wiki/backlog/` PARALLEL to the existing `backlog/` —
duplication, not integration.

Tool improvement (safe, additive — no manifest change): `implant` now emits a
`structure_advisories()` NOTE when the target has no `wiki/` but does have a
root dir whose leaf collides with a wiki subtree we stamp (`backlog`, `log`).
The dry-run now says, on both targets: *"target already has a root 'backlog/' —
implant would create 'wiki/backlog/' ALONGSIDE it ... Decide: migrate 'backlog/'
into wiki/, or adapt the manifest."* Silent on wiki-organised targets. +2 tests
(72 total).

**Operator-pending decision (does NOT block anything — no implant is imminent):**
before any `implant --apply` on sovereign-os / selfdef, choose the backlog
layout: (a) point the brain at the existing root `backlog/` (adapt the manifest
+ templates to `backlog/` instead of `wiki/backlog/`); (b) author a migration
that moves `backlog/` under `wiki/`; or (c) accept `wiki/backlog/` as the
canonical brain backlog and leave the legacy `backlog/` as-is. Manifest / new
migration changes need operator approval (work-mode) — surfaced, not chosen.

## Cycle 5 — resolving that decision by reasoning to the real answer

Operator: *"you need to think by yourself and find out what is the real right
answer"* — i.e. stop offering a menu; determine it. Did so from the CANONICAL
adoption guide (`devops-solutions-information-hub/wiki/spine/references/adoption-guide.md`),
which is explicit: *"Backlog paths — if your backlog lives at a different path,
update all references"* and *"Change `wiki/log/` to wherever your project stores
operator directives ... (or your equivalent path)"*. **Only the epic>module>task
hierarchy + frontmatter state machines are sacrosanct; the `wiki/` prefix is
not.**

So all three options I'd offered were subtly wrong — (b) migrate and (c) parallel
both FORCE a layout the standard leaves free, and (a) framed adaptation as a
per-run chore. The real defect was in THIS tool: `implant`/`upgrade`/`scaffold`
hardcoded `wiki/backlog/` + `wiki/log/`, making project-maintainer *stricter
than the standard it exists to enforce*.

Evidence that clinched it: sovereign-os already has a mature root `backlog/`
(`epics/ modules/ features/ milestones/ requirements/`) and keeps verbatim
operator mandates in `docs/standing-directives/`; selfdef has a root `backlog/`
and date-prefixed directives in `docs/operator/`. Forcing `wiki/` would drop an
EMPTY backlog beside a populated one and a `wiki/log/` beside the real directive
store.

Fix (the answer, implemented): made the implant layout **registry-driven**.
- `projects.yaml` gains `backlog_root` / `log_root` (empty → ecosystem default
  `wiki/backlog` / `wiki/log`, so wiki projects are unchanged).
- Templates use `{{BACKLOG}}` / `{{LOG}}` placeholders (substituted like
  `{{PROJECT}}`); `implant`/`upgrade`/`scaffold` derive dirs, manifest
  destinations, and stamped content from the target's roots.
- Set sovereign-os → `backlog` + `docs/standing-directives`; selfdef →
  `backlog` + `docs/operator`.
- `structure_advisories` reworked (cycle-4 → cycle-5): now warns only when the
  *configured* path would create a fresh tree while a populated same-leaf dir
  exists elsewhere — i.e. "you haven't told the registry about this layout".
  Silent once the roots are set correctly.

Verified: dry-run implant on sovereign-os / selfdef now stamps into their real
`backlog/` + directive dirs, creates NOTHING under `wiki/`, advisory silent;
rendered CLAUDE.md points at `backlog/` + `docs/standing-directives/`. Default
`wiki/` layout preserved for wiki projects (tested). `selfcheck`: **74 tests
pass**. No mutation applied to any real target.

**Decision RESOLVED** — the layout is per-project by the standard; the tool now
honours it. No operator menu needed.

## Cycle 6 — first real deliverable, and the CI-blindness gap it exposed

Applied the NNRT trailing-ws cleanup for real (operator: *"ready"*):
`clean --apply` on 10 docs files, +22/−22, verified whitespace-only (0 content
change), NNRT re-audits clean. Pushed to NNRT's branch → **NNRT PR #15** (draft).

**NNRT CI went red.** Investigated: the failing step is `ruff check nnrt/ tests/`
reporting **6422 pre-existing errors** in NNRT's own `.py` files (E501, W291,
…) — nothing to do with the docs-only change (ruff doesn't lint markdown). CI
was already red before the PR.

Operator: *"it should have detected the CI is will fail, we need to improve
project-maintainer."* Correct — project-maintainer mutated + pushed + opened a PR
**blind to the target's build/gate health**. A tool that opens PRs should know
the target's CI baseline so a red check reads as pre-existing target debt, not an
after-the-fact surprise.

Fix — new read-only verb **`pm doctor`** (`tools/doctor.py`):
- detects `.github/workflows/*.yml`, extracts the check commands the CI runs
  (inline + block `run:` steps, split on `&&`/`;`);
- classifies each: static linter / type-check / format / test / modify / skip;
- runs the SAFE, STATIC ones locally (ruff/flake8/mypy/black --check/cargo
  clippy/…) — they parse code, don't execute or modify it; test suites +
  format-in-place are detected but NOT run (`--tests` opts in);
- reports GREEN / RED / UNKNOWN with the failing command + summary.

Plus a **fast pre-flight** wired into the mutation guard (`_mutate.guard`): every
`--apply` runs `doctor.preflight_advisory` (sub-second linters only — ruff /
flake8 / black --check; never mypy/cargo/pytest) and prints `CI PRE-FLIGHT:
target CI baseline is RED …` when the target's CI is already failing. Advisory
only — never blocks or crashes a mutation.

Verified: `pm doctor --project nnrt` → `[FAIL] ruff check nnrt/ tests/ — 6422
error(s)` → BASELINE RED; `clean --apply` on nnrt now prints the RED pre-flight
warning before touching anything. +16 tests (`test_doctor.py`: classify /
extract / derive_status hermetic + real-ruff red/green when ruff present).
`selfcheck`: **90 tests pass**.

**NNRT PR #15 status:** the docs change is correct + whitespace-only; the red CI
is NNRT's own pre-existing ruff debt (out of scope for a docs-cleanup PR, and
outside project-maintainer's current reach — `clean` maintains markdown, not
Python lint). Operator's call whether to merge #15 (docs-only, red is
pre-existing) or leave it until NNRT's lint debt is addressed separately.
