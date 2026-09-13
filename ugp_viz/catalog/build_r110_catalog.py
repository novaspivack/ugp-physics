"""
Generate the Rule 110 glider catalog for fca_sync / afca models.

Two sources are ingested:

1. **Martinez phase catalog** — `_assets/listPhasesR110.txt`.
   Genaro Martinez's verbatim bit patterns for every periodic glider
   phase (ether, A, B, B-, B^, C1, C2, C3, D1, D2, E, E-, F, G, H, Gun).
   Roughly 365 bit patterns plus 29 f4_1 aliases = 394 total.

2. **Cook glider catalog** — Cook (2004) Figure 5 reference data.
   Named gliders A, B, C1, C2, C3, D1, D2, Ebar, F, H with width,
   period (Δt, Δx), and ω-coefficients; plus indexed families Bbar,
   Bhat, En, Gn. Bit patterns for the named gliders are taken from
   the matching Martinez f1_1 / canonical phase.

Output schema (one JSON file per entry, written under
`ugp_viz/catalog/fca_sync/` and copied to `ugp_viz/catalog/afca/`):

    {
        "kind": "<name>",
        "family": "<Martinez family>",   # ether|A|B|Bminus|Bhat|C1|...
        "parent": "<Martinez parent>",   # null | A | B | ...
        "phase": "f1_1" | "f2_1" | "f3_1" | "f4_1",
        "bits": "11111000100110",        # cell pattern
        "ncells": 14,
        "left_tiles":  1,                # ether T3 tiles to the left
        "right_tiles": 0,
        "period_dt": 3,                  # only set for named Cook gliders
        "period_dx": 2,
        "width": 6,
        "omega_a": 1,
        "omega_b": 0,
        "tape_length": 256,              # default placement size
        "ether_padding": 4,              # number of full ether periods left/right
        "source": "martinez 2004" | "cook 2004",
        "notes": "Martinez listPhasesR110.txt; A glider, f1_1."
    }

Re-run as:

    python -m ugp_viz.catalog.build_r110_catalog
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

PACKAGE = Path(__file__).resolve().parent.parent  # ugp_viz/
ASSETS = PACKAGE / "catalog" / "_assets"
MARTINEZ_TXT = ASSETS / "listPhasesR110.txt"
OUT_FCA_SYNC = PACKAGE / "catalog" / "fca_sync" / "r110"
OUT_AFCA = PACKAGE / "catalog" / "afca" / "r110"

# Family display labels in `listPhasesR110.txt`:
#   "A glider", "B glider", "B- glider", "B^ glider", "C1 glider", ...
FAMILY_HEADERS: dict[str, str] = {
    "ether (background periodic)": "ether",
    "A glider": "A",
    "B glider": "B",
    "B- glider": "Bminus",
    "B^ glider": "Bhat",
    "C1 glider": "C1",
    "C2 glider": "C2",
    "C3 glider": "C3",
    "D1 glider": "D1",
    "D2 glider": "D2",
    "E glider": "E",
    "E- glider": "Eminus",
    "F glider": "F",
    "G glider": "G",
    "H glider": "H",
    "Gun glider": "Gun",
}


# Cook Figure 5 named-glider reference data (Cook 2004, Complex Systems 15(1)).
#
# width is the integer representative of the ether-offset class mod 14;
# period_dt / period_dx is (Δt, Δx) per complete period;
# (omega_a, omega_b) are Cook's primitive period coefficients.
COOK_NAMED: dict[str, dict[str, int]] = {
    "A":   {"width": 6,  "period_dt": 3,  "period_dx": 2,   "omega_a": 1, "omega_b": 0},
    "B":   {"width": 8,  "period_dt": 4,  "period_dx": -2,  "omega_a": 0, "omega_b": 1},
    "C1":  {"width": 9,  "period_dt": 7,  "period_dx": 0,   "omega_a": 1, "omega_b": 1},
    "C2":  {"width": 3,  "period_dt": 7,  "period_dx": 0,   "omega_a": 1, "omega_b": 1},
    "C3":  {"width": 11, "period_dt": 7,  "period_dx": 0,   "omega_a": 1, "omega_b": 1},
    "D1":  {"width": 11, "period_dt": 10, "period_dx": 2,   "omega_a": 2, "omega_b": 1},
    "D2":  {"width": 5,  "period_dt": 10, "period_dx": 2,   "omega_a": 2, "omega_b": 1},
    "Ebar":{"width": 7,  "period_dt": 30, "period_dx": -8,  "omega_a": 2, "omega_b": 6},
    "F":   {"width": 1,  "period_dt": 36, "period_dx": -4,  "omega_a": 4, "omega_b": 6},
    "H":   {"width": 11, "period_dt": 92, "period_dx": -18, "omega_a": 8, "omega_b": 17},
}


def _normalize_parent(s: str | None) -> str | None:
    if s is None:
        return None
    s = s.strip()
    if not s:
        return None
    return s


_ALIAS_RE = re.compile(
    r"^(?P<lhs>[A-Za-z0-9\-\^]+)\(((?P<parent>[^,)]+),)?\s*(?P<phase>f\d_\d|A2[^)]*|B2[^)]*)\)"
    r"\s*=\s*(?P<rhs>[A-Za-z0-9\-\^]+)\(((?P<rparent>[^,)]+),)?\s*(?P<rphase>f\d_\d)\)"
    r"\s*$"
)

_ENTRY_RE = re.compile(
    r"^\[(?P<bits>[01]+)\]\s*=\s*"
    r"(?P<family>[A-Za-z0-9\-\^]+)"
    r"\(((?P<parent>[^,)]+),)?\s*(?P<phase>f\d_\d)\)\s*,\s*"
    r"(?P<ncells>\d+)\s*cells"
    r"(?:\s*,\s*(?P<lt>\d+)l-(?P<rt>\d+)r)?"
)

_ETHER_RE = re.compile(
    r"^\[(?P<bits>[01]+)\]\s*=\s*e\(f1_1\)\s*,\s*(?P<ncells>\d+)\s*cells"
)


def parse_martinez_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    entries: list[dict[str, Any]] = []
    aliases: list[dict[str, str]] = []
    current_family: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("//"):
            continue
        # Family headers ("A glider", "B- glider", "ether (background ...)" etc.)
        for header, fam in FAMILY_HEADERS.items():
            if line.lower() == header.lower():
                current_family = fam
                break
        # Ether row is special (no parent / no left/right counts)
        m_e = _ETHER_RE.match(line)
        if m_e:
            entries.append({
                "family": "ether",
                "parent": None,
                "phase": "f1_1",
                "bits": m_e.group("bits"),
                "ncells": int(m_e.group("ncells")),
                "left_tiles": None,
                "right_tiles": None,
                "source": "martinez 2004",
            })
            continue
        m = _ENTRY_RE.match(line)
        if m:
            fam = m.group("family").strip()
            fam_norm = {"B-": "Bminus", "B^": "Bhat", "E-": "Eminus",
                        }.get(fam, fam)
            entries.append({
                "family": fam_norm,
                "parent": _normalize_parent(m.group("parent")),
                "phase": m.group("phase"),
                "bits": m.group("bits"),
                "ncells": int(m.group("ncells")),
                "left_tiles": int(m.group("lt")) if m.group("lt") else None,
                "right_tiles": int(m.group("rt")) if m.group("rt") else None,
                "source": "martinez 2004",
            })
            continue
        m_a = _ALIAS_RE.match(line)
        if m_a:
            aliases.append({
                "lhs_family": m_a.group("lhs"),
                "lhs_parent": _normalize_parent(m_a.group("parent")),
                "lhs_phase": m_a.group("phase"),
                "rhs_family": m_a.group("rhs"),
                "rhs_parent": _normalize_parent(m_a.group("rparent")),
                "rhs_phase": m_a.group("rphase"),
            })
            continue
    return {"entries": entries, "aliases": aliases}


# Cook's ether unit cell in the rule110-lean coordinate system is
# `10011011111000`. Martinez phases are quoted on the Martinez ether
# `11111000100110`. The two strings are the same period-14 ether at
# different rotations: rotate Cook by 5 cells to match Martinez. We
# store the bits as Martinez wrote them; downstream code can rotate
# at injection time if it wants Cook alignment.
MARTINEZ_ETHER = "11111000100110"


def _build_tape(bits: str, *, length: int = 256,
                ether: str = MARTINEZ_ETHER) -> str:
    """Pad the glider pattern with the ether on both sides up to length."""
    if length <= len(bits):
        return bits[:length]
    pad = length - len(bits)
    left = pad // 2
    right = pad - left
    e = (ether * ((max(left, right) // len(ether)) + 2))
    return e[:left] + bits + e[:right]


def _safe_name(family: str, parent: str | None, phase: str) -> str:
    pieces = ["martinez", family]
    if parent:
        pieces.append(parent.replace("/", "_"))
    pieces.append(phase)
    return "_".join(pieces)


def _write_entry(out_dir: Path, *, name: str, payload: dict[str, Any]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"{name}.json"
    p.write_text(json.dumps(payload, indent=2))
    return p


def build_catalog(*, tape_length: int = 256) -> dict[str, int]:
    parsed = parse_martinez_file(MARTINEZ_TXT)
    entries = parsed["entries"]
    counts = {"martinez": 0, "cook": 0, "aliases": len(parsed["aliases"])}

    # Wipe-and-rebuild policy for the r110/ sub-catalog (idempotent).
    for out_dir in (OUT_FCA_SYNC, OUT_AFCA):
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

    # --- Martinez phases ---
    for e in entries:
        name = _safe_name(e["family"], e["parent"], e["phase"])
        tape = _build_tape(e["bits"], length=tape_length)
        payload = {
            "kind": name,
            "family": e["family"],
            "parent": e["parent"],
            "phase": e["phase"],
            "bits": e["bits"],
            "ncells": e["ncells"],
            "left_tiles": e["left_tiles"],
            "right_tiles": e["right_tiles"],
            "tape_length": tape_length,
            "tape": tape,
            "ether": MARTINEZ_ETHER,
            "source": e["source"],
            "notes": (
                "Martinez listPhasesR110.txt; "
                f"family={e['family']}, parent={e['parent']}, phase={e['phase']}."
            ),
        }
        _write_entry(OUT_FCA_SYNC, name=name, payload=payload)
        _write_entry(OUT_AFCA, name=name, payload=payload)
        counts["martinez"] += 1

    # --- Aliases ---
    if parsed["aliases"]:
        alias_payload = {
            "kind": "_martinez_aliases",
            "description": (
                "Equivalences between Martinez phase keys "
                "(LHS = RHS) drawn from listPhasesR110.txt."
            ),
            "aliases": parsed["aliases"],
            "source": "martinez 2004",
        }
        _write_entry(OUT_FCA_SYNC, name="_martinez_aliases", payload=alias_payload)
        _write_entry(OUT_AFCA, name="_martinez_aliases", payload=alias_payload)

    # --- Cook named gliders (with bit patterns from Martinez f1_1 where possible) ---
    martinez_lookup: dict[tuple[str, str | None, str], dict[str, Any]] = {
        (e["family"], e["parent"], e["phase"]): e for e in entries
    }

    def _bits_for_cook(name: str) -> tuple[str, str | None]:
        # Map Cook name -> (Martinez family, Martinez parent) for the f1_1 bits.
        cook_to_martinez: dict[str, tuple[str, str | None]] = {
            "A":   ("A", None),
            "B":   ("B", None),
            "C1":  ("C1", "A"),
            "C2":  ("C2", "A"),
            "C3":  ("C3", "A"),
            "D1":  ("D1", "A"),
            "D2":  ("D2", "A"),
            "Ebar":("Eminus", "A"),
            "F":   ("F", "A"),
            "H":   ("H", "A"),
        }
        fam, par = cook_to_martinez[name]
        entry = martinez_lookup.get((fam, par, "f1_1"))
        if entry is None:
            return "", None
        return entry["bits"], "martinez f1_1 of " + fam + (f"({par})" if par else "")

    cook_index: list[dict[str, Any]] = []
    for cook_name, props in COOK_NAMED.items():
        bits, src = _bits_for_cook(cook_name)
        if not bits:
            continue
        tape = _build_tape(bits, length=tape_length)
        name = f"cook_{cook_name}"
        payload = {
            "kind": name,
            "cook_name": cook_name,
            "family": cook_name,
            "bits": bits,
            "ncells": len(bits),
            "width": props["width"],
            "period_dt": props["period_dt"],
            "period_dx": props["period_dx"],
            "omega_a": props["omega_a"],
            "omega_b": props["omega_b"],
            "tape_length": tape_length,
            "tape": tape,
            "ether": MARTINEZ_ETHER,
            "source": "cook 2004 (figure 5)",
            "bit_source": src,
            "notes": (
                f"Cook (2004) named glider {cook_name}. Width "
                f"{props['width']} cells; period (Δt,Δx)=({props['period_dt']},"
                f"{props['period_dx']}); ω-coeffs (ω_A,ω_B)=({props['omega_a']},"
                f"{props['omega_b']}). Bit pattern taken from {src}."
            ),
        }
        _write_entry(OUT_FCA_SYNC, name=name, payload=payload)
        _write_entry(OUT_AFCA, name=name, payload=payload)
        cook_index.append({"name": name, **props})
        counts["cook"] += 1

    # Cook indexed families (Bbar_n, Bhat_n, En, Gn) — store affine widths
    # only; the catalog manager exposes them via list_entries() so users
    # can inspect the formulas.
    indexed: dict[str, dict[str, Any]] = {
        "Bbar": {"width_formula": "13 + 9*n", "period_dt": 12, "period_dx": -6,  "omega_a": 0, "omega_b": 3},
        "Bhat": {"width_formula": "2 + 9*n",  "period_dt": 12, "period_dx": -6,  "omega_a": 0, "omega_b": 3},
        "En":   {"width_formula": "11 + 8*n", "period_dt": 15, "period_dx": -4,  "omega_a": 1, "omega_b": 3},
        "Gn":   {"width_formula": "2 + 8*n",  "period_dt": 42, "period_dx": -14, "omega_a": 2, "omega_b": 9},
    }
    payload = {
        "kind": "_cook_indexed_families",
        "description": (
            "Cook (2004) Figure 5 affine glider families (width depends on "
            "an integer index n; period and ω-coefficients are independent "
            "of n)."
        ),
        "families": indexed,
        "source": "cook 2004 (figure 5)",
    }
    _write_entry(OUT_FCA_SYNC, name="_cook_indexed_families", payload=payload)
    _write_entry(OUT_AFCA, name="_cook_indexed_families", payload=payload)

    # Index manifest
    manifest = {
        "martinez_count": counts["martinez"],
        "cook_count": counts["cook"],
        "alias_count": counts["aliases"],
        "ether_pattern": MARTINEZ_ETHER,
        "tape_length": tape_length,
        "cook_named": [d["name"] for d in cook_index],
    }
    _write_entry(OUT_FCA_SYNC, name="_index", payload=manifest)
    _write_entry(OUT_AFCA, name="_index", payload=manifest)

    return counts


if __name__ == "__main__":
    c = build_catalog()
    print(json.dumps(c, indent=2))
