# .claude/rules/routing.md — Operator intent → verb routing + verb contracts

> Loaded on demand when operator intent is ambiguous. CLAUDE.md has the summary table.

## Verb contracts (shared by all mutating verbs)

Every verb accepts target selection:
- `--target <path>` — explicit path to a project checkout
- `--project <name>` — resolve path via `projects.yaml` registry
- (report only) no selector = all registry projects

Every MUTATING verb (clean, fix, implant, upgrade, migrate, scaffold) additionally:
- defaults to **dry-run**; requires `--apply` to write
- refuses dirty targets (uncommitted changes) unless `--allow-dirty`
- prints a change report: `WOULD <action> <path>` (dry-run) / `DID <action> <path>` (apply) / `SKIP <path>: <reason>`
- is idempotent: second `--apply` run reports 0 changes

**Brain layout is per-project, not hardcoded.** The adoption guide makes the
backlog and operator-log paths a per-project choice — only the epic>module>task
hierarchy is sacrosanct, not the `wiki/` prefix. `implant`/`upgrade`/`scaffold`
resolve those paths from the registry's `backlog_root` / `log_root` (empty →
ecosystem default `wiki/backlog` + `wiki/log`); the brain templates carry
`{{BACKLOG}}` / `{{LOG}}` placeholders. A target that already keeps a `backlog/`
and directive log elsewhere (e.g. sovereign-os `backlog/` + `docs/standing-directives/`)
must declare those roots so implant lands ON them instead of creating a parallel
`wiki/`. `structure_advisories` warns when a configured path would duplicate an
existing populated tree.

## Routing table

| Operator says... | Verb | Notes |
|---|---|---|
| "audit X" / "check X" / "scan X" | `pm audit --target/--project X` | Read-only. Checks: broken relative links, frontmatter presence/shape in wiki pages, junk files, merge-conflict markers, empty files. |
| "clean X" / "corrections" (mechanical) | `pm clean` | audit first → dry-run → show → `--apply` on approval |
| "fix X" (judgment corrections) | `pm fix` | frontmatter repair, index regen — per-check flags |
| "implant" / "wiki-hub implantation" / "install the brain" | `pm implant` | Stamps templates per implant manifest; additive; conflicts → `.proposed` |
| "upgrade" / "re-sync the brain" | `pm upgrade` | Diff canonical templates vs target; additive merge or `.proposed` |
| "migrate" / restructure | `pm migrate --list` then `pm migrate --id NNNN` | Versioned; state recorded in target at `.pm/migrations.applied` |
| "scaffold a <type> in X" | `pm scaffold <type>` | Stamps a single template |
| "is X's CI green" / "will the PR be red" / pre-PR check | `pm doctor` | Read-only. Detects the target's CI workflow(s), extracts the check commands, and runs the SAFE STATIC ones locally (linters / type-checkers / format --check) → GREEN/RED/UNKNOWN. Test suites + format-in-place are detected but not run (`--tests` to run tests). Every mutating `--apply` also runs a fast (sub-second linters only) pre-flight via `doctor.preflight_advisory` and warns when the target's CI is ALREADY red — so a red PR check reads as pre-existing target debt, not a surprise from our change. |
| "report" / "health of everything" | `pm report` | audit across registry, consolidated output |
| "registry" / "what targets" | `pm registry list` | |
| "log <directive>" | Write `wiki/log/YYYY-MM-DD-<slug>.md` | BEFORE acting |

## Mechanism order of preference

1. An existing verb (`bin/pm ...`) — never improvise one-off bash against a target when a verb exists.
2. Extend the verb (add a check/fixer) when the need is recurring — Infrastructure > Instructions.
3. One-off bash only for genuinely one-time investigation, read-only.
