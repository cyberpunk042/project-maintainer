# .claude/rules/work-mode.md — How the agent operates in project-maintainer

> Loaded on demand for solo-session pattern + PO approval boundary. CLAUDE.md has the hot-path rules.

## Context

Solo coding AI helping the operator (PO) build and run the maintenance toolbelt. Not a fleet agent, not a sub-agent.

## Default operation mode

- Work on `main` (operator directive 2026-07-03: "on the main"). No feature branches unless the operator explicitly asks.
- Operator decides commits unless explicitly delegated for a work block.
- No worktrees, no git stash.

## The special danger of this project

Every mutating verb here touches ANOTHER project's files. The discipline stack:

1. **Dry-run default** — mutation only with `--apply`.
2. **Dirty-target refusal** — mutating verbs check `git status --porcelain` on the target and refuse if dirty (override `--allow-dirty`, must be logged).
3. **Report before/after** — show the operator exactly what would change / changed.
4. **Idempotency** — re-running any verb must be a no-op the second time.
5. **Additive over destructive** — implant/upgrade merge or emit `.proposed` siblings; they never overwrite.

## Safe unilateral work (no approval needed)

- Reading anything (this repo, targets, second-brain).
- Running read-only verbs: `registry`, `audit`, `report`, any `--dry-run`.
- Drafting in `wiki/log/`, `wiki/backlog/`, scratch locations.
- Fixing bugs in `tools/` internals; adding audit checks.

## Needs operator approval before execution

- Any `--apply` against a target (unless the operator asked for that exact operation).
- Changes to CLAUDE.md / AGENTS.md / CONTEXT.md / projects.yaml / methodology.yaml.
- New or changed templates (they define what gets stamped into every target).
- New migrations (they restructure targets).
- Git operations that could lose work.

## Verify status claims

"Cleaned" / "implanted" / "migrated" / "done" claims must inline the verifying command's output in the same response (P4 — Declarations Aspirational Until Verified).
