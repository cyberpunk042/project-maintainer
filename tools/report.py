"""pm report — run audit across all registry projects; consolidated health report."""
from __future__ import annotations

import argparse
import sys

from tools.audit import as_dict, audit_target, counts, print_report
from tools.registry import load_registry


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="pm report", description=__doc__)
    ap.add_argument("--checks", help="comma-separated subset of checks to run")
    ap.add_argument("--json", action="store_true", help="emit the whole report as JSON")
    args = ap.parse_args(argv)
    checks = set(args.checks.split(",")) if args.checks else None

    reg = load_registry()
    totals: dict[str, int] = {}
    skipped: list[str] = []
    json_projects: list[dict] = []
    for entry in reg.values():
        if not entry.exists_locally():
            skipped.append(entry.name)
            continue
        path = entry.resolved_path()
        findings = audit_target(path, entry, checks)
        totals[entry.name] = len(findings)
        if args.json:
            d = as_dict(path, findings)
            d["project"] = entry.name
            json_projects.append(d)
        else:
            print_report(path, findings)
            print()

    if args.json:
        import json

        print(json.dumps({
            "projects": json_projects,
            "skipped": skipped,
            "totals": totals,
        }, indent=2))
        return 0

    print("=" * 60)
    print("REPORT summary:")
    for name, count in totals.items():
        print(f"  {name:<32} {count} finding(s)")
    for name in skipped:
        print(f"  {name:<32} SKIP: not cloned locally")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
