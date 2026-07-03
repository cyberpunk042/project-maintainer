---
title: "M005 — Language cleanup (slurs / vulgar)"
type: module
project: "project-maintainer"
parent_epic: E001-base-toolbelt
status: done
priority: high
readiness: 85
created: "2026-07-03"
updated: "2026-07-03"
tags: [language, content-policy, audit, clean]
---

# M005 — Language cleanup (slurs / vulgar)

## Scope

The content-cleanup capability the project name implies: detect and (when appropriate) redact slurs and vulgar language across a target's docs/wiki. Two data-driven tiers (`config/language.yaml`), per-project policy (`language_policy` in `projects.yaml`), conservative defaults, and a per-run `--language-policy` override for explicit operator authorization.

Operator directive (verbatim): *"cleanup slur and vulgar language when and if appropriate, including my verbatim, words like "fucking", etc... NNRT a project you dont know has intentional mean words though, just to consider that some sister project be treated differently."*

## What landed

- `config/language.yaml` — vulgar + slur word lists, replacement mode (data, not code)
- `tools/language.py` — curated whole-word detection (no Scunthorpe false positives), policy matrix, redaction
- `audit` gains `slur` + `vulgar` checks (policy-gated)
- `clean` gains a `profanity` fixer (opt-in, policy-gated, never in the default set, dry-run default)
- `projects.yaml` `language_policy` per project (root-ghostproxy + second-brain → `preserve` for sacrosanct verbatim)
- `.claude/rules/content-policy.md` — policy semantics + the sacrosanct-verbatim tension
- `tests/test_language.py` — 11 regression tests, wired into `pm selfcheck`

## Done When

- [x] Audit flags both tiers under flag-only; suppresses vulgar under preserve; suppresses all under preserve-all
- [x] Profanity fixer refuses unless policy authorizes; redacts under `clean`; idempotent second run
- [x] `--language-policy` per-run override works
- [x] Curated matching proven against Scunthorpe cases; 11 unit tests green in selfcheck
- [ ] First real operator-approved language cleanup applied to a sister project (deferred — needs operator "when appropriate" call per target)
