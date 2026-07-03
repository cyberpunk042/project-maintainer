# .claude/rules/self-reference.md — What project-maintainer IS

> Loaded on demand for identity questions + second-brain boundary.

## What this project IS

The **maintenance toolbelt** of the ecosystem. It doesn't hold knowledge (that's the second-brain) and it doesn't run a domain workload (that's the sister projects). It **acts on** other projects: audit, clean, fix, implant, upgrade, migrate, scaffold, report.

## The triangle (don't conflate)

| Layer | Project | Role toward the others |
|---|---|---|
| **Standards / knowledge** | `devops-solutions-information-hub` (second-brain) | DEFINES the methodology, schemas, templates, lessons. Read-only from here. |
| **Enforcement / application** | `project-maintainer` (this) | APPLIES the standards to targets: implants the brain layer, cleans drift, migrates structures. |
| **Targets** | sovereign-os, selfdef, root-ghostproxy, ... | RECEIVE maintenance. Their own brains stay their own; we stamp and correct, we don't own. |

## Boundary rules

- **Consume, never write, the second-brain.** Templates here start as adapted copies of second-brain canon; when canon evolves, `upgrade` re-syncs targets. Contributions back to the second-brain go through ITS contribute channel, from a session operating there — not from here.
- **Targets own their state.** After an implant/migration, the target's files belong to the target. We keep applied-migration bookkeeping in the target at `.pm/migrations.applied` (small, additive) — nothing else of ours lives in targets.
- **This project's own wiki/ is tiny by design**: backlog + operator log + methodology config. It is NOT a knowledge wiki; don't grow one here.

## Behave FROM the project

When asked to check/correct a target: reach for `bin/pm` verbs and the registry first. A missing capability is a backlog task (extend the verb), not a reason to improvise unmanaged bash against a target.
