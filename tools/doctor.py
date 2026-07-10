"""pm doctor — read-only target CI/health baseline.

Detects the target's CI workflow(s), extracts the check commands the CI actually
runs, and re-runs the SAFE, STATIC ones locally (linters / type-checkers /
format --check) to report a baseline: GREEN / RED / UNKNOWN.

Why this exists: project-maintainer opens PRs into targets. If a target's CI is
ALREADY red (its own lint/test debt), a maintenance PR will show a red check the
change didn't cause. Doctor establishes that baseline BEFORE a mutation/PR, so a
red gate is surfaced as maintenance signal instead of an after-the-fact surprise.

Safety: only static, read-only checks are executed (they parse code, they don't
run it or modify files). Test suites (`pytest`, `cargo test`, `npm test`) and
format-in-place commands (`black` without `--check`) are DETECTED and listed but
NOT run — pass --tests to also run detected test suites.
"""
from __future__ import annotations

import argparse
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from tools.registry import resolve_target

WORKFLOW_GLOBS = (".github/workflows/*.yml", ".github/workflows/*.yaml")

STATIC_LINTERS = {"ruff", "flake8", "pyflakes", "pycodestyle", "pylint", "mypy", "pyright", "vulture"}
# Sub-second linters — safe to run as an inline mutation pre-flight. The rest
# (mypy, pyright, pylint, cargo clippy/check) can compile/type-check a whole
# codebase and are only run by the explicit `doctor` verb.
FAST_TOOLS = {"ruff", "flake8", "pyflakes", "pycodestyle", "black", "isort"}
FORMAT_CHECKERS = {"black", "isort", "yapf"}          # read-only ONLY with --check/--diff
TEST_RUNNERS = {"pytest", "tox", "nox"}
FORMAT_READONLY_FLAGS = {"--check", "--check-only", "--diff"}
# command first-tokens that are setup/noise, never a check
SKIP_TOKENS = {"pip", "pip3", "poetry", "uv", "apt", "apt-get", "sudo", "echo", "cd",
               "export", "curl", "wget", "make", "bash", "sh", "cp", "mv", "mkdir", "git"}

Kind = str  # 'static' | 'test' | 'modify' | 'skip'


@dataclass
class Check:
    command: str
    tool: str
    kind: Kind
    # populated when run:
    ran: bool = False
    passed: bool = False
    rc: int | None = None
    summary: str = ""


def find_workflows(target: Path) -> list[Path]:
    found: list[Path] = []
    for pat in WORKFLOW_GLOBS:
        found.extend(sorted(target.glob(pat)))
    return found


def extract_run_commands(yml_text: str) -> list[str]:
    """Pull the shell commands out of every `run:` step (inline + block scalar)."""
    cmds: list[str] = []
    lines = yml_text.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^(\s*)(?:-\s*)?run:\s*(.*)$", lines[i])
        if not m:
            i += 1
            continue
        indent, rest = len(m.group(1)), m.group(2).strip()
        if rest in ("|", ">", "|-", ">-", "|+", ">+", ""):   # block scalar
            j = i + 1
            while j < len(lines):
                bl = lines[j]
                if not bl.strip():
                    j += 1
                    continue
                if len(bl) - len(bl.lstrip()) <= indent:
                    break
                cmds.append(bl.strip())
                j += 1
            i = j
        else:
            cmds.append(rest)
            i += 1
    return cmds


def _tool_of(tokens: list[str]) -> str:
    """Resolve the effective tool name, unwrapping `python -m <tool>`."""
    if tokens and tokens[0] in ("python", "python3") and len(tokens) > 2 and tokens[1] == "-m":
        return tokens[2]
    return tokens[0] if tokens else ""


def classify(command: str) -> Check:
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()
    if not tokens:
        return Check(command, "", "skip")
    tool = _tool_of(tokens)
    rest = tokens[tokens.index(tool) + 1:] if tool in tokens else tokens[1:]

    if tool in SKIP_TOKENS:
        return Check(command, tool, "skip")
    if tool == "cargo":
        sub = rest[0] if rest else ""
        if sub in ("clippy", "check"):
            return Check(command, "cargo", "static")
        if sub == "fmt":
            return Check(command, "cargo", "static" if "--check" in rest else "modify")
        if sub == "test":
            return Check(command, "cargo", "test")
        return Check(command, "cargo", "skip")
    if tool in ("npm", "pnpm", "yarn"):
        joined = " ".join(rest)
        if "test" in rest or "lint" in joined:
            return Check(command, tool, "test")     # runs project scripts — defer to --tests
        return Check(command, tool, "skip")
    if tool == "ruff":
        # `ruff check` is read-only; `ruff format` rewrites files
        return Check(command, "ruff", "static" if (rest and rest[0] == "check") else
                     ("modify" if rest and rest[0] == "format" else "static"))
    if tool in STATIC_LINTERS:
        return Check(command, tool, "static")
    if tool in FORMAT_CHECKERS:
        readonly = any(f in rest for f in FORMAT_READONLY_FLAGS)
        return Check(command, tool, "static" if readonly else "modify")
    if tool in TEST_RUNNERS:
        return Check(command, tool, "test")
    return Check(command, tool, "skip")


def _summarize(output: str) -> str:
    m = re.search(r"[Ff]ound (\d+) error", output) or re.search(r"(\d+) errors?\b", output)
    if m:
        return f"{m.group(1)} error(s)"
    for line in reversed(output.splitlines()):
        if line.strip():
            return line.strip()[:120]
    return ""


def run_check(check: Check, target: Path, timeout: int = 180) -> Check:
    tool = check.tool
    if not shutil.which(tool):
        check.summary = f"{tool} not installed locally — cannot verify"
        return check
    try:
        proc = subprocess.run(shlex.split(check.command), cwd=str(target),
                              capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired, ValueError) as e:
        check.summary = f"could not run: {e}"
        return check
    check.ran = True
    check.rc = proc.returncode
    check.passed = proc.returncode == 0
    check.summary = _summarize((proc.stdout or "") + "\n" + (proc.stderr or ""))
    return check


def baseline(target: Path, run_tests: bool = False, fast: bool = False) -> dict:
    """Detect + run the target's static CI checks. Returns a structured baseline.
    fast=True runs only sub-second linters (for the inline mutation pre-flight)."""
    workflows = find_workflows(target)
    commands: list[str] = []
    for wf in workflows:
        try:
            commands.extend(extract_run_commands(wf.read_text(encoding="utf-8")))
        except OSError:
            continue
    # split on && / ; into individual commands, dedupe preserving order
    parts: list[str] = []
    for c in commands:
        for piece in re.split(r"&&|;", c):
            piece = piece.strip()
            if piece and piece not in parts:
                parts.append(piece)
    checks = [classify(p) for p in parts]

    for chk in checks:
        if fast and chk.tool not in FAST_TOOLS:
            continue
        if chk.kind == "static" or (chk.kind == "test" and run_tests):
            run_check(chk, target)
    return {"status": derive_status(workflows, checks), "workflows": workflows, "checks": checks}


def derive_status(workflows: list, checks: list[Check]) -> str:
    if not workflows:
        return "no-ci"
    if any(c.ran and not c.passed for c in checks):
        return "red"
    if any(c.ran for c in checks):
        return "green"
    return "unknown"


def preflight_advisory(target: Path) -> list[str]:
    """One-liner(s) for the mutation pre-flight: only speak up when the target's
    CI baseline is already RED (a PR would show red regardless of our change),
    or UNKNOWN because a check couldn't be verified locally. Static checks only —
    fast, no test suites. Silent on green / no-CI."""
    result = baseline(target, run_tests=False, fast=True)
    if result["status"] == "red":
        fails = [f"{c.tool} (`{c.command}`): {c.summary}" for c in result["checks"] if c.ran and not c.passed]
        return [f"target CI baseline is RED before this change — a PR will show red "
                f"independent of it: {'; '.join(fails)}. Run `pm doctor` for detail."]
    return []


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="pm doctor", description=__doc__)
    ap.add_argument("--target", help="path to a project checkout")
    ap.add_argument("--project", help="registry name from projects.yaml")
    ap.add_argument("--tests", action="store_true", help="also run detected test suites (heavier)")
    args = ap.parse_args(argv)
    target, _ = resolve_target(args.target, args.project)
    result = baseline(target, run_tests=args.tests)

    print(f"DOCTOR {target}")
    wfs = result["workflows"]
    if not wfs:
        print("  no CI workflow detected (.github/workflows/*.yml) — nothing to verify")
        return 0
    print(f"  CI: {len(wfs)} workflow(s) — {', '.join(str(w.relative_to(target)) for w in wfs)}")
    for c in result["checks"]:
        if c.ran:
            tag = "PASS" if c.passed else "FAIL"
            detail = f" — exit {c.rc}: {c.summary}" if not c.passed else ""
            print(f"  [{tag}] {c.command}{detail}")
        elif c.kind == "test":
            print(f"  [defer] {c.command} (test suite — run with --tests)")
        elif c.kind == "modify":
            print(f"  [skip] {c.command} (would modify files — not a read-only check)")
        elif c.kind == "static":
            print(f"  [skip] {c.command} ({c.summary or 'not runnable locally'})")
    status = result["status"]
    labels = {"green": "GREEN — all runnable checks pass",
              "red": "RED — a check is failing",
              "unknown": "UNKNOWN — no check could be run locally",
              "no-ci": "no CI"}
    print(f"  BASELINE: {labels.get(status, status)}")
    return 1 if status == "red" else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
