---
title: "M002 — Audit/clean hardening"
type: module
project: "project-maintainer"
parent_epic: E001-base-toolbelt
status: draft
priority: high
readiness: 0
created: "2026-07-03"
updated: "2026-07-03"
tags: [audit, clean]
---

# M002 — Audit/clean hardening

## Scope

Run `pm audit` against every real target; triage the findings; harden the check set (reduce false positives, add missing check classes — e.g. wiki-link `[[...]]` resolution, stale-count detection, index/dir drift); grow `clean`/`fix` one fixer per proven recurring finding (Infrastructure > Instructions).

## Done When

- [ ] Audit findings triaged on all 4 registry targets, false positives fixed
- [ ] ≥2 new check classes added from real findings
- [ ] `pm clean --apply` run and verified idempotent on ≥1 sister project
- [ ] First `pm fix` fixer implemented (likely frontmatter or index regen)
