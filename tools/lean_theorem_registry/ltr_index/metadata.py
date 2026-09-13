"""Best-effort metadata ingestion (SPEC_090_LTR3)."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from ltr_index.config import (
    DEFAULT_DB,
    DEFAULT_UNRESOLVED,
    UGP_PHYSICS_ROOT,
    load_config,
    paper_id_from_dirname,
)


LEAN_MACRO_RE = re.compile(
    r"\\lean(?:ref|cite|name|module)?\*?\{([^}]+)\}",
    re.IGNORECASE,
)
BACKTICK_NAME_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_.]*)`")
THEOREMS_ROW_RE = re.compile(
    r"^\|\s*\*\*([^*|]+)\*\*\s*\|\s*([^|]+)\|\s*([^|]+)\|"
)
SECTION_HEADER_RE = re.compile(r"^##\s+(.+)$")


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def log_unresolved(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def load_decl_index(conn: sqlite3.Connection) -> tuple[dict[str, str], dict[str, list[str]]]:
    by_name: dict[str, str] = {}
    by_suffix: dict[str, list[str]] = {}
    for row in conn.execute(
        "SELECT global_id, lean_name FROM declarations WHERE is_stub = 0"
    ):
        gid, name = row["global_id"], row["lean_name"]
        by_name[name] = gid
        suffix = name.split(".")[-1]
        by_suffix.setdefault(suffix, []).append(gid)
    return by_name, by_suffix


def resolve_name(
    raw: str,
    by_name: dict[str, str],
    by_suffix: dict[str, list[str]],
) -> tuple[str | None, str]:
    raw = raw.strip().strip("`")
    if raw in by_name:
        return by_name[raw], "extracted"
    if raw.endswith(".lean"):
        return None, "module_path"
    candidates = by_suffix.get(raw.split(".")[-1], [])
    if len(candidates) == 1:
        return candidates[0], "inferred"
    if raw in by_name:
        return by_name[raw], "extracted"
    # try suffix on full dotted name
    suffix = raw.split(".")[-1]
    cands = by_suffix.get(suffix, [])
    if len(cands) == 1:
        return cands[0], "inferred"
    return None, "no_match"


def seed_papers(conn: sqlite3.Connection, papers_dir: Path) -> int:
    count = 0
    for child in sorted(papers_dir.iterdir()):
        if not child.is_dir():
            continue
        paper_id = paper_id_from_dirname(child.name)
        if not paper_id:
            continue
        title = child.name.replace("_", " ")
        conn.execute(
            """
            INSERT INTO papers (paper_id, title, artifact_id)
            VALUES (?, ?, ?)
            ON CONFLICT(paper_id) DO UPDATE SET title=excluded.title
            """,
            (paper_id, title, f"ugp-physics-{paper_id.lower()}"),
        )
        count += 1
    conn.commit()
    return count


def ingest_provenance(
    conn: sqlite3.Connection,
    papers_dir: Path,
    by_name: dict[str, str],
    by_suffix: dict[str, list[str]],
    unresolved_path: Path,
) -> dict[str, int]:
    stats = {"resolved": 0, "unresolved": 0, "links": 0}
    for prov in papers_dir.glob("*/PROVENANCE.md"):
        paper_id = paper_id_from_dirname(prov.parent.name)
        if not paper_id:
            continue
        text = prov.read_text(encoding="utf-8", errors="replace")
        if not re.search(r"(?i)theorem|lean|module", text):
            continue
        names = set(BACKTICK_NAME_RE.findall(text))
        for raw in names:
            if raw.endswith(".lean") or raw.endswith(".md"):
                continue
            gid, confidence = resolve_name(raw, by_name, by_suffix)
            if gid:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO declaration_papers
                      (global_id, paper_id, source, confidence)
                    VALUES (?, ?, 'provenance_md', ?)
                    """,
                    (gid, paper_id, confidence),
                )
                stats["links"] += 1
                stats["resolved"] += 1
            else:
                log_unresolved(
                    unresolved_path,
                    {
                        "source": "provenance_md",
                        "paper": paper_id,
                        "raw_name": raw,
                        "reason": confidence,
                        "file": str(prov.relative_to(UGP_PHYSICS_ROOT)),
                    },
                )
                stats["unresolved"] += 1
    conn.commit()
    return stats


def ingest_tex(
    conn: sqlite3.Connection,
    papers_dir: Path,
    by_name: dict[str, str],
    by_suffix: dict[str, list[str]],
    unresolved_path: Path,
) -> dict[str, int]:
    stats = {"resolved": 0, "unresolved": 0, "links": 0, "refs": 0}
    paper_dirs = {d.name: paper_id_from_dirname(d.name) for d in papers_dir.iterdir() if d.is_dir()}
    for tex in papers_dir.glob("*/*.tex"):
        paper_id = paper_id_from_dirname(tex.parent.name)
        if not paper_id:
            continue
        text = tex.read_text(encoding="utf-8", errors="replace")
        for m in LEAN_MACRO_RE.finditer(text):
            raw = m.group(1).strip()
            stats["refs"] += 1
            gid, confidence = resolve_name(raw, by_name, by_suffix)
            if gid:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO declaration_papers
                      (global_id, paper_id, source, confidence)
                    VALUES (?, ?, 'tex_lean_macro', ?)
                    """,
                    (gid, paper_id, confidence),
                )
                stats["links"] += 1
                stats["resolved"] += 1
            else:
                log_unresolved(
                    unresolved_path,
                    {
                        "source": "tex_lean_macro",
                        "paper": paper_id,
                        "raw_name": raw,
                        "reason": confidence,
                        "file": str(tex.relative_to(UGP_PHYSICS_ROOT)),
                    },
                )
                stats["unresolved"] += 1
    conn.commit()
    return stats


def slugify_tag(header: str) -> str:
    s = header.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:64] or "untagged"


def ingest_theorems_md(
    conn: sqlite3.Connection,
    theorems_path: Path,
    by_name: dict[str, str],
    by_suffix: dict[str, list[str]],
    unresolved_path: Path,
) -> dict[str, int]:
    stats = {
        "rows": 0,
        "matched": 0,
        "unmatched": 0,
        "notes": 0,
        "tags": 0,
    }
    if not theorems_path.exists():
        return stats

    current_tag = "catalog"
    for line in theorems_path.read_text(encoding="utf-8", errors="replace").splitlines():
        sec = SECTION_HEADER_RE.match(line)
        if sec:
            current_tag = slugify_tag(sec.group(1))
            conn.execute("INSERT OR IGNORE INTO tags (tag) VALUES (?)", (current_tag,))
            continue
        row = THEOREMS_ROW_RE.match(line)
        if not row:
            continue
        stats["rows"] += 1
        thm_name = row.group(1).strip()
        statement = row.group(3).strip()
        gid, confidence = resolve_name(thm_name, by_name, by_suffix)
        if not gid:
            stats["unmatched"] += 1
            log_unresolved(
                unresolved_path,
                {
                    "source": "theorems_md",
                    "raw_name": thm_name,
                    "reason": "stale_no_db_match",
                    "file": str(theorems_path),
                },
            )
            continue
        stats["matched"] += 1
        conn.execute("INSERT OR IGNORE INTO tags (tag) VALUES (?)", (current_tag,))
        conn.execute(
            """
            INSERT OR IGNORE INTO declaration_tags (global_id, tag, source)
            VALUES (?, ?, 'theorems_md')
            """,
            (gid, current_tag),
        )
        stats["tags"] += 1
        desc = statement[:500]
        conn.execute(
            """
            INSERT INTO notes (global_id, description, source, updated_at)
            VALUES (?, ?, 'theorems_md', ?)
            ON CONFLICT(global_id) DO UPDATE SET
              description=excluded.description,
              source=excluded.source,
              updated_at=excluded.updated_at
            """,
            (gid, desc, datetime.now(timezone.utc).replace(microsecond=0).isoformat()),
        )
        stats["notes"] += 1
    conn.commit()
    return stats


def ingest_manual(conn: sqlite3.Connection, csv_path: Path) -> dict[str, int]:
    stats = {"rows": 0, "links": 0}
    if not csv_path.exists():
        return stats
    import csv

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stats["rows"] += 1
            gid = row.get("global_id", "").strip()
            paper_id = row.get("paper_id", "").strip()
            tag = row.get("tag", "").strip()
            desc = row.get("description", "").strip()
            if paper_id:
                conn.execute(
                    "INSERT OR IGNORE INTO papers (paper_id, title) VALUES (?, ?)",
                    (paper_id, paper_id),
                )
                conn.execute(
                    """
                    INSERT OR REPLACE INTO declaration_papers
                      (global_id, paper_id, source, confidence)
                    VALUES (?, ?, 'manual', 'manual')
                    """,
                    (gid, paper_id),
                )
                stats["links"] += 1
            if tag:
                conn.execute("INSERT OR IGNORE INTO tags (tag) VALUES (?)", (tag,))
                conn.execute(
                    """
                    INSERT OR REPLACE INTO declaration_tags (global_id, tag, source)
                    VALUES (?, ?, 'manual')
                    """,
                    (gid, tag),
                )
            if desc:
                conn.execute(
                    """
                    INSERT INTO notes (global_id, description, source, updated_at)
                    VALUES (?, ?, 'manual', ?)
                    ON CONFLICT(global_id) DO UPDATE SET
                      description=excluded.description,
                      source='manual',
                      updated_at=excluded.updated_at
                    """,
                    (gid, desc, datetime.now(timezone.utc).replace(microsecond=0).isoformat()),
                )
    conn.commit()
    return stats


def staleness_report(conn: sqlite3.Connection, theorems_path: Path, theorems_stats: dict) -> dict:
    ugp_count = conn.execute(
        "SELECT COUNT(*) FROM declarations WHERE repo_slug = 'ugp-lean' AND is_stub = 0"
    ).fetchone()[0]
    return {
        "THEOREMS.md_rows": theorems_stats.get("rows", 0),
        "matched_in_db": theorems_stats.get("matched", 0),
        "in_db_not_in_theorems_md": max(0, ugp_count - theorems_stats.get("matched", 0)),
        "in_theorems_md_not_in_db": theorems_stats.get("unmatched", 0),
        "theorems_md_path": str(theorems_path),
    }


def run_ingest(
    db_path: Path,
    sources: set[str],
    unresolved_path: Path,
    theorems_md: Path | None = None,
) -> dict:
    if sources == {"none"}:
        return {"status": "noop"}

    if unresolved_path.exists():
        unresolved_path.unlink()

    conn = connect(db_path)
    by_name, by_suffix = load_decl_index(conn)
    papers_dir = UGP_PHYSICS_ROOT / "papers"
    report: dict = {}

    if "papers" in sources or "all" in sources:
        report["papers_seeded"] = seed_papers(conn, papers_dir)

    if "provenance" in sources or "all" in sources:
        report["provenance"] = ingest_provenance(
            conn, papers_dir, by_name, by_suffix, unresolved_path
        )

    if "tex" in sources or "all" in sources:
        report["tex"] = ingest_tex(conn, papers_dir, by_name, by_suffix, unresolved_path)

    theorems_path = theorems_md or Path("/Users/nova/ugp-lean/docs/THEOREMS.md")
    theorems_stats: dict = {"rows": 0, "matched": 0, "unmatched": 0}
    if "theorems" in sources or "all" in sources:
        theorems_stats = ingest_theorems_md(
            conn, theorems_path, by_name, by_suffix, unresolved_path
        )
        report["theorems_md"] = theorems_stats
        report["staleness"] = staleness_report(conn, theorems_path, theorems_stats)

    manual_csv = Path(__file__).resolve().parent.parent / "config" / "manual_links.csv"
    if "manual" in sources or "all" in sources:
        report["manual"] = ingest_manual(conn, manual_csv)

    unresolved_count = 0
    if unresolved_path.exists():
        unresolved_count = sum(1 for _ in open(unresolved_path, encoding="utf-8"))
    report["unresolved_total"] = unresolved_count
    conn.close()
    return report


def run_metadata_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="ltr_index metadata")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ingest = sub.add_parser("ingest")
    p_ingest.add_argument(
        "--sources",
        default="all",
        help="Comma-separated: all|none|provenance,tex,theorems,manual,papers",
    )
    p_ingest.add_argument("--db", type=Path, default=DEFAULT_DB)
    p_ingest.add_argument("--unresolved", type=Path, default=DEFAULT_UNRESOLVED)
    p_ingest.add_argument("--theorems-md", type=Path, default=None)

    p_seed = sub.add_parser("seed-papers")
    p_seed.add_argument("--db", type=Path, default=DEFAULT_DB)

    args = parser.parse_args(argv)
    if args.cmd == "seed-papers":
        conn = connect(args.db)
        n = seed_papers(conn, UGP_PHYSICS_ROOT / "papers")
        print(json.dumps({"papers_seeded": n}, indent=2))
        return 0

    sources = {s.strip() for s in args.sources.split(",") if s.strip()}
    report = run_ingest(args.db, sources, args.unresolved, args.theorems_md)
    print(json.dumps(report, indent=2))
    return 0
