# AGENTS.md — project-maintainer (universal cross-tool agent contract)

> Applies to ANY AI tool operating in this repo (Claude Code, opencode, Codex, Cursor, Gemini, ...). Claude-Code-specific delta lives in [CLAUDE.md](CLAUDE.md).

## What this project is

The ecosystem's maintenance toolbelt. It operates ON sister projects — auditing, cleaning, correcting, implanting/upgrading the second-brain layer, migrating docs/wiki structures, stamping templates. Python core (`tools/`), bash wrappers (`bin/pm`), template library (`templates/`), versioned migrations (`migrations/`), target registry (`projects.yaml`).

Operator seed (verbatim, 2026-07-03): *"it will help us to clean the other project with scripts and such, template and such, migrations, etc..."*

## Universal Hard Rules

1. **Operator words are sacrosanct.** Quote verbatim, never paraphrase. Log directives to `wiki/log/YYYY-MM-DD-<slug>.md` BEFORE acting.
2. **Adding ≠ discarding.** Layer new direction onto old; never wholesale-replace content (in this repo or in targets) unless the operator explicitly directs.
3. **Dry-run by default.** Every mutating verb requires `--apply` to touch a target. No exceptions.
4. **Never mutate a dirty target** (uncommitted git changes) without `--allow-dirty` + a logged reason.
5. **Verify status claims.** A verb "done" claim must inline the verifying command's output in the same response.
6. **Boundary: the second-brain is read-only from here.** Consume its standards/templates; never write into `devops-solutions-information-hub`.
7. **Don't fabricate.** Investigate with the project's own verbs (`audit`, `registry`, `report`) before asserting facts about a target's state.
8. **Read full files before synthesizing or editing.** Especially target files about to be corrected.

## Operating doctrine

- **Infrastructure > Instructions**: a recurring correction becomes a check in `audit` + a fixer in `clean`/`fix` + (when warranted) a migration — not advice in a doc.
- **Idempotency**: every mutating verb must be safe to re-run; second run is a no-op.
- **Report everything**: verbs emit what they saw, what they would change (dry-run) or changed (apply), and what they skipped. Silent skips are bugs.
- **Additive implants**: `implant`/`upgrade` diff first; conflicts produce `.proposed` siblings for operator review rather than overwrites.

## Structure

| Path | What |
|---|---|
| `tools/pm.py` | CLI dispatcher — `python3 -m tools.pm <verb>` |
| `tools/<verb>.py` | One module per verb (audit, clean, fix, implant, upgrade, migrate, scaffold, report) |
| `tools/registry.py` | projects.yaml loader (PyYAML optional; minimal fallback parser) |
| `bin/pm` | Bash entrypoint wrapping the Python core |
| `templates/` | Canonical templates (brain files, backlog items, wiki pages) |
| `migrations/` | Versioned migrations + `migrations/README.md` conventions |
| `wiki/backlog/` | This project's own epic/module/task backlog |
| `wiki/log/` | Operator directives, verbatim, date-prefixed |
| `wiki/config/methodology.yaml` | Stage-gate methodology engine (adopted from the second-brain) |
