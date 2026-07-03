"""Language cleanup engine — detect + redact slurs / vulgar language.

Loads word lists from config/language.yaml (data, not code). Two tiers
(vulgar, slur) so per-project policy can treat them differently. Matching is
whole-word, case-insensitive, on a CURATED variant list — no substring
stemming — to avoid false positives (the Scunthorpe problem).

Per-project policy (from projects.yaml `language_policy`):
  clean        -> flag both tiers; the clean fixer may redact when invoked
  flag-only    -> flag both tiers; fixer REFUSES to act (default for unknown)
  preserve     -> vulgar is intentional: don't flag vulgar; still flag slurs
  preserve-all -> flag nothing (fully intentional / operator-verbatim corpus)

Nothing here writes on its own; redaction is applied by tools/clean.py under
the mutation guard (dry-run default).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from tools._paths import REPO_ROOT

CONFIG_FILE = REPO_ROOT / "config" / "language.yaml"
VALID_POLICIES = {"clean", "flag-only", "preserve", "preserve-all"}
DEFAULT_POLICY = "flag-only"


@dataclass
class LanguageConfig:
    vulgar: list[str]
    slur: list[str]
    replacement: str = "redact"
    placeholder: str = "[redacted]"
    _vulgar_re: re.Pattern | None = None
    _slur_re: re.Pattern | None = None

    def __post_init__(self):
        self._vulgar_re = _compile(self.vulgar)
        self._slur_re = _compile(self.slur)

    def pattern(self, tier: str) -> re.Pattern | None:
        return self._vulgar_re if tier == "vulgar" else self._slur_re


def _compile(words: list[str]) -> re.Pattern | None:
    if not words:
        return None
    alt = "|".join(sorted((re.escape(w) for w in words), key=len, reverse=True))
    return re.compile(rf"\b(?:{alt})\b", re.IGNORECASE)


def _tiny_yaml_lists(text: str) -> dict:
    """Minimal parser for the constrained config shape: top-level `key:` with
    either a scalar value or a block sequence of `- item` lines. Stdlib-only
    fallback when PyYAML is absent."""
    data: dict = {}
    current_key: str | None = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0] if not raw.lstrip().startswith("#") else ""
        if not line.strip():
            continue
        if line.startswith("  ") and line.strip().startswith("- "):
            if current_key is not None:
                data.setdefault(current_key, []).append(line.strip()[2:].strip().strip("'\""))
            continue
        if ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            key, val = key.strip(), val.strip().strip("'\"")
            current_key = key
            data[key] = val if val else []
    return data


def load_config(config_file: Path = CONFIG_FILE) -> LanguageConfig:
    text = config_file.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text) or {}
    except ImportError:
        data = _tiny_yaml_lists(text)
    return LanguageConfig(
        vulgar=list(data.get("vulgar", []) or []),
        slur=list(data.get("slur", []) or []),
        replacement=str(data.get("replacement", "redact") or "redact"),
        placeholder=str(data.get("placeholder", "[redacted]") or "[redacted]"),
    )


def tiers_for_policy(policy: str, *, action: str) -> set[str]:
    """Which tiers apply for a given policy.
    action='flag'  -> what audit reports
    action='clean' -> what the fixer may redact (empty set => fixer refuses)
    """
    policy = policy if policy in VALID_POLICIES else DEFAULT_POLICY
    if action == "flag":
        return {
            "clean": {"vulgar", "slur"},
            "flag-only": {"vulgar", "slur"},
            "preserve": {"slur"},
            "preserve-all": set(),
        }[policy]
    # action == 'clean' — only explicit `clean` policy authorizes mutation
    return {"vulgar", "slur"} if policy == "clean" else set()


def _redact(word: str, cfg: LanguageConfig) -> str:
    if cfg.replacement == "placeholder":
        return cfg.placeholder
    if cfg.replacement == "remove":
        return ""
    return word[0] + "*" * (len(word) - 1) if word else word


@dataclass
class Match:
    tier: str
    word: str
    line_no: int


def scan(text: str, cfg: LanguageConfig, tiers: set[str]) -> list[Match]:
    matches: list[Match] = []
    for i, line in enumerate(text.splitlines(), 1):
        for tier in tiers:
            pat = cfg.pattern(tier)
            if pat:
                for m in pat.finditer(line):
                    matches.append(Match(tier, m.group(0), i))
    return matches


def redact_text(text: str, cfg: LanguageConfig, tiers: set[str]) -> tuple[str, int]:
    """Return (new_text, n_replacements). Only the given tiers are touched."""
    count = 0

    def sub_tier(t: str, s: str) -> str:
        nonlocal count
        pat = cfg.pattern(t)
        if not pat:
            return s

        def repl(m: re.Match) -> str:
            nonlocal count
            count += 1
            out = _redact(m.group(0), cfg)
            return out

        return pat.sub(repl, s)

    out = text
    for tier in ("slur", "vulgar"):
        if tier in tiers:
            out = sub_tier(tier, out)
    # 'remove' can leave doubled spaces — normalize the ones we created
    if cfg.replacement == "remove":
        out = re.sub(r"[ \t]{2,}", " ", out)
    return out, count
