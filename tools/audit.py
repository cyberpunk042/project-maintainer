"""pm audit — read-only scan of a target's docs/wiki for maintenance findings.

Base check classes (M001 scope; extend per-finding in M002):
  junk            .DS_Store, Thumbs.db, *.orig, *.rej, .*.swp, ~ backups
  conflict        unresolved git merge-conflict markers in text files
  empty           zero-byte or whitespace-only markdown files
  broken-link     relative markdown links pointing at missing files IN THIS repo
  cross-repo      relative links into a sibling registry project (informational;
                  can't be verified from here — NOT counted as broken)
  frontmatter     wiki pages missing YAML frontmatter (nav files + log dirs +
                  per-project frontmatter_exempt are excused)
  trailing-ws     trailing whitespace in markdown files (informational)
  slur            targeted-hate / demeaning terms (per-project language policy)
  vulgar          stylistic profanity (per-project language policy)

Language checks (slur/vulgar) are gated by the target's `language_policy`
(projects.yaml): preserve suppresses vulgar, preserve-all suppresses both,
flag-only/clean flag both. Unknown targets default to flag-only (don't assume
intent). Override for one run with --language-policy.

Read-only by design: audit NEVER writes to the target.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from tools.language import DEFAULT_POLICY, load_config, scan, tiers_for_policy
from tools.registry import Project, load_registry, resolve_target

def clean_trailing_ws(text: str) -> str:
    """Strip trailing whitespace, but PRESERVE Markdown hard line breaks.

    A line of non-blank content ending in >=2 spaces is a CommonMark hard line
    break (renders as <br>); stripping it silently collapses two visually-separate
    lines into one. So a trailing-whitespace cleaner MUST leave those alone.
    We strip: whitespace-only lines (fully), and content lines ending in a single
    trailing space or trailing tab(s). CRLF line endings are preserved."""
    out: list[str] = []
    for line in text.splitlines(keepends=True):
        nl = ""
        if line.endswith("\r\n"):
            body, nl = line[:-2], "\r\n"
        elif line.endswith(("\n", "\r")):
            body, nl = line[:-1], line[-1]
        else:
            body = line
        if body.strip() == "":
            body = ""                              # dead whitespace-only line
        elif re.search(r"\S {2,}\Z", body):
            pass                                    # markdown hard break — keep
        else:
            body = re.sub(r"[ \t]+\Z", "", body)   # single-space / tab — strip
        out.append(body + nl)
    return "".join(out)


def has_cleanable_trailing_ws(text: str) -> bool:
    return clean_trailing_ws(text) != text


JUNK_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
JUNK_SUFFIXES = (".orig", ".rej", ".swp", ".swo", "~")
SKIP_DIRS = {".git", "node_modules", "target", ".venv", "venv", "__pycache__", "dist", "build", ".pm"}
CONFLICT_RE = re.compile(r"^(<{7} |={7}$|>{7} )", re.MULTILINE)
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)#?\s]+)(?:[#?][^)]*)?\)")

# frontmatter check exemptions — navigation/readme files and chronological log
# entries legitimately carry no frontmatter. Extend per-project via projects.yaml
# `frontmatter_exempt` (list of path substrings).
FRONTMATTER_EXEMPT_NAMES = {"_index.md", "index.md", "readme.md"}
FRONTMATTER_EXEMPT_DIRS = {"log", "logs"}


def _sibling_names() -> set[str]:
    """Directory names of registry projects — used to recognize cross-repo links."""
    names: set[str] = set()
    try:
        for p in load_registry().values():
            if p.path:
                names.add(Path(p.path).name)
    except OSError:
        pass
    return names


def _frontmatter_exempt(rel: str, name: str, extra: list[str]) -> bool:
    if name.lower() in FRONTMATTER_EXEMPT_NAMES:
        return True
    parts = {p.lower() for p in Path(rel).parts}
    if parts & FRONTMATTER_EXEMPT_DIRS:
        return True
    return any(sub and sub in rel for sub in extra)


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
    """Documentation DIRECTORIES to scan: registry-declared, else conventional.

    Kept for callers that only want directory roots. `docs:` entries that name a
    FILE (e.g. a top-level `readme.md`) are handled by iter_doc_files, not here.
    """
    candidates = entry.docs if entry and entry.docs else ["docs", "wiki", "backlog"]
    roots = [target / c for c in candidates if (target / c).is_dir()]
    files = [target / c for c in candidates if (target / c).is_file()]
    # Only fall back to whole-target when NOTHING (dir or file) was declared/found.
    return roots or ([] if files else [target])


def iter_doc_files(target: Path, entry: Project | None):
    """Yield every file to audit/clean/fix, deduped, from the target's configured
    roots. A registry `docs:` entry may be a directory (walked, minus SKIP_DIRS)
    OR a single file (e.g. a top-level `readme.md` a docs/-only scan would miss).
    This is the adaptation that lets non-wiki targets — a Java/Gradle repo whose
    primary doc is a root readme — actually be covered."""
    candidates = entry.docs if entry and entry.docs else ["docs", "wiki", "backlog"]
    file_entries = [target / c for c in candidates if (target / c).is_file()]
    seen: set[Path] = set()
    for root in doc_roots(target, entry):
        for f in iter_files(root):
            if f not in seen:
                seen.add(f)
                yield f
    for f in file_entries:
        if f in seen:
            continue
        if set(f.relative_to(target).parts) & SKIP_DIRS:
            continue
        seen.add(f)
        yield f


def audit_target(target: Path, entry: Project | None, checks: set[str] | None = None,
                 policy_override: str | None = None, siblings: set[str] | None = None) -> list[Finding]:
    findings: list[Finding] = []
    wiki_root = (target / entry.wiki) if entry and entry.wiki else None
    enabled = lambda c: checks is None or c in checks  # noqa: E731

    # Language checks are gated by the target's per-project policy (projects.yaml
    # language_policy). Unknown/undeclared target -> flag-only (don't assume intent).
    # An explicit --language-policy override is operator authorization for this run.
    policy = policy_override or (entry.language_policy if entry else DEFAULT_POLICY)
    lang_tiers = tiers_for_policy(policy, action="flag")
    try:
        lang_cfg = load_config() if lang_tiers else None
    except OSError:
        lang_cfg = None
    siblings = siblings if siblings is not None else _sibling_names()
    fm_exempt = list(getattr(entry, "frontmatter_exempt", []) or [])
    # cross-repo is informational: report only when explicitly requested.
    cross_repo_on = checks is not None and "cross-repo" in checks

    for f in iter_doc_files(target, entry):
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
            if enabled("broken-link") or cross_repo_on:
                for m in LINK_RE.finditer(text):
                    href = m.group(1)
                    if "://" in href or href.startswith(("mailto:", "/", "<")):
                        continue
                    if (f.parent / href).exists():
                        continue
                    # A link into a sibling registry project can't be verified
                    # from here — classify as cross-repo, not broken.
                    if siblings & set(Path(href).parts):
                        if cross_repo_on:
                            findings.append(Finding("cross-repo", rel, f"-> {href}"))
                    elif enabled("broken-link"):
                        findings.append(Finding("broken-link", rel, f"-> {href}"))
            if enabled("frontmatter") and wiki_root and f.is_relative_to(wiki_root):
                if not text.startswith("---") and not _frontmatter_exempt(rel, f.name, fm_exempt):
                    findings.append(Finding("frontmatter", rel, "no YAML frontmatter"))
            if enabled("trailing-ws") and has_cleanable_trailing_ws(text):
                findings.append(Finding("trailing-ws", rel))
            if lang_cfg and f.name != "language.yaml":
                for tier in ("slur", "vulgar"):
                    if tier in lang_tiers and enabled(tier):
                        hits = scan(text, lang_cfg, {tier})
                        if hits:
                            sample = sorted({m.word.lower() for m in hits})[:5]
                            findings.append(Finding(
                                tier, rel,
                                f"{len(hits)}x [{', '.join(sample)}] (policy={policy})"))
    return findings


def counts(findings: list[Finding]) -> dict[str, int]:
    by_check: dict[str, int] = {}
    for fi in findings:
        by_check[fi.check] = by_check.get(fi.check, 0) + 1
    return by_check


def print_report(target: Path, findings: list[Finding]) -> None:
    print(f"AUDIT {target}")
    if not findings:
        print("  clean — 0 findings")
        return
    for fi in findings:
        print(fi.line())
    summary = ", ".join(f"{k}={v}" for k, v in sorted(counts(findings).items()))
    print(f"  TOTAL {len(findings)} finding(s): {summary}")


def as_dict(target: Path, findings: list[Finding]) -> dict:
    return {
        "target": str(target),
        "total": len(findings),
        "counts": counts(findings),
        "findings": [{"check": f.check, "path": f.path, "detail": f.detail} for f in findings],
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="pm audit", description=__doc__)
    ap.add_argument("--target", help="path to a project checkout")
    ap.add_argument("--project", help="registry name from projects.yaml")
    ap.add_argument("--checks", help="comma-separated subset of checks to run")
    ap.add_argument("--language-policy", dest="language_policy",
                    help="override the registry language_policy for this run "
                         "(clean|flag-only|preserve|preserve-all)")
    ap.add_argument("--json", action="store_true", help="emit findings as JSON")
    args = ap.parse_args(argv)
    target, entry = resolve_target(args.target, args.project)
    checks = set(args.checks.split(",")) if args.checks else None
    findings = audit_target(target, entry, checks, policy_override=args.language_policy)
    if args.json:
        import json

        print(json.dumps(as_dict(target, findings), indent=2))
    else:
        print_report(target, findings)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
