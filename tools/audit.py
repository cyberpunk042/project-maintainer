"""pm audit — read-only scan of a target's docs/wiki for maintenance findings.

Base check classes (M001 scope; extend per-finding in M002):
  junk            .DS_Store, Thumbs.db, *.orig, *.rej, .*.swp, ~ backups
  conflict        unresolved git merge-conflict markers in text files
  empty           zero-byte or whitespace-only markdown files
  broken-link     relative markdown links pointing at missing files
  frontmatter     wiki pages (under a declared wiki root) missing YAML frontmatter
  trailing-ws     trailing whitespace in markdown files (informational)

Read-only by design: audit NEVER writes to the target.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from tools.registry import Project, resolve_target

JUNK_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
JUNK_SUFFIXES = (".orig", ".rej", ".swp", ".swo", "~")
SKIP_DIRS = {".git", "node_modules", "target", ".venv", "venv", "__pycache__", "dist", "build", ".pm"}
CONFLICT_RE = re.compile(r"^(<{7} |={7}$|>{7} )", re.MULTILINE)
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)#?\s]+)(?:[#?][^)]*)?\)")


@dataclass
class Finding:
    check: str
    path: str
    detail: str = ""

    def line(self) -> str:
        return f"  [{self.check:<11}] {self.path}" + (f" — {self.detail}" if self.detail else "")


def iter_files(root: Path):
    for p in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        if p.is_file():
            yield p


def doc_roots(target: Path, entry: Project | None) -> list[Path]:
    """Documentation roots to scan: registry-declared, else conventional."""
    candidates = entry.docs if entry and entry.docs else ["docs", "wiki", "backlog"]
    roots = [target / c for c in candidates if (target / c).is_dir()]
    return roots or [target]


def audit_target(target: Path, entry: Project | None, checks: set[str] | None = None) -> list[Finding]:
    findings: list[Finding] = []
    wiki_root = (target / entry.wiki) if entry and entry.wiki else None
    enabled = lambda c: checks is None or c in checks  # noqa: E731

    for root in doc_roots(target, entry):
        for f in iter_files(root):
            rel = str(f.relative_to(target))
            if enabled("junk") and (f.name in JUNK_NAMES or f.name.endswith(JUNK_SUFFIXES)):
                findings.append(Finding("junk", rel))
                continue
            if f.suffix.lower() not in (".md", ".markdown", ".txt", ".yaml", ".yml", ".toml", ".json"):
                continue
            try:
                text = f.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if enabled("conflict") and CONFLICT_RE.search(text):
                findings.append(Finding("conflict", rel, "unresolved merge-conflict markers"))
            if f.suffix.lower() in (".md", ".markdown"):
                if enabled("empty") and not text.strip():
                    findings.append(Finding("empty", rel))
                    continue
                if enabled("broken-link"):
                    for m in LINK_RE.finditer(text):
                        href = m.group(1)
                        if "://" in href or href.startswith(("mailto:", "/", "<")):
                            continue
                        if not (f.parent / href).exists():
                            findings.append(Finding("broken-link", rel, f"-> {href}"))
                if enabled("frontmatter") and wiki_root and f.is_relative_to(wiki_root):
                    if not text.startswith("---"):
                        findings.append(Finding("frontmatter", rel, "no YAML frontmatter"))
                if enabled("trailing-ws") and re.search(r"[ \t]+$", text, re.MULTILINE):
                    findings.append(Finding("trailing-ws", rel))
    return findings


def print_report(target: Path, findings: list[Finding]) -> None:
    print(f"AUDIT {target}")
    if not findings:
        print("  clean — 0 findings")
        return
    by_check: dict[str, int] = {}
    for fi in findings:
        by_check[fi.check] = by_check.get(fi.check, 0) + 1
        print(fi.line())
    summary = ", ".join(f"{k}={v}" for k, v in sorted(by_check.items()))
    print(f"  TOTAL {len(findings)} finding(s): {summary}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="pm audit", description=__doc__)
    ap.add_argument("--target", help="path to a project checkout")
    ap.add_argument("--project", help="registry name from projects.yaml")
    ap.add_argument("--checks", help="comma-separated subset of checks to run")
    args = ap.parse_args(argv)
    target, entry = resolve_target(args.target, args.project)
    checks = set(args.checks.split(",")) if args.checks else None
    findings = audit_target(target, entry, checks)
    print_report(target, findings)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
