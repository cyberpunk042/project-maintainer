---
title: "M001 — Base scaffold"
type: module
project: "project-maintainer"
parent_epic: E001-base-toolbelt
status: done
priority: high
readiness: 80
created: "2026-07-03"
updated: "2026-07-03"
tags: [scaffold]
---

# M001 — Base scaffold

## Scope

The 2026-07-03 base landing: brain files (CLAUDE/AGENTS/CONTEXT + 3 rules), `projects.yaml` registry, `tools/` core (dispatcher + 9 verbs + guard framework), `bin/pm` wrapper, `templates/` library, `migrations/` conventions, this backlog, methodology config.

## Done When

- [x] `bin/pm selfcheck` passes
- [x] `bin/pm registry list` shows all 4 targets
- [x] `bin/pm audit --target <sister>` produces findings on a real project
- [x] Mutating verbs refuse without `--apply` and refuse non-writable targets
