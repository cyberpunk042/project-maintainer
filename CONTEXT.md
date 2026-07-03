# CONTEXT.md — project-maintainer current state

> Live operational state. Updated as work lands. Identity + rules live in [CLAUDE.md](CLAUDE.md) / [AGENTS.md](AGENTS.md).

## Current phase

**Scaffold → implement** on `main` (operator directive: use main). Toolbelt maturing before any real cleanup on a sister repo (operator goal). 36 unit tests green via `bin/pm selfcheck`.

## Active epic

- **E001 — Base toolbelt** ([wiki/backlog/epics/E001-base-toolbelt.md](wiki/backlog/epics/E001-base-toolbelt.md))
  - M001 base scaffold — done
  - M002 audit/clean hardening — in-progress (false-positive classes fixed, `--json`, 9 tests)
  - M003 implant/upgrade engine — draft (smoke-tested; manifest pre-approval pending)
  - M004 migration runner — in-progress (runner proven + reference migration + tests)
  - M005 language cleanup (slurs/vulgar) — done

## Maturity snapshot (before we try a real cleanup)

- Working + tested: `registry`, `audit` (8 checks, precision-hardened), `clean` (junk/trailing-ws/profanity), `report`, `migrate` (runner + reference migration), `implant`/`upgrade`/`scaffold` (smoke), `selfcheck`.
- Tests: 36 (language 11 · audit 9 · guard 7 · migrate 4 · implant 5).
- Safety proven: dry-run default, dirty-target refusal, writable gating, additive `.proposed`, idempotency.

## Next-best moves

1. Implement the first `pm fix` fixer (frontmatter repair or `_index.md` regen) — the last scaffold-only verb (M002/M003).
2. Finalize + get operator approval on the implant manifest before any `implant --apply` on a brainless sister (M003).
3. When the operator says a specific target is ready: run the real cleanup (audit → review → `clean --apply`), starting with the safest classes.

## Operator-pending decisions

- Per-target language cleanup is opt-in by design — each "clean the language in X" is an operator "when appropriate" call. No standing decision pending.

## Registry snapshot

Targets in [projects.yaml](projects.yaml): sovereign-os (`flag-only`), selfdef (`flag-only`), root-ghostproxy (`preserve` — sacrosanct verbatim), second-brain (`preserve`, READ-ONLY — never written from here).
