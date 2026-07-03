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
from tools.registry import resolve_target

TRAILING_WS_RE = re.compile(r"[ \t]+$", re.MULTILINE)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="pm clean", description=__doc__)
    add_mutation_args(ap)
    ap.add_argument("--fixers", default="junk,trailing-ws",
                    help="comma-separated fixers to run (default: junk,trailing-ws)")
    args = ap.parse_args(argv)
    target, entry = resolve_target(args.target, args.project)
    guard(target, entry, args.apply, args.allow_dirty)
    fixers = set(args.fixers.split(","))
    report = ChangeReport(apply=args.apply)

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
    return report.print(f"CLEAN {target}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
