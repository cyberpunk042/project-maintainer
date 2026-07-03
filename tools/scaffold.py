"""pm scaffold — stamp a single template into a target (scaffold stage).

Usage: pm scaffold <type> --target/--project ... [--name <slug>]
Types map to files under templates/ (e.g. backlog/task, backlog/epic).
Additive: never overwrites; existing destination -> `.proposed` sibling.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

from tools._mutate import ChangeReport, add_mutation_args, guard
from tools._paths import TEMPLATES_DIR
from tools.registry import resolve_target

DESTINATIONS = {
    "backlog/epic": "wiki/backlog/epics/{name}.md",
    "backlog/module": "wiki/backlog/modules/{name}.md",
    "backlog/task": "wiki/backlog/tasks/{name}.md",
}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="pm scaffold", description=__doc__)
    ap.add_argument("type", help=f"template type: {', '.join(DESTINATIONS)}")
    ap.add_argument("--name", default="new-item", help="destination slug")
    add_mutation_args(ap)
    args = ap.parse_args(argv)
    target, entry = resolve_target(args.target, args.project)
    guard(target, entry, args.apply, args.allow_dirty, getattr(args, 'force_write', False))
    report = ChangeReport(apply=args.apply)

    src = TEMPLATES_DIR / f"{args.type}.md"
    if args.type not in DESTINATIONS or not src.is_file():
        raise SystemExit(f"ERROR: unknown template type '{args.type}' (have: {', '.join(DESTINATIONS)})")
    dst = target / DESTINATIONS[args.type].format(name=args.name)
    content = (src.read_text(encoding="utf-8")
               .replace("{{PROJECT}}", entry.name if entry else target.name)
               .replace("{{NAME}}", args.name)
               .replace("{{DATE}}", date.today().isoformat()))
    if dst.exists():
        dst = dst.with_name(dst.name + ".proposed")
        report.act("propose", dst.relative_to(target), "destination exists")
    else:
        report.act("stamp", dst.relative_to(target))
    if args.apply:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(content, encoding="utf-8")
    return report.print(f"SCAFFOLD {args.type} -> {target}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
