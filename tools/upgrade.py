"""pm upgrade — re-sync an implanted target with newer canonical templates.

Diffs each implant-manifest destination against the current template; identical
files are skipped, drifted files get a `.proposed` sibling (NEVER overwritten —
additive per Hard Rule 8; the operator merges or accepts).

Status: SCAFFOLD (M003). Shares the manifest with implant; the diff-summary UX
(what drifted, how much) is the M003 implement task.
"""
from __future__ import annotations

import argparse
import sys

from tools.implant import MANIFEST, substitute
from tools._mutate import ChangeReport, add_mutation_args, guard, propose
from tools._paths import TEMPLATES_DIR
from tools.registry import resolve_target


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="pm upgrade", description=__doc__)
    add_mutation_args(ap)
    args = ap.parse_args(argv)
    target, entry = resolve_target(args.target, args.project)
    guard(target, entry, args.apply, args.allow_dirty, getattr(args, 'force_write', False))
    name = entry.name if entry else target.name
    report = ChangeReport(apply=args.apply)

    for src_rel, dst_rel in MANIFEST.items():
        src = TEMPLATES_DIR / src_rel
        dst = target / dst_rel
        if not src.is_file():
            report.skip(dst_rel, f"template missing: templates/{src_rel}")
            continue
        if not dst.exists():
            report.skip(dst_rel, "not implanted (run pm implant)")
            continue
        canonical = substitute(src.read_text(encoding="utf-8"), name)
        if dst.read_text(encoding="utf-8") == canonical:
            report.skip(dst_rel, "up to date")
            continue
        propose(report, target, dst, canonical, args.apply, "drifted from canonical")
    return report.print(f"UPGRADE {name} -> {target}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
