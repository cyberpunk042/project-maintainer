---
title: "M003 — Implant/upgrade engine"
type: module
project: "project-maintainer"
parent_epic: E001-base-toolbelt
status: draft
priority: medium
readiness: 0
created: "2026-07-03"
updated: "2026-07-03"
tags: [implant, upgrade, second-brain]
---

# M003 — Implant/upgrade engine

## Scope

Finalize the implant manifest against the second-brain adoption guide (which brain pieces + wiki skeleton + methodology config land in a target), implement the per-target adaptation pass (placeholders, identity table, gate-command binding), and give `upgrade` a real diff summary UX. Design first (manifest as design doc), then implement — the templates define what lands in EVERY target, so operator approval gates each manifest change.

## Done When

- [ ] Implant manifest reviewed + approved by operator
- [ ] `pm implant --apply` lands a working brain layer on a brainless sister (sovereign-os or selfdef)
- [ ] `pm upgrade` shows drift meaningfully and proposes without overwriting
- [ ] Second run of both verbs is a no-op (idempotency verified)
