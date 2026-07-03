# project-maintainer
Used to maintain, clean, level-up projects.

## What it is

The ecosystem's **maintenance toolbelt**: a Python core with bash wrappers that operates ON sister projects (path-based or registry-driven) to keep their wikis, docs, and brain layers clean, consistent, and up to standard. The second-brain (`devops-solutions-information-hub`) defines the standards; project-maintainer **applies and enforces them on targets**.

Operator seed (verbatim): *"it will help us to clean the other project with scripts and such, template and such, migrations, etc..."*

## Capability map (the name is the spec: maintain · clean · level-up)

| Verb | What it does | Status |
|---|---|---|
| `audit` | Scan a target's wiki/ + docs/: broken links, missing/invalid frontmatter, junk files, conflict markers, empty pages, drift signals. Read-only. | working (base checks) |
| `clean` | Apply safe mechanical corrections found by audit (junk removal, whitespace, link fixes). Dry-run by default. | scaffold |
| `fix` | Targeted corrections beyond mechanical (frontmatter repair, index regen). Dry-run by default. | scaffold |
| `implant` | Implant the second-brain layer into a target (brain files, rules skeleton, wiki/backlog + wiki/log structure, methodology.yaml) per the adoption guide. | scaffold |
| `upgrade` | Re-sync an already-implanted target with newer canonical templates (diff-first, additive — never wholesale replace). | scaffold |
| `migrate` | Run versioned, idempotent migrations against a target (moves, renames, frontmatter rewrites) with dry-run + report. | scaffold |
| `scaffold` | Stamp templates (pages, backlog items, brain pieces) into a target. | scaffold |
| `report` | Run audit across all registry projects; emit a consolidated health report. | working (wraps audit) |
| `registry` | List/inspect the target-project registry (`projects.yaml`). | working |

## Usage

```bash
bin/pm <verb> [--target <path> | --project <registry-name>] [options]

# examples
bin/pm registry list
bin/pm audit --target ../sovereign-os
bin/pm report                      # audit everything in projects.yaml
bin/pm clean --project selfdef --dry-run
```

Python core is invocable directly: `python3 -m tools.pm <verb> ...` (stdlib-only; PyYAML used when present, graceful fallback otherwise).

## Layout

| Path | Purpose |
|---|---|
| `tools/` | Python core (one module per verb + registry + shared paths) |
| `bin/pm` | Bash wrapper / single entrypoint |
| `templates/` | Canonical templates stamped into targets (brain files, backlog items, pages) |
| `migrations/` | Versioned migration scripts + conventions |
| `projects.yaml` | Target-project registry (path + remote + layout per project) |
| `wiki/` | This project's own backlog + operator log + methodology config |
| `CLAUDE.md` / `AGENTS.md` / `CONTEXT.md` | The brain (routing, rules, state) |

## Principles (inherited from the second-brain)

1. **Infrastructure > Instructions** — corrections ship as tools/hooks/migrations, not prose advice.
2. **Structured Context > Content** — registry + templates + YAML program the behavior.
3. **Goldilocks** — process scales with the target's identity/phase/scale.
4. **Declarations Aspirational Until Verified** — every clean/implant/migrate ends with a verification pass; dry-run is the default everywhere.

Read-only by default, destructive only with explicit flags, additive over destructive (adding ≠ discarding), operator words sacrosanct (logged verbatim in `wiki/log/`).
