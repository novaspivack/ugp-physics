"""CLI entrypoint: python -m ltr_index merge|query|metadata|export"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("Usage: python -m ltr_index {merge,query,metadata,export} ...", file=sys.stderr)
        return 2

    cmd = argv[0]
    rest = argv[1:]

    if cmd == "merge":
        from ltr_index.merge import run_merge_cli

        return run_merge_cli(rest)
    if cmd == "query":
        from ltr_index.query import run_query_cli

        return run_query_cli(rest)
    if cmd == "metadata":
        from ltr_index.metadata import run_metadata_cli

        return run_metadata_cli(rest)
    if cmd == "export":
        from ltr_index.export import run_export_cli

        return run_export_cli(rest)

    print(f"Unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
