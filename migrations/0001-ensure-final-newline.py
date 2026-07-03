"""0001-ensure-final-newline — ensure every markdown file ends with exactly one newline.

Safe, idempotent structural normalization: a POSIX text file should end with a
single newline. plan() lists offenders; apply() fixes them. Re-running is a no-op.

This is the reference migration — copy its shape for real restructures
(see migrations/README.md for the contract).
"""
from __future__ import annotations

from pathlib import Path

DESCRIPTION = "Ensure every markdown file ends with exactly one trailing newline"

SKIP_DIRS = {".git", "node_modules", "target", ".venv", "venv", "__pycache__", ".pm"}


def _md_files(target: Path):
    for p in sorted(target.rglob("*.md")):
        if any(part in SKIP_DIRS for part in p.relative_to(target).parts):
            continue
        if p.is_file():
            yield p


def _needs_fix(text: str) -> bool:
    return text != "" and (not text.endswith("\n") or text.endswith("\n\n"))


def _normalized(text: str) -> str:
    return text.rstrip("\n") + "\n" if text.strip() else text


def plan(target: Path) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for f in _md_files(target):
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if _needs_fix(text):
            reason = "no final newline" if not text.endswith("\n") else "multiple trailing newlines"
            rows.append(("normalize final newline", str(f.relative_to(target)), reason))
    return rows


def apply(target: Path) -> None:
    for f in _md_files(target):
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if _needs_fix(text):
            f.write_text(_normalized(text), encoding="utf-8")
