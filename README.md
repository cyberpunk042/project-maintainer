# project-maintainer
Used to maintain, clean, level-up projects.

## What it is

The ecosystem's **maintenance toolbelt**: a Python core with bash wrappers that operates ON sister projects (path-based or registry-driven) to keep their wikis, docs, and brain layers clean, consistent, and up to standard. The second-brain (`devops-solutions-information-hub`) defines the standards; project-maintainer **applies and enforces them on targets**.

Operator seed (verbatim): *"it will help us to clean the other project with scripts and such, template and such, migrations, etc..."*

## Capability map (the name is the spec: maintain · clean · level-up)

| Verb | What it does | Status |
|---|---|---|
| `audit` | Scan a target's wiki/ + docs/: broken links, missing/invalid frontmatter, junk files, conflict markers, empty pages, **slurs / vulgar language** (per-project policy), drift signals. Read-only. | working |
| `clean` | Apply safe mechanical corrections found by audit (junk removal, trailing whitespace, **policy-gated profanity redaction**). Dry-run by default. | working (junk · trailing-ws · profanity) |
| `fix` | Targeted corrections. `links`: repair a broken relative link to a uniquely-named file. `wikilinks`: convert a broken relative link to a moved `.md` note into a dynamic Obsidian `[[stem\|display]]` wikilink (move-resilient — the fix for vaults whose files migrate through maturity stages; anchors/ambiguous left alone). Dry-run + `--diff`. | working |
| `implant` | Implant the second-brain layer into a target (brain files, rules skeleton, wiki/backlog + wiki/log structure) per the adoption guide. Additive; conflicts → `.proposed`. | working (smoke-tested; manifest pre-approval) |
| `upgrade` | Re-sync an already-implanted target with newer canonical templates (diff-first, additive — never wholesale replace). | working (smoke-tested) |
| `migrate` | Run versioned, idempotent migrations against a target (moves, renames, frontmatter rewrites) with dry-run + report + applied-state bookkeeping. | working (runner + reference migration) |
| `scaffold` | Stamp a single template (page, backlog item) into a target. | working |
| `report` | Run audit across all registry projects; consolidated health report (`--json` for triage). | working |
| `registry` | List/inspect the target-project registry (`projects.yaml`). | working |
| `selfcheck` | Sanity-check this repo (imports, registry, manifest, language config, unit tests). | working |

## Usage

```bash
bin/pm <verb> [--target <path> | --project <registry-name>] [options]

# examples
bin/pm registry list
bin/pm audit --target ../sovereign-os
bin/pm audit --project selfdef --json       # machine-readable findings for triage
bin/pm report                               # audit everything in projects.yaml
bin/pm clean --project selfdef --dry-run
bin/pm clean --project selfdef --diff       # exact byte-level preview before approving
bin/pm migrate --project selfdef --list     # applied/pending migrations vs a target
```

Every mutating verb (`clean`, `fix`, `implant`, `upgrade`, `migrate`, `scaffold`) defaults to **dry-run**, requires `--apply` to write, refuses a dirty target (uncommitted changes) without `--allow-dirty`, and is idempotent. Run `bin/pm selfcheck` to verify the toolbelt itself (currently 36 unit tests).

Python core is invocable directly: `python3 -m tools.pm <verb> ...` (stdlib-only; PyYAML used when present, graceful fallback otherwise).

### Language cleanup (slurs / vulgar language)

`audit` flags — and `clean --fixers profanity` redacts — slurs and vulgar language, driven by data in [`config/language.yaml`](config/language.yaml) (two tiers: `slur`, `vulgar`) and gated **per project** by `language_policy` in [`projects.yaml`](projects.yaml):

| Policy | Audit flags | `clean --fixers profanity` |
|---|---|---|
| `clean` | slur + vulgar | redacts both (when invoked + `--apply`) |
| `flag-only` (default / unknown) | slur + vulgar | **refuses** (surfaces, never auto-cleans) |
| `preserve` | slur only (vulgar is intentional) | refuses |
| `preserve-all` | nothing (operator-verbatim corpus) | refuses |

Design intent (operator directive 2026-07-03): clean *"when and if appropriate"*, *"consider that some sister project be treated differently"*. So: dry-run default, profanity **never** in the default `clean` set, unknown targets flagged-not-assumed, and projects whose strong language is intentional operator-verbatim (root-ghostproxy, second-brain — sacrosanct) set to `preserve`. A one-off `--language-policy <policy>` overrides the registry for a single run (explicit operator authorization). Matching is whole-word, case-insensitive, curated-variant (no substring stemming → no Scunthorpe false positives).

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
