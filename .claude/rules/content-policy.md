# .claude/rules/content-policy.md — Language cleanup policy + the sacrosanct-verbatim tension

> Loaded on demand when the operator asks to clean up slurs / vulgar language, or when tuning `config/language.yaml` / `language_policy`. Origin: operator directive 2026-07-03 ([wiki/log/2026-07-03-language-cleanup-and-main-directive.md](../../wiki/log/2026-07-03-language-cleanup-and-main-directive.md)).

## The feature

`audit` flags — `clean --fixers profanity` redacts — two tiers of language, defined as **data** in `config/language.yaml`:

- **vulgar** — stylistic profanity ("fucking", "shit", …). Often intentional.
- **slur** — targeted-hate / demeaning terms ("retard", …).

Both are gated **per project** by `language_policy` in `projects.yaml`.

## Policy semantics

| Policy | Audit flags | Fixer redacts | Use for |
|---|---|---|---|
| `clean` | slur + vulgar | both | project where all such language should go |
| `flag-only` | slur + vulgar | **refuses** | **default / unknown** — surface, let operator decide |
| `preserve` | slur only | refuses | intentional vulgar (operator-verbatim); still catch slurs |
| `preserve-all` | nothing | refuses | fully operator-verbatim / intentional corpus |

## The operator's three constraints (verbatim, 2026-07-03)

1. *"cleanup slur and vulgar language when and if appropriate, including my verbatim, words like "fucking""* — the feature must be willing to clean even the operator's own strong language.
2. *"NNRT [do not assume] a project you dont know has intentional mean words"* — an **unknown** target is NOT assumed to have intentional language → default `flag-only` (flag, don't preserve, don't auto-destroy).
3. *"just to consider that some sister project be treated differently"* — **known** projects whose strong language is intentional get `preserve`.

## The sacrosanct-verbatim tension (important)

Two ecosystem projects carry operator-verbatim strong language as a **core, sacrosanct rule** — their brains literally instruct "quote the operator verbatim, never dilute":

- **root-ghostproxy** and the **second-brain** → `language_policy: preserve`.

Redacting vulgar language there would violate *their own* sacrosanct-verbatim rule. So: preserve vulgar, still flag slurs (a slur in a doc is worth surfacing even in those repos — the operator decides). This is the concrete meaning of "some sister project be treated differently."

`project-maintainer`'s own `wiki/log/` is likewise operator-verbatim primary source — do not run the profanity fixer against this repo's own logs.

## Discipline

- **Dry-run default.** Profanity is **never** in the default `clean` fixer set (`junk,trailing-ws`); it only runs on explicit `--fixers profanity`.
- **Policy-gated.** The fixer refuses unless policy is `clean` (registry) or `--language-policy clean` (explicit per-run operator authorization).
- **Whole-word, curated variants** — no substring stemming (avoids the Scunthorpe problem). Tune the lists in `config/language.yaml`, not in code.
- **When ambiguous, flag — don't clean.** If unsure whether a target's language is intentional, leave it `flag-only` and surface it. The operator decides ("when and if appropriate").
