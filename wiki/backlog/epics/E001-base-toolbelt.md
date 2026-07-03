---
title: "E001 — Base toolbelt"
type: epic
project: "project-maintainer"
status: active
priority: high
readiness: 20
created: "2026-07-03"
updated: "2026-07-03"
modules: [M001-base-scaffold, M002-audit-clean-hardening, M003-implant-upgrade-engine, M004-migration-runner]
tags: [base, toolbelt]
---

# E001 — Base toolbelt

## Mission

Stand up the maintenance toolbelt end-to-end: registry, audit/report, safe cleaning, brain implantation/upgrade, and the migration runner — every verb honoring the guard contract (dry-run default, dirty-target refusal, additive stamps, idempotency).

Operator seed (verbatim): *"it will help us to clean the other project with scripts and such, template and such, migrations, etc..."*

## Modules

| Module | Scope | Status |
|---|---|---|
| [M001 base scaffold](../modules/M001-base-scaffold.md) | Brain files, registry, tool skeleton, working audit/report/registry/selfcheck, templates, migration conventions | done (scaffold stage) |
| [M002 audit/clean hardening](../modules/M002-audit-clean-hardening.md) | Run against real targets; add checks/fixers per real findings; `fix` fixer classes | next |
| [M003 implant/upgrade engine](../modules/M003-implant-upgrade-engine.md) | Implant manifest finalization, per-target adaptation pass, upgrade diff UX | after M002 |
| [M004 migration runner](../modules/M004-migration-runner.md) | First real migrations (per-need, operator-approved), runner hardening | after M002 |

## Done When

- [ ] `pm report` runs clean-or-triaged across all registry projects
- [ ] `pm clean --apply` trusted on at least 2 sister projects
- [ ] One real implant or upgrade landed on a sister project via `pm implant`/`pm upgrade`
- [ ] One real migration authored, applied, and verified idempotent
