"""pm migrate — versioned, idempotent migrations against a target.

Migrations live at migrations/NNNN-<slug>.py, each exposing:
    DESCRIPTION: str
    def plan(target: Path) -> list[tuple[str, str, str]]   # (action, path, detail)
    def apply(target: Path) -> None

Applied migrations are recorded in the TARGET at .pm/migrations.applied
(one id per line) — the only bookkeeping we keep inside targets.

Status: SCAFFOLD (M004). Runner + state format are real; first migrations
are authored per-need with operator approval (they restructure targets).
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

from tools._mutate import ChangeReport, add_mutation_args, guard
from tools._paths import APPLIED_MIGRATIONS_FILE, MIGRATIONS_DIR, TARGET_STATE_DIR
from tools.registry import resolve_target


def discover() -> dict[str, Path]:
    return {p.stem: p for p in sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9][0-9]-*.py"))}


def applied_ids(target: Path) -> set[str]:
    f = target / TARGET_STATE_DIR / APPLIED_MIGRATIONS_FILE
    return set(f.read_text(encoding="utf-8").split()) if f.is_file() else set()


def record_applied(target: Path, mig_id: str) -> None:
    d = target / TARGET_STATE_DIR
    d.mkdir(exist_ok=True)
    f = d / APPLIED_MIGRATIONS_FILE
    ids = applied_ids(target) | {mig_id}
    f.write_text("\n".join(sorted(ids)) + "\n", encoding="utf-8")


def load_migration(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="pm migrate", description=__doc__)
    add_mutation_args(ap)
    ap.add_argument("--list", action="store_true", help="list migrations + applied state")
    ap.add_argument("--id", help="run a single migration by id (e.g. 0001-example)")
    args = ap.parse_args(argv)

    migrations = discover()
    if args.list and not (args.target or args.project):
        print(f"{len(migrations)} migration(s) in {MIGRATIONS_DIR}:")
        for mig_id in migrations:
            print(f"  {mig_id}")
        return 0

    target, entry = resolve_target(args.target, args.project)
    done = applied_ids(target)

    if args.list:
        print(f"MIGRATIONS vs {target}:")
        for mig_id in migrations:
            print(f"  [{'applied' if mig_id in done else 'pending'}] {mig_id}")
        return 0

    guard(target, entry, args.apply, args.allow_dirty)
    to_run = [args.id] if args.id else [m for m in migrations if m not in done]
    report = ChangeReport(apply=args.apply)
    for mig_id in to_run:
        if mig_id not in migrations:
            raise SystemExit(f"ERROR: unknown migration '{mig_id}'")
        if mig_id in done:
            report.skip(mig_id, "already applied (idempotency)")
            continue
        mod = load_migration(migrations[mig_id])
        for action, path, detail in mod.plan(target):
            report.act(f"{mig_id}: {action}", path, detail)
        if args.apply:
            mod.apply(target)
            record_applied(target, mig_id)
    return report.print(f"MIGRATE {target}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
