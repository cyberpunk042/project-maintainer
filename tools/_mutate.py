"""Shared guard framework for every MUTATING verb (Hard Rules 3, 4, 8).

Contract (see .claude/rules/routing.md):
  - dry-run by default; --apply required to write
  - refuse dirty targets unless --allow-dirty
  - refuse registry projects marked writable: false
  - report every action: WOULD / DID / SKIP — silent skips are bugs
"""
from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from tools.registry import Project


def add_mutation_args(ap: argparse.ArgumentParser) -> None:
    ap.add_argument("--target", help="path to a project checkout")
    ap.add_argument("--project", help="registry name from projects.yaml")
    ap.add_argument("--apply", action="store_true", help="actually write (default: dry-run)")
    ap.add_argument("--allow-dirty", action="store_true",
                    help="proceed even if the target has uncommitted changes (logged)")


def git_dirty(target: Path) -> bool:
    try:
        out = subprocess.run(
            ["git", "-C", str(target), "status", "--porcelain"],
            capture_output=True, text=True, timeout=30,
        )
        return out.returncode == 0 and bool(out.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        return False  # not a git repo / git unavailable -> dirty-check not applicable


def guard(target: Path, entry: Project | None, apply: bool, allow_dirty: bool) -> None:
    """Raise SystemExit if mutation is not permitted. No-op for dry-runs."""
    if entry is not None and not entry.writable:
        raise SystemExit(
            f"BLOCKED: '{entry.name}' is marked writable: false in projects.yaml. "
            f"REASON: AGENTS.md Hard Rule 6 (e.g. the second-brain is read-only from here). "
            f"INSTEAD: run audit, or change the registry entry with operator approval."
        )
    if not apply:
        return
    if git_dirty(target) and not allow_dirty:
        raise SystemExit(
            f"BLOCKED: target {target} has uncommitted changes. "
            f"REASON: Hard Rule 4 — never mutate a dirty target. "
            f"INSTEAD: commit/stash in the target first, or re-run with --allow-dirty (logged)."
        )
    if allow_dirty:
        print(f"NOTE: --allow-dirty on {target} (operator-visible per Hard Rule 4)")


@dataclass
class ChangeReport:
    apply: bool
    actions: list[str] = field(default_factory=list)
    skips: list[str] = field(default_factory=list)

    def act(self, action: str, path: Path | str, detail: str = "") -> None:
        verb = "DID" if self.apply else "WOULD"
        self.actions.append(f"  {verb} {action} {path}" + (f" — {detail}" if detail else ""))

    def skip(self, path: Path | str, reason: str) -> None:
        self.skips.append(f"  SKIP {path}: {reason}")

    def print(self, title: str) -> int:
        print(title + (" [APPLY]" if self.apply else " [dry-run]"))
        for line in self.actions:
            print(line)
        for line in self.skips:
            print(line)
        n = len(self.actions)
        print(f"  {n} change(s){' applied' if self.apply else ' would be applied (use --apply)'}"
              f", {len(self.skips)} skip(s)")
        return 0
