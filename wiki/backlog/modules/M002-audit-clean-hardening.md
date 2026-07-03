---
title: "M002 — Audit/clean hardening"
type: module
project: "project-maintainer"
parent_epic: E001-base-toolbelt
status: in-progress
priority: high
readiness: 70
created: "2026-07-03"
updated: "2026-07-03"
tags: [audit, clean, fix]
---

# M002 — Audit/clean hardening

## Scope

Run `pm audit` against every real target; triage the findings; harden the check set (reduce false positives, add missing check classes — e.g. wiki-link `[[...]]` resolution, stale-count detection, index/dir drift); grow `clean`/`fix` one fixer per proven recurring finding (Infrastructure > Instructions).

## Progress

- [x] Audit triaged on all 4 targets; two false-positive classes fixed (log/nav frontmatter exemptions; cross-repo link reclassification). Signal: root-ghostproxy 27→9, sovereign-os 53→5.
- [x] `--json` output on `audit` + `report` for programmatic triage.
- [x] `tests/test_audit.py` (9) covering the precision rules.

## Done When

- [x] Audit findings triaged on all 4 registry targets, false positives fixed
- [x] ≥2 new check classes / precision rules added from real findings (cross-repo, frontmatter exemptions)
- [x] First `pm fix` fixer implemented — `links` (conservative unique-match link repair) + `clean --diff` byte-level preview
- [ ] `pm clean --apply` run and verified idempotent on ≥1 sister project (needs operator go-ahead on a target)
