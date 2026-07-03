"""pm clean — apply SAFE mechanical corrections to a target (dry-run by default).

Implemented fixers (M001 base):
  junk          delete junk files (.DS_Store, *.orig, *.rej, swap/backup files)
  trailing-ws   strip trailing whitespace in markdown files

Further fixer classes land via M002 (audit/clean hardening) — one fixer per
recurring audit finding, per Infrastructure > Instructions.
"""
from __future__ import annotations

import argparse
import re
import sys

from tools.audit import JUNK_NAMES, JUNK_SUFFIXES, doc_roots, iter_files
from tools._mutate import ChangeReport, add_mutation_args, guard
from tools.language import DEFAULT_POLICY, load_config, redact_text, tiers_for_policy
from tools.registry import resolve_target

TRAILING_WS_RE = re.compile(r"[ \t]+$", re.MULTILINE)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="pm clean", description=__doc__)
    add_mutation_args(ap)
    ap.add_argument("--fixers", default="junk,trailing-ws",
                    help="comma-separated fixers: junk, trailing-ws, profanity "
                         "(profanity is opt-in AND policy-gated; never in the default set)")
    ap.add_argument("--language-policy", dest="language_policy",
                    help="override the registry language_policy for this run "
                         "(clean|flag-only|preserve|preserve-all) — explicit operator authorization")
    args = ap.parse_args(argv)
    target, entry = resolve_target(args.target, args.project)
    guard(target, entry, args.apply, args.allow_dirty)
    fixers = set(args.fixers.split(","))
    report = ChangeReport(apply=args.apply)

    # profanity fixer is authorized only by an explicit `language_policy: clean`
    # (registry) or an explicit --language-policy clean override.
    policy = args.language_policy or (entry.language_policy if entry else DEFAULT_POLICY)
    lang_tiers: set[str] = set()
    lang_cfg = None
    if "profanity" in fixers:
        lang_tiers = tiers_for_policy(policy, action="clean")
        if not lang_tiers:
            report.skip(target, f"profanity fixer refused: language_policy={policy} "
                                 f"(set language_policy: clean in projects.yaml to authorize)")
        else:
            lang_cfg = load_config()

    for root in doc_roots(target, entry):
        for f in iter_files(root):
            rel = f.relative_to(target)
            if "junk" in fixers and (f.name in JUNK_NAMES or f.name.endswith(JUNK_SUFFIXES)):
                report.act("delete", rel)
                if args.apply:
                    f.unlink()
                continue
            if "trailing-ws" in fixers and f.suffix.lower() in (".md", ".markdown"):
                try:
                    text = f.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    report.skip(rel, "unreadable as utf-8")
                    continue
                cleaned = TRAILING_WS_RE.sub("", text)
                if cleaned != text:
                    report.act("strip trailing-ws", rel)
                    if args.apply:
                        f.write_text(cleaned, encoding="utf-8")
            if lang_cfg is not None and f.suffix.lower() in (".md", ".markdown") and f.name != "language.yaml":
                try:
                    text = f.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    continue
                new_text, n = redact_text(text, lang_cfg, lang_tiers)
                if n:
                    report.act("redact language", rel, f"{n} match(es) [{'+'.join(sorted(lang_tiers))}]")
                    if args.apply:
                        f.write_text(new_text, encoding="utf-8")
    return report.print(f"CLEAN {target}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
