"""pm report — run audit across all registry projects; consolidated health report."""
from __future__ import annotations

import argparse
import sys

from tools.audit import audit_target, print_report
from tools.registry import load_registry


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="pm report", description=__doc__)
    ap.add_argument("--checks", help="comma-separated subset of checks to run")
    args = ap.parse_args(argv)
    checks = set(args.checks.split(",")) if args.checks else None

    reg = load_registry()
    totals: dict[str, int] = {}
    skipped: list[str] = []
    for entry in reg.values():
        if not entry.exists_locally():
            skipped.append(entry.name)
            continue
        findings = audit_target(entry.resolved_path(), entry, checks)
        print_report(entry.resolved_path(), findings)
        totals[entry.name] = len(findings)
        print()
    print("=" * 60)
    print("REPORT summary:")
    for name, count in totals.items():
        print(f"  {name:<32} {count} finding(s)")
    for name in skipped:
        print(f"  {name:<32} SKIP: not cloned locally")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
