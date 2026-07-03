---
title: "M004 — Migration runner"
type: module
project: "project-maintainer"
parent_epic: E001-base-toolbelt
status: in-progress
priority: medium
readiness: 60
created: "2026-07-03"
updated: "2026-07-03"
tags: [migrations]
---

# M004 — Migration runner

## Scope

Harden the migration runner (plan/apply contract, `.pm/migrations.applied` bookkeeping, per-migration verification) and author the first real migrations per-need — e.g. a docs/wiki restructure in a sister project. Every migration is operator-approved before it exists.

## Progress

- [x] Runner verified end-to-end on a fixture (list → dry-run → apply → applied-state → idempotent skip); dirty-target guard confirmed
- [x] Reference migration `0001-ensure-final-newline` (safe, idempotent) + `tests/test_migrate.py`

## Done When

- [x] Runner verified on a fixture target (plan = apply, idempotent re-run)
- [ ] First real migration authored + approved + applied to a sister project (deferred — per-need, operator-approved)
- [ ] Post-migration audit clean on the migrated area
