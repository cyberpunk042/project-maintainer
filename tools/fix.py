"""pm fix — targeted corrections that need more than mechanical cleaning.

Implemented fixers:
  links      repair a broken relative markdown link when EXACTLY ONE file with
             that basename exists in the target. Ambiguous (0 or >1 matches)
             links are reported, never guessed. Cross-repo links left alone.
  wikilinks  convert a broken relative markdown link to a moved .md note into an
             Obsidian wikilink `[[stem|display]]` (dynamic, resolves by name so
             it survives future moves). For vaults whose convention is wikilinks
             — the move-resilient fix, not another hardcoded relative path.
             Only unique-match .md notes; ambiguous/non-note links untouched.

Planned (per recurring audit finding): frontmatter repair, _index.md regen.

Dry-run by default; --apply to write; --diff to preview. Guard-protected
(dirty-target refusal, writable gating). Conservative: only unambiguous fixes.
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

from tools.audit import LINK_RE, SKIP_DIRS, doc_roots, iter_files
from tools._mutate import ChangeReport, add_mutation_args, guard
from tools.registry import load_registry, resolve_target

# [display](target) capturing the FULL target incl any #anchor/?query, so the
# wikilink fixer can detect (and skip) anchor-bearing links rather than drop them.
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")


def _sibling_names() -> set[str]:
    try:
        return {Path(p.path).name for p in load_registry().values() if p.path}
    except OSError:
        return set()


def _basename_index(target: Path) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for p in target.rglob("*"):
        if p.is_file() and not (set(p.relative_to(target).parts) & SKIP_DIRS):
            index.setdefault(p.name, []).append(p)
    return index


def _stem_index(target: Path) -> dict[str, list[Path]]:
    """Index .md notes by stem (filename without extension) for wikilink resolution."""
    index: dict[str, list[Path]] = {}
    for p in target.rglob("*.md"):
        if not (set(p.relative_to(target).parts) & SKIP_DIRS):
            index.setdefault(p.stem, []).append(p)
    return index


def _print_diff(rel, before: str, after: str) -> None:
    for line in difflib.unified_diff(before.splitlines(keepends=True),
                                     after.splitlines(keepends=True),
                                     fromfile=f"a/{rel}", tofile=f"b/{rel}"):
        print("    " + line.rstrip("\n"))


def fix_links(target, entry, report: ChangeReport, show_diff: bool) -> None:
    siblings = _sibling_names()
    index = _basename_index(target)
    for root in doc_roots(target, entry):
        for f in iter_files(root):
            if f.suffix.lower() not in (".md", ".markdown"):
                continue
            try:
                text = f.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            rel = f.relative_to(target)
            new_text = text
            for m in LINK_RE.finditer(text):
                href = m.group(1)
                if "://" in href or href.startswith(("mailto:", "/", "<")):
                    continue
                if (f.parent / href).exists():
                    continue
                if siblings & set(Path(href).parts):
                    continue  # cross-repo — leave alone
                candidates = index.get(Path(href).name, [])
                if len(candidates) == 1:
                    new_href = _relpath(f.parent, candidates[0])
                    new_text = new_text.replace(f"]({href})", f"]({new_href})")
                    report.act("fix link", rel, f"{href} -> {new_href}")
                else:
                    report.skip(rel, f"link '{href}' not auto-fixable "
                                     f"({len(candidates)} candidate(s) named {Path(href).name})")
            if new_text != text:
                if show_diff:
                    _print_diff(rel, text, new_text)
                if report.apply:
                    f.write_text(new_text, encoding="utf-8")


def _relpath(from_dir: Path, to_file: Path) -> str:
    import os

    return os.path.relpath(to_file, from_dir).replace("\\", "/")


def fix_wikilinks(target, entry, report: ChangeReport, show_diff: bool) -> None:
    """Convert a broken relative markdown link to a moved .md note into an
    Obsidian wikilink `[[stem|display]]` (dynamic — survives future moves)."""
    siblings = _sibling_names()
    stems = _stem_index(target)
    for root in doc_roots(target, entry):
        for f in iter_files(root):
            if f.suffix.lower() not in (".md", ".markdown"):
                continue
            try:
                text = f.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            rel = f.relative_to(target)
            new_text = text
            for m in MD_LINK_RE.finditer(text):
                display, tgt = m.group(1), m.group(2)
                if "://" in tgt or tgt.startswith(("mailto:", "/", "<")):
                    continue
                if "#" in tgt or "?" in tgt:
                    # anchor/query-bearing: markdown slug != Obsidian heading;
                    # don't risk corrupting it — leave for manual review.
                    href = tgt.split("#", 1)[0].split("?", 1)[0]
                    if href and Path(href).suffix.lower() == ".md" and not (f.parent / href).exists():
                        report.skip(rel, f"link '{tgt}' has an anchor/query — not auto-converted")
                    continue
                href = tgt
                if Path(href).suffix.lower() != ".md":
                    continue  # only note links become wikilinks
                if (f.parent / href).exists():
                    continue  # not broken — leave working links alone
                if siblings & set(Path(href).parts):
                    continue  # cross-repo
                stem = Path(href).stem
                candidates = stems.get(stem, [])
                if len(candidates) == 1:
                    wl = f"[[{stem}]]" if display.strip() == stem else f"[[{stem}|{display}]]"
                    new_text = new_text.replace(m.group(0), wl)
                    report.act("wikilink", rel, f"{m.group(0)} -> {wl}")
                else:
                    report.skip(rel, f"link '{href}' not convertible "
                                     f"({len(candidates)} note(s) named {stem})")
            if new_text != text:
                if show_diff:
                    _print_diff(rel, text, new_text)
                if report.apply:
                    f.write_text(new_text, encoding="utf-8")


FIXERS = {"links": fix_links, "wikilinks": fix_wikilinks}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="pm fix", description=__doc__)
    add_mutation_args(ap)
    ap.add_argument("--fixers", default="links",
                    help=f"comma-separated fixers to run (available: {', '.join(FIXERS)})")
    ap.add_argument("--diff", action="store_true", help="print a unified diff of each change")
    args = ap.parse_args(argv)
    target, entry = resolve_target(args.target, args.project)
    guard(target, entry, args.apply, args.allow_dirty, getattr(args, 'force_write', False))
    report = ChangeReport(apply=args.apply)
    for name in args.fixers.split(","):
        fixer = FIXERS.get(name.strip())
        if fixer is None:
            report.skip(target, f"unknown fixer '{name.strip()}' (available: {', '.join(FIXERS)})")
        else:
            fixer(target, entry, report, args.diff)
    return report.print(f"FIX {target}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
