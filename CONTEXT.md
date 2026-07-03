# CONTEXT.md — project-maintainer current state

> Live operational state. Updated as work lands. Identity + rules live in [CLAUDE.md](CLAUDE.md) / [AGENTS.md](AGENTS.md).

## Current phase

**Scaffold** (SFIF: Scaffold), on `main` (operator directive: use main). Base landed 2026-07-03 (M001); language-cleanup feature landed same day (M005).

## Active epic

- **E001 — Base toolbelt** ([wiki/backlog/epics/E001-base-toolbelt.md](wiki/backlog/epics/E001-base-toolbelt.md))
  - M001 base scaffold — done (scaffold stage)
  - M002 audit/clean hardening — next
  - M003 implant/upgrade engine — after M002
  - M004 migration runner — after M002
  - M005 language cleanup (slurs/vulgar) — done (working: audit flags + policy-gated `clean --fixers profanity` + 11 tests)

## Next-best moves

1. Triage the ~540 `bin/pm report` findings across the four targets; harden audit checks and grow `clean`/`fix` fixers per real recurring findings (M002).
2. Design the implant manifest (which template files land where, per adoption guide) before `implant --apply` (M003).
3. When the operator calls it "appropriate" for a specific target: run the language cleanup end-to-end on a sister project (set `language_policy: clean` or use `--language-policy clean`, dry-run → review → apply).

## Operator-pending decisions

- Per-target language cleanup is opt-in by design — each "clean the language in X" is an operator "when appropriate" call. No standing decision pending.

## Registry snapshot

Targets in [projects.yaml](projects.yaml): sovereign-os (`flag-only`), selfdef (`flag-only`), root-ghostproxy (`preserve` — sacrosanct verbatim), second-brain (`preserve`, READ-ONLY — never written from here).
