"""Export registry data to markdown (THEOREMS.md)."""

from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from ltr_index.config import DEFAULT_DB


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def export_theorems_md(
    conn: sqlite3.Connection,
    repo_slug: str,
    output_path: Path,
) -> dict:
    rows = conn.execute(
        """
        SELECT lean_name, display_name, kind, module, verification_status,
               trusted_reason, code_path, line_start
        FROM declarations
        WHERE repo_slug = ? AND is_stub = 0
          AND kind IN ('theorem', 'lemma', 'def', 'axiom')
        ORDER BY module, kind, lean_name
        """,
        (repo_slug,),
    ).fetchall()

    sorry_rows = conn.execute(
        """
        SELECT lean_name, module, verification_status
        FROM declarations
        WHERE repo_slug = ? AND verification_status = 'unverified'
        ORDER BY module, lean_name
        """,
        (repo_slug,),
    ).fetchall()

    axiom_rows = conn.execute(
        """
        SELECT lean_name, module
        FROM declarations
        WHERE repo_slug = ? AND trusted_reason = 'axiom'
        ORDER BY module, lean_name
        """,
        (repo_slug,),
    ).fetchall()

    run = conn.execute(
        """
        SELECT commit_sha, extracted_at, declaration_count, sorry_count, axiom_count
        FROM extraction_runs
        WHERE repo_slug = ?
        ORDER BY id DESC LIMIT 1
        """,
        (repo_slug,),
    ).fetchone()

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    lines: list[str] = [
        f"# {repo_slug}: Theorem Catalog",
        "",
        "> **Auto-generated** by the Lean Theorem Registry (LTR). Do not hand-edit.",
        "> Regenerate: `python -m ltr_index export markdown --repo "
        f"{repo_slug} --output <path>`",
        "",
    ]
    if run:
        lines.extend(
            [
                f"**Source commit:** `{run['commit_sha'][:12]}`  ",
                f"**Extracted:** {run['extracted_at']}  ",
                f"**Declarations indexed:** {run['declaration_count']}  ",
                f"**Sorry count:** {run['sorry_count']}  ",
                f"**Axiom count:** {run['axiom_count']}  ",
                "",
            ]
        )

    lines.extend(
        [
            "## Sorry audit (live)",
            "",
        ]
    )
    if sorry_rows:
        lines.append("| Theorem | Module | Status |")
        lines.append("|---------|--------|--------|")
        for r in sorry_rows:
            short = r["lean_name"].split(".")[-1]
            mod = (r["module"] or "").split(".")[-1]
            lines.append(f"| **{short}** | {mod} | unverified (sorry) |")
    else:
        lines.append("No sorry-bearing declarations detected in the indexed package.")
    lines.append("")

    lines.extend(["## Axioms (live)", ""])
    if axiom_rows:
        lines.append("| Name | Module |")
        lines.append("|------|--------|")
        for r in axiom_rows:
            short = r["lean_name"].split(".")[-1]
            mod = (r["module"] or "").split(".")[-1]
            lines.append(f"| **{short}** | {mod} |")
    else:
        lines.append("No axioms in indexed package declarations.")
    lines.append("")

    # Group by module
    by_module: dict[str, list] = {}
    for r in rows:
        mod = r["module"] or "Unknown"
        by_module.setdefault(mod, []).append(r)

    lines.append("## Declarations by module")
    lines.append("")
    for mod in sorted(by_module.keys()):
        short_mod = mod.split(".")[-1] if mod else "Unknown"
        lines.append(f"### {mod}")
        lines.append("")
        lines.append("| Name | Kind | Verification |")
        lines.append("|------|------|--------------|")
        for r in by_module[mod]:
            short = r["lean_name"].split(".")[-1]
            v = r["verification_status"] or ""
            if r["trusted_reason"] == "axiom":
                v = "trusted (axiom)"
            elif v == "unverified":
                v = "unverified ⚠"
            lines.append(f"| **{short}** | {r['kind']} | {v} |")
        lines.append("")

    lines.append(f"<!-- ltr-generated-at: {now} -->")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "repo_slug": repo_slug,
        "output": str(output_path),
        "declaration_rows": len(rows),
        "modules": len(by_module),
        "sorry": len(sorry_rows),
        "axioms": len(axiom_rows),
    }


def run_export_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="ltr_index export")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_md = sub.add_parser("markdown")
    p_md.add_argument("--repo", default="ugp-lean")
    p_md.add_argument("--db", type=Path, default=DEFAULT_DB)
    p_md.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    conn = connect(args.db)
    if args.cmd == "markdown":
        import json

        result = export_theorems_md(conn, args.repo, args.output)
        print(json.dumps(result, indent=2))
    return 0
