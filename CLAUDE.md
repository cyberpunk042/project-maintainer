# CLAUDE.md — project-maintainer (Claude Code delta)

> Claude-Code-specific operating context. Universal cross-tool rules: [AGENTS.md](AGENTS.md). Current state: [CONTEXT.md](CONTEXT.md). Project description: [README.md](README.md). Detailed topic rules: [.claude/rules/](.claude/rules/).

## Operator Directives (Sacrosanct — verbatim, never paraphrase)

- "Lets init and start working on project-maintainer, on the main. Do the base and ask questions if needed" (2026-07-03)
- "it will help us to clean the other project with scripts and such, template and such, migrations, etc..." (2026-07-03)
- "all this and more... think about the name and extrapole" (2026-07-03 — capabilities scope)

Full log: [wiki/log/](wiki/log/) (verbatim, sacrosanct). Log new directives there BEFORE acting.

## Identity Profile (Goldilocks — stable fields only)

| Dimension | Value |
|---|---|
| **Type** | tooling (maintenance toolbelt operating ON sister projects) |
| **Domain** | code (Python core + bash wrappers) + knowledge (templates, migrations) |
| **Phase** | scaffold (new; base landing) |
| **Scale** | micro |
| **PM Level** | L1 (wiki/backlog + CLAUDE.md directives) |
| **Trust Tier** | operator-supervised |
| **Second Brain** | consumer (reads standards from `devops-solutions-information-hub`; applies them to targets) |

## Hard Rules (every-message hot path)

| # | Rule | Why |
|---|---|---|
| 1 | **Operator words are SACROSANCT — quote verbatim, log to `wiki/log/YYYY-MM-DD-<slug>.md` BEFORE acting.** Never paraphrase, dilute, or summarize. | Ecosystem alignment mechanism. |
| 2 | **Adding ≠ discarding.** New direction layers onto prior direction. Never replace sections wholesale unless the operator explicitly directs. | Recurring ecosystem failure mode (going-to-extremes). |
| 3 | **Dry-run is the default for every mutating verb** (clean / fix / implant / upgrade / migrate / scaffold). Mutation requires `--apply`. A tool that writes without `--apply` is a bug. | This project's whole job is touching OTHER projects — blast radius discipline. |
| 4 | **Never mutate a dirty target.** Mutating verbs refuse to run against a target with uncommitted git changes (override: `--allow-dirty`, logged). | Target repos are the operator's work; don't mix tool output with WIP. |
| 5 | **Status claims must inline verification output.** "Cleaned" / "implanted" / "migrated" without command output in the same response is aspirational (P4). | Second-brain Principle 4. |
| 6 | **Behave FROM the project.** Use `bin/pm` / `python3 -m tools.pm` verbs, the registry, and the templates — don't improvise one-off bash against targets when a verb exists. | Second-brain doctrine. |
| 7 | **The second-brain is consumed, never written.** Standards/templates flow FROM `devops-solutions-information-hub` here; knowledge flows back only via its own contribute channel. Don't write into the second-brain repo from here. | Ecosystem boundary rule. |
| 8 | **Additive implant/upgrade.** `implant`/`upgrade` never overwrite an existing target file wholesale; they diff, then merge additively or emit a `.proposed` sibling for operator review. | Hard Rule 2 applied to targets. |
| 9 | **Solo work on `main`.** No feature branches, no auto-commit sprees; operator decides commits unless explicitly delegated. | Operator: "on the main". |

## Routing (operator intent → verb)

| Operator says... | First action |
|---|---|
| "audit X" / "check X" / "how dirty is X" | `bin/pm audit --target <path>` (or `--project <name>`) |
| "clean X" / "corrections" | `bin/pm audit` first, then `bin/pm clean --dry-run`, show, then `--apply` on approval |
| "implant the brain into X" / "wiki-hub implantation" | `bin/pm implant --project <name> --dry-run` |
| "upgrade X's brain" | `bin/pm upgrade --project <name> --dry-run` |
| "migrate X" / restructure docs/wiki | `bin/pm migrate --project <name> --list` then run specific migration |
| "report" / "health of everything" | `bin/pm report` |
| "add project X" / registry changes | Edit [projects.yaml](projects.yaml), then `bin/pm registry list` to verify |
| "log <directive>" / verbatim quote | Write `wiki/log/YYYY-MM-DD-<slug>.md` BEFORE acting |
| "status" / "what's next" | Read [CONTEXT.md](CONTEXT.md) + `wiki/backlog/` |

## Methodology

Stage-gate methodology adopted from the second-brain (adoption guide): engine at [wiki/config/methodology.yaml](wiki/config/methodology.yaml). 5 stages (document → design → scaffold → implement → test), hard ALLOWED/FORBIDDEN boundaries, backlog at [wiki/backlog/](wiki/backlog/) (epic → module → task, readiness flows up). Quality gates for THIS project: `python3 -m tools.pm selfcheck` (lint-level) and dry-runs of each verb against a fixture target.

## Pointers to Depth

| For... | Read |
|---|---|
| Universal cross-tool rules | [AGENTS.md](AGENTS.md) |
| Current state + next moves | [CONTEXT.md](CONTEXT.md) |
| Solo-session pattern + PO approval boundary | [.claude/rules/work-mode.md](.claude/rules/work-mode.md) |
| Intent → verb routing detail + verb contracts | [.claude/rules/routing.md](.claude/rules/routing.md) |
| What this project IS vs the second-brain | [.claude/rules/self-reference.md](.claude/rules/self-reference.md) |
| Target registry | [projects.yaml](projects.yaml) |
| Templates stamped into targets | [templates/](templates/) |
| Migration conventions | [migrations/README.md](migrations/README.md) |
| Second-brain adoption guide (canonical) | `../devops-solutions-information-hub/wiki/spine/references/adoption-guide.md` |
