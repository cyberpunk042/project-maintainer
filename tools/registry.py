"""projects.yaml registry loader.

Uses PyYAML when available; falls back to a minimal parser that handles
the constrained schema this registry actually uses (nested mappings,
scalar values, inline [a, b] lists, comments). Zero hard dependencies.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

from tools._paths import REGISTRY_FILE, expand


@dataclass
class Project:
    name: str
    path: str = ""
    remote: str = ""
    docs: list[str] = field(default_factory=list)
    wiki: str = ""
    brain: str = "none"
    writable: bool = False
    language_policy: str = "flag-only"
    frontmatter_exempt: list[str] = field(default_factory=list)
    # Where the epic>module>task backlog and the verbatim operator-directive log
    # live IN THIS TARGET. The adoption guide makes these paths per-project
    # ("if your backlog lives at a different path, update all references"); only
    # the hierarchy is sacrosanct, not the wiki/ prefix. Empty -> the ecosystem
    # default (wiki/backlog, wiki/log), resolved by tools.implant.
    backlog_root: str = ""
    log_root: str = ""
    notes: str = ""

    def resolved_path(self) -> Path:
        """Resolve `~/name` per registry convention; fall back to a sibling
        checkout of this repo (covers environments where HOME differs from
        the operator's machine, e.g. remote containers)."""
        p = expand(self.path)
        if not p.is_dir() and self.path:
            from tools._paths import REPO_ROOT

            sibling = REPO_ROOT.parent / Path(self.path).name
            if sibling.is_dir():
                return sibling
        return p

    def exists_locally(self) -> bool:
        return self.resolved_path().is_dir()


def _parse_scalar(raw: str):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        return [x.strip().strip("'\"") for x in inner.split(",")] if inner else []
    if raw in ("true", "True"):
        return True
    if raw in ("false", "False"):
        return False
    return raw.strip("'\"")


def _fallback_parse(text: str) -> dict:
    """Minimal YAML-subset parser: `projects:` → name → key: value."""
    projects: dict[str, dict] = {}
    current: dict | None = None
    in_projects = False
    for line in text.splitlines():
        stripped = line.split("#", 1)[0].rstrip() if not line.lstrip().startswith("#") else ""
        if not stripped.strip():
            continue
        indent = len(stripped) - len(stripped.lstrip())
        content = stripped.strip()
        if indent == 0:
            in_projects = content == "projects:"
            current = None
            continue
        if not in_projects or ":" not in content:
            continue
        key, _, value = content.partition(":")
        if indent == 2 and not value.strip():
            current = {}
            projects[key.strip()] = current
        elif indent >= 4 and current is not None:
            current[key.strip()] = _parse_scalar(value)
    return {"projects": projects}


def load_registry(registry_file: Path = REGISTRY_FILE) -> dict[str, Project]:
    text = registry_file.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text) or {}
    except ImportError:
        data = _fallback_parse(text)
    result: dict[str, Project] = {}
    for name, fields in (data.get("projects") or {}).items():
        fields = fields or {}
        result[name] = Project(
            name=name,
            path=str(fields.get("path", "")),
            remote=str(fields.get("remote", "")),
            docs=list(fields.get("docs", []) or []),
            wiki=str(fields.get("wiki", "") or ""),
            brain=str(fields.get("brain", "none")),
            writable=bool(fields.get("writable", False)),
            language_policy=str(fields.get("language_policy", "flag-only") or "flag-only"),
            frontmatter_exempt=list(fields.get("frontmatter_exempt", []) or []),
            backlog_root=str(fields.get("backlog_root", "") or ""),
            log_root=str(fields.get("log_root", "") or ""),
            notes=str(fields.get("notes", "")),
        )
    return result


def resolve_target(target: str | None, project: str | None) -> tuple[Path, Project | None]:
    """Resolve --target/--project selection to (path, registry entry or None)."""
    if target and project:
        raise SystemExit("ERROR: use --target OR --project, not both")
    if project:
        reg = load_registry()
        if project not in reg:
            raise SystemExit(
                f"ERROR: project '{project}' not in registry. Known: {', '.join(sorted(reg))}"
            )
        entry = reg[project]
        path = entry.resolved_path()
        if not path.is_dir():
            raise SystemExit(f"ERROR: registry path for '{project}' not found locally: {path}")
        return path, entry
    if target:
        path = expand(target)
        if not path.is_dir():
            raise SystemExit(f"ERROR: target path not found: {path}")
        # If the path matches a registry entry, attach its metadata.
        for entry in load_registry().values():
            try:
                if entry.resolved_path() == path:
                    return path, entry
            except Exception:
                continue
        return path, None
    raise SystemExit("ERROR: a target is required (--target <path> or --project <name>)")


def main(argv: list[str]) -> int:
    action = argv[0] if argv else "list"
    reg = load_registry()
    if action == "list":
        print(f"{len(reg)} project(s) in registry ({REGISTRY_FILE}):\n")
        for p in reg.values():
            local = "local" if p.exists_locally() else "NOT CLONED"
            rw = "writable" if p.writable else "READ-ONLY"
            print(f"  {p.name:<28} {p.path:<38} brain={p.brain:<10} {rw:<10} "
                  f"lang={p.language_policy:<12} [{local}]")
            if p.notes:
                print(f"  {'':<28} {p.notes}")
        return 0
    if action == "show" and len(argv) > 1:
        p = reg.get(argv[1])
        if not p:
            print(f"ERROR: unknown project '{argv[1]}'", file=sys.stderr)
            return 1
        for k, v in vars(p).items():
            print(f"  {k}: {v}")
        return 0
    print("usage: pm registry [list | show <name>]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
