---
title: "M004 — Migration runner"
type: module
project: "project-maintainer"
parent_epic: E001-base-toolbelt
status: draft
priority: medium
readiness: 0
created: "2026-07-03"
updated: "2026-07-03"
tags: [migrations]
---

# M004 — Migration runner

## Scope

Harden the migration runner (plan/apply contract, `.pm/migrations.applied` bookkeeping, per-migration verification) and author the first real migrations per-need — e.g. a docs/wiki restructure in a sister project. Every migration is operator-approved before it exists.

## Done When

- [ ] Runner verified on a fixture target (plan = apply, idempotent re-run)
- [ ] First real migration authored + approved + applied to a sister project
- [ ] Post-migration audit clean on the migrated area
