# .claude/rules/work-mode.md — How the agent operates in {{PROJECT}}

> Loaded on demand for solo-session pattern + PO approval boundary. Implanted by project-maintainer; adapt the boundaries to this project.

## Default operation mode

- Solo session. Operator decides branch policy and commits unless explicitly delegated.
- No worktrees, no git stash, no subagent chains without operator review between tasks.

## Behavioral rules

- **When called out:** stop, re-read, identify what's actually missing. Don't repeat the mistake.
- **When told to investigate:** investigate — present findings, don't propose fixes.
- **When told to execute:** execute — no `--help` probing, no re-scoping questions.
- **Forward, not backward:** build from current state; don't revert and restart.
- **Grounded in reality:** verify each named tool/file/command exists before referencing it.

## PO approval boundary

**Safe unilateral work:** reading anything; running read-only tools; drafting in `wiki/log/` and scratch locations; mechanical fixes requiring no judgment.

**Needs operator approval:** changes to CLAUDE.md / AGENTS.md / root docs; schema or config policy changes; git operations that could lose work; restructuring directories.

<!-- ADAPT: extend both lists with project-specific entries. -->

## Verify status claims

Status claims (done / loaded / complete) must inline the verification command's output in the same response.
