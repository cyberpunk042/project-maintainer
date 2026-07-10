"""project-maintainer CLI dispatcher: python3 -m tools.pm <verb> [args...]

Verbs (the name is the spec — maintain, clean, level-up):
  registry   list/inspect target-project registry        [working]
  audit      read-only scan of a target's docs/wiki      [working — base checks]
  report     audit across all registry projects          [working]
  clean      safe mechanical corrections (dry-run dflt)  [base fixers]
  fix        targeted corrections                        [scaffold]
  implant    implant the second-brain layer into target  [scaffold]
  upgrade    re-sync implanted target with templates     [scaffold]
  migrate    versioned idempotent migrations             [scaffold]
  scaffold   stamp a single template into a target       [scaffold]
  doctor     target CI/health baseline (green/red/unknown) [working]
  selfcheck  sanity-check this repo itself               [working]
"""
from __future__ import annotations

import sys


def selfcheck(argv: list[str]) -> int:
    """Verify this repo's own invariants: imports, registry parse, templates present."""
    import compileall

    from tools._paths import MIGRATIONS_DIR, REGISTRY_FILE, REPO_ROOT, TEMPLATES_DIR
    from tools.implant import MANIFEST
    from tools.registry import load_registry

    ok = True
    if not compileall.compile_dir(str(REPO_ROOT / "tools"), quiet=1):
        print("  FAIL: tools/ does not compile")
        ok = False
    reg = load_registry()
    print(f"  ok: registry parses ({len(reg)} project(s) in {REGISTRY_FILE.name})")
    missing = [s for s in MANIFEST if not (TEMPLATES_DIR / s).is_file()]
    if missing:
        print(f"  FAIL: implant manifest references missing templates: {missing}")
        ok = False
    else:
        print(f"  ok: implant manifest complete ({len(MANIFEST)} template(s))")
    print(f"  ok: migrations dir present ({MIGRATIONS_DIR.exists()})")

    from tools.language import VALID_POLICIES, load_config
    try:
        cfg = load_config()
        print(f"  ok: language config loads ({len(cfg.vulgar)} vulgar, {len(cfg.slur)} slur term(s))")
    except (OSError, ValueError) as e:
        print(f"  FAIL: language config: {e}")
        ok = False
    bad = [p.name for p in reg.values() if p.language_policy not in VALID_POLICIES]
    if bad:
        print(f"  FAIL: invalid language_policy on: {bad}")
        ok = False
    else:
        print("  ok: all registry language_policy values valid")

    import unittest

    suite = unittest.defaultTestLoader.discover(str(REPO_ROOT / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=0, stream=open("/dev/null", "w")).run(suite)
    if result.wasSuccessful():
        print(f"  ok: unit tests pass ({result.testsRun} test(s))")
    else:
        print(f"  FAIL: {len(result.failures)} failure(s), {len(result.errors)} error(s) in unit tests")
        ok = False

    print("SELFCHECK " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


VERBS = {
    "registry": "tools.registry",
    "audit": "tools.audit",
    "report": "tools.report",
    "clean": "tools.clean",
    "fix": "tools.fix",
    "implant": "tools.implant",
    "upgrade": "tools.upgrade",
    "migrate": "tools.migrate",
    "scaffold": "tools.scaffold",
    "doctor": "tools.doctor",
}


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    verb, rest = argv[0], argv[1:]
    if verb == "selfcheck":
        return selfcheck(rest)
    if verb not in VERBS:
        print(f"ERROR: unknown verb '{verb}'.\n{__doc__}", file=sys.stderr)
        return 2
    import importlib

    module = importlib.import_module(VERBS[verb])
    return module.main(rest)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
