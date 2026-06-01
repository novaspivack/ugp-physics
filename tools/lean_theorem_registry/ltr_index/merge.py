"""Merge probe-lean JSON artifacts into SQLite (SPEC_090_LTR2)."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ltr_index.config import (
    DEFAULT_DB,
    DEFAULT_PROBE_DIR,
    build_namespace_map,
    load_config,
    load_mathlib_stub,
)


SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS repos (
  repo_slug     TEXT PRIMARY KEY,
  display_name  TEXT NOT NULL,
  github_url    TEXT,
  tier          INTEGER NOT NULL DEFAULT 1,
  root_namespaces TEXT NOT NULL,
  last_commit   TEXT,
  last_extracted_at TEXT
);

CREATE TABLE IF NOT EXISTS declarations (
  global_id           TEXT PRIMARY KEY,
  repo_slug           TEXT NOT NULL REFERENCES repos(repo_slug),
  lean_name           TEXT NOT NULL,
  display_name        TEXT,
  kind                TEXT NOT NULL,
  module              TEXT,
  code_path           TEXT,
  line_start          INTEGER,
  line_end            INTEGER,
  verification_status TEXT,
  trusted_reason      TEXT,
  is_stub             INTEGER NOT NULL DEFAULT 0,
  UNIQUE (repo_slug, lean_name)
);

CREATE INDEX IF NOT EXISTS idx_decl_repo ON declarations(repo_slug);
CREATE INDEX IF NOT EXISTS idx_decl_kind ON declarations(kind);
CREATE INDEX IF NOT EXISTS idx_decl_verify ON declarations(verification_status);
CREATE INDEX IF NOT EXISTS idx_decl_module ON declarations(module);

CREATE TABLE IF NOT EXISTS dependencies (
  from_id     TEXT NOT NULL REFERENCES declarations(global_id),
  to_id       TEXT NOT NULL REFERENCES declarations(global_id),
  edge_kind   TEXT NOT NULL,
  PRIMARY KEY (from_id, to_id, edge_kind)
);

CREATE INDEX IF NOT EXISTS idx_deps_from ON dependencies(from_id);
CREATE INDEX IF NOT EXISTS idx_deps_to ON dependencies(to_id);

CREATE TABLE IF NOT EXISTS extraction_runs (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  repo_slug     TEXT NOT NULL REFERENCES repos(repo_slug),
  commit_sha    TEXT NOT NULL,
  probe_json_path TEXT,
  declaration_count INTEGER,
  sorry_count   INTEGER,
  axiom_count   INTEGER,
  extracted_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS papers (
  paper_id      TEXT PRIMARY KEY,
  title         TEXT,
  artifact_id   TEXT
);

CREATE TABLE IF NOT EXISTS declaration_papers (
  global_id     TEXT NOT NULL REFERENCES declarations(global_id),
  paper_id      TEXT NOT NULL REFERENCES papers(paper_id),
  source        TEXT NOT NULL,
  confidence    TEXT NOT NULL DEFAULT 'extracted',
  PRIMARY KEY (global_id, paper_id, source)
);

CREATE TABLE IF NOT EXISTS tags (
  tag           TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS declaration_tags (
  global_id     TEXT NOT NULL REFERENCES declarations(global_id),
  tag           TEXT NOT NULL REFERENCES tags(tag),
  source        TEXT NOT NULL,
  PRIMARY KEY (global_id, tag)
);

CREATE TABLE IF NOT EXISTS notes (
  global_id     TEXT PRIMARY KEY REFERENCES declarations(global_id),
  description   TEXT,
  source        TEXT NOT NULL,
  updated_at    TEXT
);
"""


def strip_probe_prefix(code_name: str) -> str:
    if code_name.startswith("probe:"):
        return code_name[6:]
    return code_name


class DependencyResolver:
    def __init__(
        self,
        namespace_map: list[tuple[str, str]],
        stub_rules: list[dict[str, str]],
        known_repos: set[str],
    ) -> None:
        self.namespace_map = namespace_map
        self.stub_rules = sorted(stub_rules, key=lambda r: len(r["prefix"]), reverse=True)
        self.known_repos = known_repos
        self.external_log: list[dict[str, str]] = []

    def resolve(self, probe_name: str, from_repo: str | None = None) -> str:
        lean_name = strip_probe_prefix(probe_name)
        for prefix, repo_slug in self.namespace_map:
            if lean_name == prefix or lean_name.startswith(prefix + "."):
                return f"{repo_slug}:{lean_name}"
        for rule in self.stub_rules:
            prefix = rule["prefix"]
            if lean_name == prefix or lean_name.startswith(prefix + "."):
                return rule["stub_id"]
        ext_id = f"external:unknown:{lean_name}"
        self.external_log.append(
            {"from_repo": from_repo or "", "probe_name": probe_name, "resolved_id": ext_id}
        )
        return ext_id


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_DDL)
    for slug, display in (("stub", "External library stubs"), ("external", "Unresolved external")):
        conn.execute(
            """
            INSERT OR IGNORE INTO repos (repo_slug, display_name, tier, root_namespaces)
            VALUES (?, ?, 0, '[]')
            """,
            (slug, display),
        )
    conn.commit()


def ensure_dep_target(conn: sqlite3.Connection, global_id: str, cfg_repos: dict[str, Any]) -> None:
    if conn.execute("SELECT 1 FROM declarations WHERE global_id = ?", (global_id,)).fetchone():
        return
    if global_id.startswith("stub:"):
        lean_name = global_id[5:]
        conn.execute(
            """
            INSERT OR IGNORE INTO declarations
              (global_id, repo_slug, lean_name, display_name, kind, module,
               verification_status, trusted_reason, is_stub)
            VALUES (?, 'stub', ?, ?, 'stub', ?, 'trusted', NULL, 1)
            """,
            (global_id, lean_name, lean_name.split(".")[-1], lean_name),
        )
        return
    if global_id.startswith("external:unknown:"):
        lean_name = global_id[len("external:unknown:") :]
        conn.execute(
            """
            INSERT OR IGNORE INTO declarations
              (global_id, repo_slug, lean_name, display_name, kind, module,
               verification_status, is_stub)
            VALUES (?, 'external', ?, ?, 'external', ?, NULL, 0)
            """,
            (global_id, lean_name, lean_name.split(".")[-1], lean_name),
        )
        return
    if ":" in global_id:
        repo_slug, lean_name = global_id.split(":", 1)
        if repo_slug in cfg_repos:
            conn.execute(
                """
                INSERT OR IGNORE INTO repos (repo_slug, display_name, tier, root_namespaces)
                VALUES (?, ?, ?, ?)
                """,
                (
                    repo_slug,
                    repo_slug,
                    cfg_repos[repo_slug].get("tier", 1),
                    json.dumps(cfg_repos[repo_slug].get("namespaces", [])),
                ),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO declarations
                  (global_id, repo_slug, lean_name, display_name, kind, module,
                   verification_status, is_stub)
                VALUES (?, ?, ?, ?, 'external_ref', ?, NULL, 0)
                """,
                (global_id, repo_slug, lean_name, lean_name.split(".")[-1], lean_name.rsplit(".", 1)[0] if "." in lean_name else lean_name),
            )


def find_probe_json(probe_dir: Path, repo_slug: str) -> Path | None:
    latest = probe_dir / f"{repo_slug}_latest.json"
    if latest.exists():
        return latest
    summaries = sorted(probe_dir.glob(f"{repo_slug}_*.json"))
    for p in summaries:
        if p.name.endswith("_summary.json") or p.name.endswith("_latest.json"):
            continue
        return p
    return None


def merge_repo(
    conn: sqlite3.Connection,
    repo_slug: str,
    repo_cfg: dict[str, Any],
    probe_path: Path,
    resolver: DependencyResolver,
    cfg_repos: dict[str, Any],
) -> dict[str, int]:
    payload = json.loads(probe_path.read_text(encoding="utf-8"))
    if payload.get("schema") != "probe-lean/extract":
        raise ValueError(f"{probe_path}: invalid schema")
    source = payload.get("source") or {}
    commit = source.get("commit") or "unknown"
    github = repo_cfg.get("github", "")
    namespaces = json.dumps(repo_cfg.get("namespaces", []))
    extracted_at = payload.get("timestamp") or datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    conn.execute(
        """
        INSERT INTO repos (repo_slug, display_name, github_url, tier, root_namespaces,
                           last_commit, last_extracted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(repo_slug) DO UPDATE SET
          display_name=excluded.display_name,
          github_url=excluded.github_url,
          tier=excluded.tier,
          root_namespaces=excluded.root_namespaces,
          last_commit=excluded.last_commit,
          last_extracted_at=excluded.last_extracted_at
        """,
        (
            repo_slug,
            repo_slug,
            github,
            repo_cfg.get("tier", 1),
            namespaces,
            commit,
            extracted_at,
        ),
    )

    # Clear prior declarations/deps for this repo (idempotent re-merge)
    old_ids = [
        r[0]
        for r in conn.execute(
            "SELECT global_id FROM declarations WHERE repo_slug = ? AND is_stub = 0",
            (repo_slug,),
        ).fetchall()
    ]
    if old_ids:
        placeholders = ",".join("?" * len(old_ids))
        conn.execute(f"DELETE FROM dependencies WHERE from_id IN ({placeholders})", old_ids)
        conn.execute(f"DELETE FROM dependencies WHERE to_id IN ({placeholders})", old_ids)
        conn.execute(f"DELETE FROM declaration_papers WHERE global_id IN ({placeholders})", old_ids)
        conn.execute(f"DELETE FROM declaration_tags WHERE global_id IN ({placeholders})", old_ids)
        conn.execute(f"DELETE FROM notes WHERE global_id IN ({placeholders})", old_ids)
    conn.execute("DELETE FROM declarations WHERE repo_slug = ? AND is_stub = 0", (repo_slug,))

    atoms = payload.get("data") or {}
    sorry_count = 0
    axiom_count = 0
    decl_count = 0
    pending_deps: list[tuple[str, str, str]] = []

    for code_name, atom in atoms.items():
        if not atom.get("is-in-package", True):
            continue
        lean_name = strip_probe_prefix(code_name)
        global_id = f"{repo_slug}:{lean_name}"
        code_text = atom.get("code-text") or {}
        vstatus = atom.get("verification-status")
        treason = atom.get("trusted-reason")
        if vstatus == "unverified":
            sorry_count += 1
        if vstatus == "trusted" and treason == "axiom":
            axiom_count += 1

        conn.execute(
            """
            INSERT INTO declarations
              (global_id, repo_slug, lean_name, display_name, kind, module,
               code_path, line_start, line_end, verification_status, trusted_reason, is_stub)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                global_id,
                repo_slug,
                lean_name,
                atom.get("display-name"),
                atom.get("kind", "unknown"),
                atom.get("code-module"),
                atom.get("code-path"),
                code_text.get("lines-start"),
                code_text.get("lines-end"),
                vstatus,
                treason,
            ),
        )
        decl_count += 1

        type_deps = atom.get("type-dependencies") or []
        term_deps = atom.get("term-dependencies") or []
        type_set = set(type_deps)
        term_set = set(term_deps)
        all_deps = set(atom.get("dependencies") or []) | type_set | term_set
        for dep in all_deps:
            if dep in type_set and dep in term_set:
                edge_kind = "both"
            elif dep in type_set:
                edge_kind = "type"
            elif dep in term_set:
                edge_kind = "term"
            else:
                edge_kind = "both"
            to_id = resolver.resolve(dep, repo_slug)
            pending_deps.append((global_id, to_id, edge_kind))

    for from_id, to_id, edge_kind in pending_deps:
        ensure_dep_target(conn, to_id, cfg_repos)
        conn.execute(
            """
            INSERT OR IGNORE INTO dependencies (from_id, to_id, edge_kind)
            VALUES (?, ?, ?)
            """,
            (from_id, to_id, edge_kind),
        )

    conn.execute(
        """
        INSERT INTO extraction_runs
          (repo_slug, commit_sha, probe_json_path, declaration_count, sorry_count,
           axiom_count, extracted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            repo_slug,
            commit,
            str(probe_path),
            decl_count,
            sorry_count,
            axiom_count,
            datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        ),
    )

    return {
        "declarations": decl_count,
        "sorry": sorry_count,
        "axiom": axiom_count,
        "dependencies": len(pending_deps),
    }


def merge_all(
    db_path: Path,
    probe_dir: Path,
    tier: int | None = None,
    repo_slug: str | None = None,
) -> dict[str, Any]:
    cfg = load_config()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)

    namespace_map = build_namespace_map(cfg)
    stub_rules = load_mathlib_stub()
    known_repos = set(cfg.get("repos", {}).keys())
    resolver = DependencyResolver(namespace_map, stub_rules, known_repos)

    results: dict[str, Any] = {"repos": {}, "skipped": [], "external_deps": 0}
    for slug, repo_cfg in cfg.get("repos", {}).items():
        if repo_slug and slug != repo_slug:
            continue
        if tier is not None and repo_cfg.get("tier", 1) != tier:
            continue
        probe_path = find_probe_json(probe_dir, slug)
        if not probe_path:
            results["skipped"].append({"repo_slug": slug, "reason": "no probe json"})
            continue
        summary_path = probe_dir / f"{slug}_summary.json"
        if summary_path.exists():
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            if summary.get("extract_status") == "failed":
                results["skipped"].append({"repo_slug": slug, "reason": summary.get("error", "failed")})
                continue
            if summary.get("declaration_count", 0) < 20 and slug in ("ugp-lean", "ugp-physics-lean", "srrg-lean"):
                results["skipped"].append(
                    {"repo_slug": slug, "reason": f"incomplete extract ({summary.get('declaration_count')} decls)"}
                )
                continue
        try:
            stats = merge_repo(conn, slug, repo_cfg, probe_path, resolver, cfg.get("repos", {}))
            results["repos"][slug] = stats
        except Exception as exc:  # noqa: BLE001 — record per-repo failure
            results["skipped"].append({"repo_slug": slug, "reason": str(exc)})

    results["external_deps"] = len(resolver.external_log)
    unresolved_path = db_path.parent / "unresolved_external_deps.jsonl"
    if resolver.external_log:
        with open(unresolved_path, "w", encoding="utf-8") as f:
            for row in resolver.external_log:
                f.write(json.dumps(row) + "\n")

    conn.commit()
    conn.close()
    return results


def run_merge_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="ltr_index merge")
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_DB)
    parser.add_argument("--probe-dir", type=Path, default=DEFAULT_PROBE_DIR)
    parser.add_argument("--tier", type=int, default=None)
    parser.add_argument("--repo", type=str, default=None)
    args = parser.parse_args(argv)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    results = merge_all(args.output, args.probe_dir, tier=args.tier, repo_slug=args.repo)
    print(json.dumps(results, indent=2))
    if not results["repos"]:
        print("ERROR: no repos merged", file=__import__("sys").stderr)
        return 1
    return 0
