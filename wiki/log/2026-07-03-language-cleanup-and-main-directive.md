# 2026-07-03 — Language-cleanup feature + "USE main" directive (verbatim, sacrosanct)

> Logged BEFORE acting. Operator words preserved exactly, including strong language (which is itself the subject of the directive).

## Operator directive (verbatim)

> "continue the development and making things better and documented and improve the features and add the missing ones that the project name implies. things such as cleanup slur and vulgar language when and if appropriate, including my verbatim, words like "fucking", etc... NNRT a project you dont know has intentional mean words though, just to consider that some sister project be treated differently. when I ask to use main, USE Main...."

## Agent reading (flagged as agent-interpretation, not operator words)

- **Use main.** Corrective directive — develop and push on `main`, not the `claude/…` branch. Honored: this session is on `main`.
- **New flagship feature the name implies:** a language/content cleanup capability — detect + (when appropriate) redact slurs and vulgar language, *including the operator's own verbatim* ("fucking", etc.).
- **"when and if appropriate"** + **"NNRT [do not assume] a project you dont know has intentional mean words"** + **"some sister project be treated differently"** → this must be **per-project policy**, conservative by default:
  - Do NOT auto-clean. Dry-run default; profanity fixer never runs in the default `clean` set.
  - Unknown / undeclared project → **flag-only** (surface findings; refuse to auto-clean). Don't assume intent either way.
  - Known-intentional projects (operator-verbatim sacrosanct language — root-ghostproxy, second-brain) → **preserve** (their strong language is intentional; cleaning it would violate their own sacrosanct-verbatim rule).
  - Explicit **clean** policy → the fixer may redact when invoked.
- Slurs (targeted hate) and vulgar (stylistic profanity) are separate tiers so policy can treat them differently.
- Also: improve/document existing verbs, add missing ones the name implies.

## Note on this very log

Operator said clean own verbatim "when and if appropriate". The BEFORE-acting rule (log operator words verbatim) takes precedence for the primary-source log — so the quote above is preserved exactly. project-maintainer's own `language_policy` is set to `preserve` in the registry for the same reason the second-brain is: its logs are operator-verbatim primary sources.
