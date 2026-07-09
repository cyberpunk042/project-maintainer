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

- **Every verb is working + tested** — no scaffold-only stubs remain: `registry`, `audit` (8 checks, precision-hardened), `clean` (junk/trailing-ws/profanity, `--diff`), `fix` (links), `report` (`--json`), `migrate` (runner + reference migration), `implant`/`upgrade`/`scaffold` (smoke), `selfcheck`.
- Tests: 44 (language 11 · audit 9 · guard 7 · migrate 4 · implant 5 · clean 4 · fix 4).
- Safety proven under test: dry-run default, dirty-target refusal, writable gating, additive `.proposed`, idempotency, byte-level `--diff` review.

## Next-best moves

1. Finalize + get operator approval on the implant manifest before any `implant --apply` on a brainless sister (M003).
2. When the operator says a specific target is ready: run the real cleanup (`audit` → `clean --diff` review → `clean --apply`), starting with the safest classes (junk, trailing-ws), then broken-link `fix`.
3. Grow audit checks / clean+fix fixers per whatever the first real cleanup surfaces.

## Operator-pending decisions

- Per-target language cleanup is opt-in by design — each "clean the language in X" is an operator "when appropriate" call. No standing decision pending.

## Registry snapshot

Targets in [projects.yaml](projects.yaml): sovereign-os (`flag-only`), selfdef (`flag-only`), root-ghostproxy (`preserve` — sacrosanct verbatim), the-virus-block-mc (`flag-only`), nnrt (`flag-only` — loaded-language tool; findings are often legitimate data), second-brain (`preserve`, READ-ONLY — never written from here).

## Recent runs

- **2026-07-09 — NNRT test + improve cycle** ([log](wiki/log/2026-07-09-nnrt-test-and-improve-directive.md)). Registered nnrt; full audit accurate (0 structural, 1 legit-data vulgar). Surfaced + fixed a precision bug: the trailing-ws cleaner was not fenced-code-block aware (applied the hard-break rule inside code fences, and inconsistently stripped inside them). Now: prose cleaned hard-break-safe, **fenced code left byte-exact**. NNRT trailing-ws findings dropped 28→10 (noise removed). +2 tests (63 total). No mutation applied to NNRT — awaits operator go.
