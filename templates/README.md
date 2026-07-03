# templates/ — canonical templates stamped into targets

These are the files `pm implant` / `pm upgrade` / `pm scaffold` stamp into target projects. They start as adapted derivatives of second-brain canon (`devops-solutions-information-hub/wiki/config/templates/` + the adoption guide); when canon evolves, update here, then `pm upgrade` re-syncs targets.

## Placeholders

| Placeholder | Replaced with |
|---|---|
| `{{PROJECT}}` | target project name (registry name or directory name) |
| `{{NAME}}` | item slug (scaffold only) |
| `{{DATE}}` | today, ISO format (scaffold only) |

## Layout

| Path | Stamped to (in target) | Used by |
|---|---|---|
| `brain/CLAUDE.project.md` | `CLAUDE.md` | implant, upgrade |
| `brain/AGENTS.project.md` | `AGENTS.md` | implant, upgrade |
| `brain/rules/work-mode.md` | `.claude/rules/work-mode.md` | implant, upgrade |
| `backlog/epic.md` | `wiki/backlog/epics/` | implant (as `_template.md`), scaffold |
| `backlog/module.md` | `wiki/backlog/modules/` | implant (as `_template.md`), scaffold |
| `backlog/task.md` | `wiki/backlog/tasks/` | implant (as `_template.md`), scaffold |

Adding a template: place the file, add it to `MANIFEST` in `tools/implant.py` (implant-set) or `DESTINATIONS` in `tools/scaffold.py` (scaffold-set), run `bin/pm selfcheck`.

Changes to templates need operator approval (`.claude/rules/work-mode.md`) — they define what lands in EVERY target.
