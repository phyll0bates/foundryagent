"""Command line entrypoint for autopatch."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

from parser import parse_tenable
from planner import build_plan
from pr_creator import create_pr
from resolver import resolve
from notifier import notify


def main() -> int:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(description="AutoPatch agent")
    parser.add_argument("--tenable-file", required=True, help="Path to Tenable JSON report")
    parser.add_argument("--window", required=True, help="Maintenance window")
    args = parser.parse_args()

    try:
        vulnerabilities = parse_tenable(args.tenable_file)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if not vulnerabilities:
        print("No vulnerabilities found", file=sys.stderr)
        return 2

    outputs: List[Dict[str, object]] = []
    for vuln in vulnerabilities:
        try:
            pkg_dir = resolve(vuln["pkg"], vuln["version"])
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 2

        plan = build_plan(pkg_dir)
        branch = create_pr(Path("vulnerable-app"), pkg_dir, vuln["cve"])
        notify("success", f"Branch {branch} created")
        outputs.append({"cve": vuln["cve"], "plan": plan, "branch": branch})

    for item in outputs:
        print(json.dumps(item))

    return 0


if __name__ == "__main__":
    sys.exit(main())
