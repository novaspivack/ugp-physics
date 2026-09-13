"""CLI queries against ltr.db (SPEC_090_LTR2)."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from ltr_index.config import DEFAULT_DB


def connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}. Run merge first.")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def cmd_stats(conn: sqlite3.Connection, fmt: str) -> None:
    rows = conn.execute(
        """
        SELECT repo_slug, COUNT(*) AS n,
               SUM(CASE WHEN verification_status = 'unverified' THEN 1 ELSE 0 END) AS sorry,
               SUM(CASE WHEN verification_status = 'trusted' AND trusted_reason = 'axiom' THEN 1 ELSE 0 END) AS axioms
        FROM declarations
        WHERE is_stub = 0 AND repo_slug NOT IN ('stub', 'external')
        GROUP BY repo_slug
        ORDER BY repo_slug
        """
    ).fetchall()
    total = conn.execute(
        """
        SELECT COUNT(*) FROM declarations
        WHERE is_stub = 0 AND repo_slug NOT IN ('stub', 'external')
        """
    ).fetchone()[0]
    dep_count = conn.execute("SELECT COUNT(*) FROM dependencies").fetchone()[0]
    stub_count = conn.execute("SELECT COUNT(*) FROM declarations WHERE is_stub = 1").fetchone()[0]
    payload = {
        "total_declarations": total,
        "total_dependencies": dep_count,
        "stub_nodes": stub_count,
        "by_repo": [dict(r) for r in rows],
    }
    if fmt == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(f"Total declarations: {total}")
        print(f"Dependency edges: {dep_count}")
        print(f"Stub nodes: {stub_count}")
        print()
        print(f"{'repo':<40} {'decls':>8} {'sorry':>8} {'axiom':>8}")
        for r in rows:
            print(f"{r['repo_slug']:<40} {r['n']:>8} {r['sorry']:>8} {r['axioms']:>8}")


def cmd_deps(
    conn: sqlite3.Connection,
    global_id: str,
    max_depth: int,
    include_stubs: bool,
    fmt: str,
) -> None:
    stub_filter = "" if include_stubs else "AND d.is_stub = 0"
    rows = conn.execute(
        f"""
        WITH RECURSIVE dep_tree(from_id, to_id, depth) AS (
          SELECT ?, d.to_id, 1
          FROM dependencies d WHERE d.from_id = ?
          UNION
          SELECT dt.from_id, d.to_id, dt.depth + 1
          FROM dep_tree dt
          JOIN dependencies d ON d.from_id = dt.to_id
          WHERE dt.depth < ?
        )
        SELECT DISTINCT d.global_id, d.lean_name, d.kind, d.repo_slug,
               d.verification_status, d.trusted_reason, d.is_stub, MIN(dt.depth) AS depth
        FROM dep_tree dt
        JOIN declarations d ON d.global_id = dt.to_id
        WHERE 1=1 {stub_filter}
        GROUP BY d.global_id
        ORDER BY depth, d.lean_name
        """,
        (global_id, global_id, max_depth),
    ).fetchall()
    if fmt == "json":
        print(json.dumps([dict(r) for r in rows], indent=2))
    else:
        print(f"Dependencies of {global_id} (max_depth={max_depth}):")
        for r in rows:
            flags = []
            if r["verification_status"] == "unverified":
                flags.append("SORRY")
            if r["trusted_reason"] == "axiom":
                flags.append("AXIOM")
            flag_s = f" [{', '.join(flags)}]" if flags else ""
            print(f"  d={r['depth']} {r['global_id']} ({r['kind']}){flag_s}")


def cmd_dependents(conn: sqlite3.Connection, global_id: str, max_depth: int, fmt: str) -> None:
    rows = conn.execute(
        """
        WITH RECURSIVE rev_tree(from_id, to_id, depth) AS (
          SELECT d.from_id, ?, 1
          FROM dependencies d WHERE d.to_id = ?
          UNION
          SELECT d.from_id, rt.to_id, rt.depth + 1
          FROM rev_tree rt
          JOIN dependencies d ON d.to_id = rt.from_id
          WHERE rt.depth < ?
        )
        SELECT DISTINCT d.global_id, d.lean_name, d.kind, d.repo_slug,
               d.verification_status, MIN(rt.depth) AS depth
        FROM rev_tree rt
        JOIN declarations d ON d.global_id = rt.from_id
        WHERE d.is_stub = 0
        GROUP BY d.global_id
        ORDER BY depth, d.lean_name
        """,
        (global_id, global_id, max_depth),
    ).fetchall()
    if fmt == "json":
        print(json.dumps([dict(r) for r in rows], indent=2))
    else:
        print(f"Dependents of {global_id}:")
        for r in rows:
            print(f"  d={r['depth']} {r['global_id']} ({r['kind']})")


def cmd_trust_path(conn: sqlite3.Connection, global_id: str, fmt: str) -> None:
    rows = conn.execute(
        """
        WITH RECURSIVE dep_tree(from_id, to_id, depth) AS (
          SELECT ?, d.to_id, 1
          FROM dependencies d WHERE d.from_id = ?
          UNION
          SELECT dt.from_id, d.to_id, dt.depth + 1
          FROM dep_tree dt
          JOIN dependencies d ON d.from_id = dt.to_id
        )
        SELECT DISTINCT d.global_id, d.lean_name, d.kind, d.repo_slug,
               d.verification_status, d.trusted_reason, MIN(dt.depth) AS depth
        FROM dep_tree dt
        JOIN declarations d ON d.global_id = dt.to_id
        WHERE d.verification_status = 'unverified'
           OR (d.verification_status = 'trusted' AND d.trusted_reason = 'axiom')
        GROUP BY d.global_id
        ORDER BY depth, d.lean_name
        """,
        (global_id, global_id),
    ).fetchall()
    if fmt == "json":
        print(json.dumps([dict(r) for r in rows], indent=2))
    else:
        print(f"Trust-path issues for {global_id}:")
        if not rows:
            print("  (none — all deps verified or trusted non-axiom)")
        for r in rows:
            reason = r["trusted_reason"] or r["verification_status"]
            print(f"  d={r['depth']} {r['global_id']} ({r['kind']}) — {reason}")


def cmd_search(conn: sqlite3.Connection, pattern: str, repo: str | None, fmt: str) -> None:
    like = f"%{pattern}%"
    sql = """
        SELECT global_id, lean_name, kind, repo_slug, verification_status, module
        FROM declarations
        WHERE is_stub = 0 AND (lean_name LIKE ? OR display_name LIKE ?)
    """
    params: list[str] = [like, like]
    if repo:
        sql += " AND repo_slug = ?"
        params.append(repo)
    sql += " ORDER BY lean_name LIMIT 100"
    rows = conn.execute(sql, params).fetchall()
    if fmt == "json":
        print(json.dumps([dict(r) for r in rows], indent=2))
    else:
        for r in rows:
            print(f"{r['global_id']} [{r['kind']}] {r['verification_status']}")


def cmd_list(
    conn: sqlite3.Connection,
    repo: str | None,
    kind: str | None,
    status: str | None,
    fmt: str,
) -> None:
    sql = "SELECT global_id, lean_name, kind, verification_status FROM declarations WHERE is_stub = 0"
    params: list[str] = []
    if repo:
        sql += " AND repo_slug = ?"
        params.append(repo)
    if kind:
        sql += " AND kind = ?"
        params.append(kind)
    if status:
        sql += " AND verification_status = ?"
        params.append(status)
    sql += " ORDER BY lean_name LIMIT 500"
    rows = conn.execute(sql, params).fetchall()
    if fmt == "json":
        print(json.dumps([dict(r) for r in rows], indent=2))
    else:
        for r in rows:
            print(f"{r['global_id']} [{r['kind']}] {r['verification_status']}")


def cmd_paper_theorems(conn: sqlite3.Connection, paper_id: str, fmt: str) -> None:
    rows = conn.execute(
        """
        SELECT d.global_id, d.lean_name, d.kind, d.repo_slug, dp.source, dp.confidence
        FROM declaration_papers dp
        JOIN declarations d ON d.global_id = dp.global_id
        WHERE dp.paper_id = ?
        ORDER BY d.lean_name
        """,
        (paper_id,),
    ).fetchall()
    if fmt == "json":
        print(json.dumps([dict(r) for r in rows], indent=2))
    else:
        print(f"Theorems linked to {paper_id}: {len(rows)}")
        for r in rows:
            print(f"  {r['global_id']} ({r['source']}, {r['confidence']})")


def run_query_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="ltr_index query")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--format", choices=["table", "json"], default="table")
    sub = parser.add_subparsers(dest="subcmd", required=True)

    sub.add_parser("stats")

    p_deps = sub.add_parser("deps")
    p_deps.add_argument("global_id")
    p_deps.add_argument("--max-depth", type=int, default=10)
    p_deps.add_argument("--include-stubs", action="store_true")

    p_dep = sub.add_parser("dependents")
    p_dep.add_argument("global_id")
    p_dep.add_argument("--max-depth", type=int, default=10)

    p_trust = sub.add_parser("trust-path")
    p_trust.add_argument("global_id")

    p_search = sub.add_parser("search")
    p_search.add_argument("pattern")
    p_search.add_argument("--repo", default=None)

    p_list = sub.add_parser("list")
    p_list.add_argument("--repo", default=None)
    p_list.add_argument("--kind", default=None)
    p_list.add_argument("--status", default=None)

    p_paper = sub.add_parser("paper")
    p_paper.add_argument("paper_id")
    p_paper.add_argument("--list-theorems", action="store_true")

    args, _ = parser.parse_known_args(argv)
    try:
        conn = connect(args.db)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    if args.subcmd == "stats":
        cmd_stats(conn, args.format)
    elif args.subcmd == "deps":
        cmd_deps(conn, args.global_id, args.max_depth, args.include_stubs, args.format)
    elif args.subcmd == "dependents":
        cmd_dependents(conn, args.global_id, args.max_depth, args.format)
    elif args.subcmd == "trust-path":
        cmd_trust_path(conn, args.global_id, args.format)
    elif args.subcmd == "search":
        cmd_search(conn, args.pattern, args.repo, args.format)
    elif args.subcmd == "list":
        cmd_list(conn, args.repo, args.kind, args.status, args.format)
    elif args.subcmd == "paper":
        cmd_paper_theorems(conn, args.paper_id, args.format)
    return 0
