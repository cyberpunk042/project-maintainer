# migrations/ — versioned target migrations

Migrations restructure a TARGET project's docs/wiki (moves, renames, frontmatter rewrites). They are the heavy end of the toolbelt — every migration is operator-approved before it exists.

## Conventions

- **Naming:** `NNNN-<slug>.py`, zero-padded, monotonically increasing. The filename stem is the migration id.
- **Contract:** each migration module exposes:
  ```python
  DESCRIPTION = "one-line what/why"

  def plan(target: Path) -> list[tuple[str, str, str]]:
      """Return (action, path, detail) rows — what apply() WILL do. Pure, no writes."""

  def apply(target: Path) -> None:
      """Perform the change. Must be idempotent — safe to call twice."""
  ```
- **State:** applied ids are recorded inside the target at `.pm/migrations.applied` (one per line). `pm migrate` skips applied ids automatically.
- **Idempotency is mandatory.** `apply()` re-run must be a no-op.
- **Plan = truth.** Anything `apply()` does that `plan()` didn't report is a bug.
- **Dry-run default.** `pm migrate --project X` shows the plan; `--apply` executes (guarded: dirty-target refusal, writable check).

## Running

```bash
bin/pm migrate --list                       # all migrations
bin/pm migrate --project selfdef --list     # applied/pending vs a target
bin/pm migrate --project selfdef            # dry-run all pending
bin/pm migrate --project selfdef --id 0001-example --apply
```

No migrations exist yet — the first ones will be authored per-need (e.g. a docs/ restructure in a sister project), with operator approval per `.claude/rules/work-mode.md`.
