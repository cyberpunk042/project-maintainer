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
