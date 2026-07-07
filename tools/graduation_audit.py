#!/usr/bin/env python3
"""Audit papers for script graduation gaps. Read-only."""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "papers"
SANDBOX = ROOT / "research-sandbox"

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".lake", "build"}

# Known external graduated roots (outside papers/NN_*)
KNOWN_EXTERNAL = {
    "UGP_GTE_SM_Verifier/UGP_GTE_SM_Verifier.py",
    "UGP_GTE_SM_Verifier/",
    "discovery_engine/",
    "MFRR/",
    "pr0_system/",
    "ugp_discovery_lab/",
}


def walk_scripts(base: Path, exts=(".py", ".wl", ".sh")):
    out = {}
    if not base.is_dir():
        return out
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(exts):
                p = Path(dirpath) / fn
                out.setdefault(fn, []).append(str(p.relative_to(ROOT)))
    return out


def paper_dirs():
    return sorted(d for d in PAPERS.iterdir() if d.is_dir() and re.match(r"\d+_", d.name))


def unescape_latex(s: str) -> str:
    s = re.sub(r"\\allowbreak\s*", "", s)
    s = s.replace(r"\_", "_").replace(r"\-", "-").replace(r"\.", ".")
    s = re.sub(r"\\phantom\{[^}]*", "", s)
    return s.strip()


def extract_script_refs(text: str, source: str):
    """Extract explicit script references from REPRODUCE/tex prose."""
    refs = []

    # research-sandbox mentions
    for m in re.finditer(r"research[-_]sandbox[^\s`\"']*", text):
        refs.append(("sandbox_mention", m.group(0), source))

    # Full repo paths
    for m in re.finditer(
        r"papers/\d+_[^/\s`\"']+/(?:scripts|canonical_run)/[a-zA-Z0-9_./-]+\.(?:py|wl|sh)",
        text,
    ):
        refs.append(("full_path", m.group(0), source))

    # Markdown backticks with .py/.wl
    for m in re.finditer(r"`([^`\n]+\.(?:py|wl|sh))`", text):
        val = m.group(1).strip()
        if "/" in val:
            refs.append(("path", val, source))
        else:
            refs.append(("basename", Path(val).name, source))

    # LaTeX texttt / nolinkurl / verb — require plausible script name
    for m in re.finditer(
        r"\\(?:texttt|nolinkurl|verb)\{([^}]+)\}|\\(?:texttt|nolinkurl|verb)\|([^|]+)\|",
        text,
    ):
        raw = m.group(1) or m.group(2) or ""
        val = unescape_latex(raw).strip()
        if re.search(r"\.(?:py|wl|sh)$", val):
            if val.startswith("papers/"):
                refs.append(("path", val, source))
            elif "/" in val:
                refs.append(("path", val, source))
            else:
                refs.append(("basename", val, source))

    # python3 invocations (REPRODUCE)
    for m in re.finditer(r"python3\s+(?:scripts/)?([a-zA-Z][a-zA-Z0-9_]+\.(?:py|wl))", text):
        refs.append(("basename", m.group(1), source))

    # Table pipe rows: | `script.py` |
    for m in re.finditer(r"\|\s*`([a-zA-Z][a-zA-Z0-9_]+\.(?:py|wl|sh))`\s*\|", text):
        refs.append(("basename", m.group(1), source))

    return refs


def build_indexes():
    paper_scripts = {}
    paper_scripts_flat = {}
    for pd in paper_dirs():
        scripts = {}
        for dirpath, dirnames, filenames in os.walk(pd):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                if fn.endswith((".py", ".wl", ".sh")):
                    rel = str((Path(dirpath) / fn).relative_to(pd))
                    scripts.setdefault(fn, []).append(rel)
                    paper_scripts_flat.setdefault(fn, []).append((pd.name, rel))
        paper_scripts[str(pd)] = scripts
    return paper_scripts, paper_scripts_flat, walk_scripts(SANDBOX), walk_scripts(ROOT)


def classify_external(paths):
    for p in paths:
        for known in KNOWN_EXTERNAL:
            if p.startswith(known) or known.rstrip("/") in p:
                return {"status": "EXTERNAL_KNOWN", "path": p}
    return {"status": "EXTERNAL", "paths": paths[:5]}


def resolve(ref_type, ref_value, paper_dir, paper_scripts, paper_scripts_flat, sandbox_scripts, repo_scripts):
    if ref_type == "sandbox_mention":
        return {"status": "SANDBOX_MENTION", "detail": ref_value}

    if ref_type in ("full_path", "path"):
        p = ROOT / ref_value if not ref_value.startswith("/") else Path(ref_value)
        if p.is_file():
            rel = str(p.relative_to(ROOT))
            if rel.startswith("papers/"):
                return {"status": "OK", "path": rel}
            return {"status": "EXTERNAL_KNOWN", "path": rel}
        # cross-paper path missing
        bn = p.name
        if bn in paper_scripts_flat:
            hit = paper_scripts_flat[bn][0]
            return {
                "status": "WRONG_PATH",
                "expected": ref_value,
                "actual": f"papers/{hit[0]}/{hit[1]}",
                "action": f"Update reference to papers/{hit[0]}/{hit[1]}",
            }
        if bn in sandbox_scripts:
            return {
                "status": "NOT_GRADUATED",
                "sandbox_paths": sandbox_scripts[bn][:3],
                "action": f"Graduate {bn} to papers/{paper_dir.name}/scripts/",
            }
        return {"status": "MISSING", "expected": ref_value, "action": f"Locate or create {ref_value}"}

    basename = ref_value
    local = paper_scripts.get(str(paper_dir), {})
    if basename in local:
        locs = local[basename]
        in_scripts = [l for l in locs if l.startswith(("scripts/", "canonical_run/"))]
        if in_scripts:
            return {"status": "OK", "path": f"papers/{paper_dir.name}/{in_scripts[0]}"}
        return {
            "status": "NONSTANDARD_LOCATION",
            "path": f"papers/{paper_dir.name}/{locs[0]}",
            "action": f"Move {basename} to papers/{paper_dir.name}/scripts/",
        }

    if basename in paper_scripts_flat:
        hits = paper_scripts_flat[basename]
        return {
            "status": "CROSS_PAPER",
            "path": f"papers/{hits[0][0]}/{hits[0][1]}",
            "all": [f"papers/{p}/{r}" for p, r in hits],
        }

    if basename in sandbox_scripts:
        return {
            "status": "NOT_GRADUATED",
            "sandbox_paths": sandbox_scripts[basename][:3],
            "action": f"Graduate {basename} from {sandbox_scripts[basename][0]} to papers/{paper_dir.name}/scripts/",
        }

    if basename in repo_scripts:
        non_sandbox = [p for p in repo_scripts[basename] if "research-sandbox" not in p]
        sandbox_only = [p for p in repo_scripts[basename] if "research-sandbox" in p]
        if non_sandbox:
            ext = classify_external(non_sandbox)
            if ext["status"] == "EXTERNAL_KNOWN":
                return ext
            return {"status": "EXTERNAL", "paths": non_sandbox[:5],
                    "action": f"Consider graduating {basename} to papers/{paper_dir.name}/scripts/ or document external path"}
        if sandbox_only:
            return {
                "status": "NOT_GRADUATED",
                "sandbox_paths": sandbox_only[:3],
                "action": f"Graduate {basename} to papers/{paper_dir.name}/scripts/",
            }

    return {"status": "MISSING", "action": f"Locate or recreate {basename}"}


def audit_paper(paper_dir, paper_scripts, paper_scripts_flat, sandbox_scripts, repo_scripts):
    entry = {
        "paper": paper_dir.name,
        "has_scripts_dir": (paper_dir / "scripts").is_dir(),
        "has_canonical_run": (paper_dir / "canonical_run").is_dir(),
        "scripts_on_disk": sorted(paper_scripts.get(str(paper_dir), {}).keys()),
        "reproduce_issues": [],
        "tex_issues": [],
        "sandbox_mentions": [],
    }

    rep = paper_dir / "REPRODUCE.md"
    tex_files = list(paper_dir.rglob("*.tex"))

    def process(source_name, text, bucket):
        seen = set()
        for ref_type, ref_val, src in extract_script_refs(text, source_name):
            if ref_type == "sandbox_mention":
                entry["sandbox_mentions"].append({"source": source_name, "text": ref_val})
                continue
            key = (ref_type, ref_val)
            if key in seen:
                continue
            seen.add(key)
            res = resolve(ref_type, ref_val, paper_dir, paper_scripts, paper_scripts_flat, sandbox_scripts, repo_scripts)
            if res["status"] in ("OK", "CROSS_PAPER", "EXTERNAL_KNOWN"):
                continue
            # Skip wildcard / malformed refs from LaTeX
            if "*" in ref_val or ref_val.startswith("\\") or "{" in ref_val:
                continue
            bucket.append({"source": source_name, "ref": ref_val, **res})

    if rep.is_file():
        process("REPRODUCE.md", rep.read_text(errors="replace"), entry["reproduce_issues"])

    for tex in tex_files:
        process(tex.name, tex.read_text(errors="replace"), entry["tex_issues"])

    # REPRODUCE path mismatches (wrong paper folder name, same number prefix)
    if rep.is_file():
        text = rep.read_text(errors="replace")
        seen_pm = set()
        for m in re.finditer(r"papers/(\d+_[^/\s`\"']+)", text):
            cited = m.group(1)
            if cited != paper_dir.name and cited.split("_")[0] == paper_dir.name.split("_")[0]:
                if cited not in seen_pm:
                    seen_pm.add(cited)
                    entry["reproduce_issues"].append({
                        "source": "REPRODUCE.md",
                        "ref": m.group(0),
                        "status": "PATH_MISMATCH",
                        "detail": f"Cites papers/{cited} but directory is papers/{paper_dir.name}",
                        "action": f"Update all REPRODUCE paths from papers/{cited} to papers/{paper_dir.name}",
                    })

    entry["issue_count"] = len(entry["reproduce_issues"]) + len(entry["tex_issues"])
    return entry


def main():
    paper_scripts, paper_scripts_flat, sandbox_scripts, repo_scripts = build_indexes()
    findings = []
    all_papers = []

    for pd in paper_dirs():
        entry = audit_paper(pd, paper_scripts, paper_scripts_flat, sandbox_scripts, repo_scripts)
        all_papers.append({
            "paper": entry["paper"],
            "scripts_count": len(entry["scripts_on_disk"]),
            "reproduce_issues": len(entry["reproduce_issues"]),
            "tex_issues": len(entry["tex_issues"]),
            "total_issues": entry["issue_count"],
        })
        if entry["issue_count"] or entry["sandbox_mentions"]:
            findings.append(entry)

    out = {
        "summary": {
            "total_papers": len(all_papers),
            "papers_with_issues": sum(1 for p in all_papers if p["total_issues"] > 0),
            "papers_clean": sum(1 for p in all_papers if p["total_issues"] == 0),
        },
        "all_papers": all_papers,
        "findings": findings,
    }
    json_path = ROOT / "specs" / "GRADUATION_AUDIT_data.json"
    json_path.write_text(json.dumps(out, indent=2))
    print(json.dumps(out["summary"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
