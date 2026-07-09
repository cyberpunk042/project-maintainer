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
from pathlib import Path

from tools._mutate import ChangeReport, add_mutation_args, guard, propose
from tools._paths import TEMPLATES_DIR
from tools.registry import resolve_target

# Ecosystem defaults — used when a target doesn't declare its own paths. The
# adoption guide makes backlog/log locations per-project; only the hierarchy is
# sacrosanct. Wiki-organised projects (second-brain, root-ghostproxy, this repo)
# leave the registry fields empty and get these.
DEFAULT_BACKLOG_ROOT = "wiki/backlog"
DEFAULT_LOG_ROOT = "wiki/log"

# Brain files whose DESTINATION path is fixed (their CONTENT is path-aware via
# {{BACKLOG}} / {{LOG}} substitution).
BRAIN_MANIFEST = {
    "brain/CLAUDE.project.md": "CLAUDE.md",
    "brain/AGENTS.project.md": "AGENTS.md",
    "brain/rules/work-mode.md": ".claude/rules/work-mode.md",
}
# Backlog scaffolding templates: source -> subpath UNDER the target's backlog_root.
BACKLOG_TEMPLATES = {
    "backlog/epic.md": "epics/_template.md",
    "backlog/module.md": "modules/_template.md",
    "backlog/task.md": "tasks/_template.md",
}


def backlog_root(entry) -> str:
    return (getattr(entry, "backlog_root", "") or "") or DEFAULT_BACKLOG_ROOT


def log_root(entry) -> str:
    return (getattr(entry, "log_root", "") or "") or DEFAULT_LOG_ROOT


def build_manifest(entry) -> dict[str, str]:
    """Full source->destination manifest for a target, backlog paths resolved
    to the target's configured backlog_root (default wiki/backlog)."""
    m = dict(BRAIN_MANIFEST)
    br = backlog_root(entry)
    for src, sub in BACKLOG_TEMPLATES.items():
        m[src] = f"{br}/{sub}"
    return m


def build_dirs(entry) -> list[str]:
    br = backlog_root(entry)
    return [log_root(entry), f"{br}/epics", f"{br}/modules", f"{br}/tasks"]


# Default manifest (wiki/ layout) — kept for selfcheck + backward-compatible imports.
MANIFEST = build_manifest(None)


def substitute(text: str, project_name: str, entry=None) -> str:
    return (text.replace("{{PROJECT}}", project_name)
                .replace("{{BACKLOG}}", backlog_root(entry))
                .replace("{{LOG}}", log_root(entry)))


def structure_advisories(entry, target: Path) -> list[str]:
    """Warn when we WOULD create a fresh backlog/log tree at the configured path
    while a populated directory of the same leaf name already exists elsewhere —
    i.e. the target has a layout the registry hasn't been told about, so implant
    would duplicate it. Silent once backlog_root/log_root point at the real dirs."""
    notes: list[str] = []
    for label, root in (("backlog", backlog_root(entry)), ("log", log_root(entry))):
        resolved = target / root
        if resolved.is_dir():
            continue                                # using an existing dir — no duplication
        leaf = Path(root).name
        sibling = target / leaf                     # e.g. root-level backlog/ or log/
        if sibling != resolved and sibling.is_dir() and any(sibling.iterdir()):
            notes.append(
                f"{label}: configured path '{root}/' does not exist, but a populated "
                f"'{sibling.relative_to(target)}/' does — set {label}_root in "
                f"projects.yaml to reuse it, or accept a new '{root}/'."
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

    for d in build_dirs(entry):
        dest = target / d
        if not dest.is_dir():
            report.act("mkdir", d)
            if args.apply:
                dest.mkdir(parents=True, exist_ok=True)

    for src_rel, dst_rel in build_manifest(entry).items():
        src = TEMPLATES_DIR / src_rel
        dst = target / dst_rel
        if not src.is_file():
            report.skip(dst_rel, f"template missing: templates/{src_rel}")
            continue
        content = substitute(src.read_text(encoding="utf-8"), name, entry)
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
    for note in structure_advisories(entry, target):
        print(f"  ADVISORY: {note}")
    if args.apply:
        print("NOTE: update projects.yaml brain: field for this target (operator-approved edit).")
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
