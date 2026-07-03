"""Shared path resolution for project-maintainer tools."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_FILE = REPO_ROOT / "projects.yaml"
TEMPLATES_DIR = REPO_ROOT / "templates"
MIGRATIONS_DIR = REPO_ROOT / "migrations"

# Bookkeeping directory created inside targets (the ONLY thing of ours
# that lives in a target — see .claude/rules/self-reference.md).
TARGET_STATE_DIR = ".pm"
APPLIED_MIGRATIONS_FILE = "migrations.applied"


def expand(path: str) -> Path:
    return Path(path).expanduser().resolve()
