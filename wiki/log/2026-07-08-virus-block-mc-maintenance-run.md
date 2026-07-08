# 2026-07-08 — Run project-maintainer on the-virus-block-mc

## Operator directive (verbatim, sacrosanct)

> "USING project-maintainer, lets try it again but this time on the-virus-block-mc. we might need to adapt the project / tool first and to review before merging."

## Reading

- New target: `the-virus-block-mc` — a **Java/Gradle Minecraft mod** (shaders/rendering).
  This is the first non-Rust/non-wiki target. It has a `docs/` tree (156 `.md` total, ~40 under `docs/`), a large root `readme.md`, `INSTRUCTIONS.md`, `investigation_report.md`.
- Not an Obsidian vault, not operator-verbatim strong-language corpus → `language_policy: flag-only` (unknown-target default; don't assume intent).
- Registry did not yet contain this target.

## Adaptation assessment

- The tool already skips `build`/`target`/`dist` (Gradle output) via `SKIP_DIRS` — no code change needed for Gradle.
- `fix --fixers wikilinks` is **Obsidian-specific** (converts broken links to `[[wikilinks]]`) — inappropriate for this repo; NOT used here.
- `fix --fixers links` (default) is safe: only repairs a broken link when exactly one basename match exists; the 3 broken links here point at files that exist nowhere, so it correctly skips them rather than inventing a target.
- Applicable safe operation: `clean --fixers trailing-ws` (mechanical, byte-reviewable via `--diff`).

## Read-only audit result (baseline)

`python3 -m tools.pm audit --target ~/the-virus-block-mc` → 33 findings:
- `trailing-ws` = 30 (mechanical, safe to strip)
- `broken-link` = 3 (all in `docs/help/DESIGN_PATTERNS.md` → `../00_TODO_DIRECTIVES.md` ×2, `../02_CLASS_DIAGRAM.md`; targets absent everywhere → not auto-fixable, left for operator)
- 0 junk, 0 conflict, 0 empty, 0 slur, 0 vulgar

## Plan

1. Register target (flag-only, writable, docs:[docs]).
2. `clean --diff` dry-run preview (trailing-ws) → review.
3. `fix --fixers links` dry-run → confirm the 3 broken links are safely skipped.
4. Apply trailing-ws cleanup on the target's feature branch; push; draft PR; operator reviews before merge.

## Correction pass (operator: "WHERE IS THE ADAPTATING AND THE REVIEW OF THE RESULT ??????")

The first pass under-delivered on two of the operator's explicit words — *"adapt the tool first"* and *"review before merging"*. Redone properly:

### Adaptation 1 — coverage (the tool only saw 34% of the docs)

`doc_roots()` only returned **directories**, so the target's biggest doc (root `readme.md`) and all top-level + `src/`/`config/` markdown were silently skipped — 53 of 156 `.md` scanned. Fix: `docs:` registry entries may now be **files** as well as dirs (`iter_doc_files()`), deduped, still honoring `SKIP_DIRS`. Registry entry expanded to `[docs, readme.md, INSTRUCTIONS.md, investigation_report.md, LICENSE-CLARIFICATION.md, config, src]`; `.agent/` deliberately excluded (agent scratch). Tests: `TestDocsListFileEntries` (4).

### Adaptation 2 — the trailing-ws fixer was collapsing Markdown hard breaks

**Review finding:** a content line ending in **2+ trailing spaces is a CommonMark hard line break (`<br>`)**. The old fixer stripped them blindly — a *rendering* change, not cosmetic. The first (pushed) docs-only pass stripped **~20 hard breaks**, and `readme.md` alone carries **88** that the naive fixer would have destroyed. Fix: `clean_trailing_ws()` preserves hard breaks; strips only whitespace-only lines and single trailing spaces/tabs; audit's `trailing-ws` detector uses the same rule so audit and clean agree. Test: `test_preserves_markdown_hard_break`.

### Reviewed result (redone on the target, from a clean `master` base)

- 31 files, **whitespace-only** (`git diff --ignore-all-space` empty).
- **0 hard breaks stripped** (was 20); `readme.md` left entirely untouched (all-hard-break).
- selfcheck green, **61 tests**.
