"""pm fix — targeted corrections beyond mechanical cleaning (scaffold stage).

Planned fixer classes (M002 — each lands only after its audit check is
proven against real targets):
  frontmatter    add/repair YAML frontmatter on wiki pages
  index          regenerate _index.md files from directory contents
  links          rewrite relative links broken by known moves (fed by migrations)

Status: SCAFFOLD. The guard framework + CLI contract are real; fixers land
one at a time per Infrastructure > Instructions (a recurring correction
becomes a fixer, not advice).
"""
from __future__ import annotations

import argparse
import sys

from tools._mutate import ChangeReport, add_mutation_args, guard
from tools.registry import resolve_target


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="pm fix", description=__doc__)
    add_mutation_args(ap)
    ap.add_argument("--fixers", default="", help="comma-separated fixers to run")
    args = ap.parse_args(argv)
    target, entry = resolve_target(args.target, args.project)
    guard(target, entry, args.apply, args.allow_dirty)
    report = ChangeReport(apply=args.apply)
    if not args.fixers:
        report.skip(target, "no fixers implemented yet (M002) — see module docstring for the plan")
    else:
        for fixer in args.fixers.split(","):
            report.skip(target, f"fixer '{fixer}' not implemented yet (M002)")
    return report.print(f"FIX {target}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
