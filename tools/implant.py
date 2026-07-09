"""pm implant — implant the second-brain layer into a target (scaffold stage).

Stamps the implant manifest (templates/brain/ + wiki skeleton) into a target
that has `brain: none|partial` in the registry, per the second-brain adoption
guide. ADDITIVE: existing files are never overwritten — a conflicting stamp
lands as `<name>.proposed` for operator review (Hard Rule 8).

Status: SCAFFOLD (M003). The manifest + conflict policy below are real; the
per-file adaptation pass (replacing {{PROJECT}} etc.) is the M003 implement
task. Run with --dry-run (default) to see the plan.
"""
from __future__ import annotations

import argparse
import sys

from tools._mutate import ChangeReport, add_mutation_args, guard, propose
from tools._paths import TEMPLATES_DIR
from tools.registry import resolve_target

# Implant manifest: template source (under templates/) -> destination in target.
MANIFEST = {
    "brain/CLAUDE.project.md": "CLAUDE.md",
    "brain/AGENTS.project.md": "AGENTS.md",
    "brain/rules/work-mode.md": ".claude/rules/work-mode.md",
    "backlog/epic.md": "wiki/backlog/epics/_template.md",
    "backlog/module.md": "wiki/backlog/modules/_template.md",
    "backlog/task.md": "wiki/backlog/tasks/_template.md",
}
DIRS = ["wiki/log", "wiki/backlog/epics", "wiki/backlog/modules", "wiki/backlog/tasks"]


def substitute(text: str, project_name: str) -> str:
    return text.replace("{{PROJECT}}", project_name)


# Root-level dirs whose leaf name collides with a wiki/ subtree we stamp — a
# target that already organises these at the root (flat layout) would get a
# PARALLEL wiki/ copy rather than integration. Surface it so the operator can
# decide (migrate the existing tree, or adapt the manifest) before --apply.
_WIKI_LEAVES = {"backlog", "log"}


def structure_advisories(target: Path) -> list[str]:
    if (target / "wiki").is_dir():
        return []                                   # already wiki-organised — no collision
    notes: list[str] = []
    for leaf in sorted(_WIKI_LEAVES):
        existing = target / leaf
        if existing.is_dir() and any(existing.iterdir()):
            notes.append(
                f"target already has a root '{leaf}/' — implant would create "
                f"'wiki/{leaf}/' ALONGSIDE it (parallel, not integrated). "
                f"Decide: migrate '{leaf}/' into wiki/, or adapt the manifest."
            )
    return notes


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="pm implant", description=__doc__)
    add_mutation_args(ap)
    args = ap.parse_args(argv)
    target, entry = resolve_target(args.target, args.project)
    guard(target, entry, args.apply, args.allow_dirty, getattr(args, 'force_write', False))
    name = entry.name if entry else target.name
    report = ChangeReport(apply=args.apply)

    for d in DIRS:
        dest = target / d
        if not dest.is_dir():
            report.act("mkdir", d)
            if args.apply:
                dest.mkdir(parents=True, exist_ok=True)

    for src_rel, dst_rel in MANIFEST.items():
        src = TEMPLATES_DIR / src_rel
        dst = target / dst_rel
        if not src.is_file():
            report.skip(dst_rel, f"template missing: templates/{src_rel}")
            continue
        content = substitute(src.read_text(encoding="utf-8"), name)
        if dst.exists():
            if dst.read_text(encoding="utf-8") == content:
                report.skip(dst_rel, "identical — already implanted")
                continue
            propose(report, target, dst, content, args.apply,
                    "exists + differs; additive per Hard Rule 8")
        else:
            report.act("stamp", dst_rel)
            if args.apply:
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(content, encoding="utf-8")

    rc = report.print(f"IMPLANT {name} -> {target}")
    for note in structure_advisories(target):
        print(f"  ADVISORY: {note}")
    if args.apply:
        print("NOTE: update projects.yaml brain: field for this target (operator-approved edit).")
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
