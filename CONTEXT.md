# CONTEXT.md — project-maintainer current state

> Live operational state. Updated as work lands. Identity + rules live in [CLAUDE.md](CLAUDE.md) / [AGENTS.md](AGENTS.md).

## Current phase

**Scaffold** (SFIF: Scaffold). Base landed 2026-07-03: brain files, wiki structure, registry, tool skeleton with working `registry`/`audit`/`report`, templates, migration conventions.

## Active epic

- **E001 — Base toolbelt** ([wiki/backlog/epics/E001-base-toolbelt.md](wiki/backlog/epics/E001-base-toolbelt.md))
  - M001 base scaffold (this landing) — done at scaffold stage
  - M002 audit/clean hardening — next
  - M003 implant/upgrade engine — after M002
  - M004 migration runner — after M002

## Next-best moves

1. Run `bin/pm audit` against a real sister project (sovereign-os or selfdef), review findings, harden checks (M002).
2. Implement `clean --apply` for the safest check classes (junk files, trailing whitespace, conflict markers).
3. Design the implant manifest (which template files land where, per adoption guide) before implementing `implant --apply` (M003).

## Operator-pending decisions

- None currently. (Scope questions answered 2026-07-03 — see [wiki/log/2026-07-03-operator-init-directive.md](wiki/log/2026-07-03-operator-init-directive.md).)

## Registry snapshot

Targets declared in [projects.yaml](projects.yaml): sovereign-os, selfdef, root-ghostproxy, devops-solutions-information-hub (audit-only — Hard Rule: never written from here).
