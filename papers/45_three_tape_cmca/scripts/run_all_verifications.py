#!/usr/bin/env python3
"""Run all three-tape CMCA verifications and save JSON report."""
from __future__ import annotations

import argparse
import json
import os
import sys

from verification_suite import run_all


def main() -> int:
    parser = argparse.ArgumentParser(description="Three-tape CMCA verification suite")
    parser.add_argument(
        "--out",
        default="verification_report.json",
        help="Output JSON path (default: verification_report.json)",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")
    args = parser.parse_args()

    report = run_all(verbose=not args.quiet)
    out_path = args.out
    tmp_path = out_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    os.replace(tmp_path, out_path)
    if not args.quiet:
        print(f"\nReport saved to {out_path}")
    n_fail = report["summary"]["total"] - report["summary"]["passed"]
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
