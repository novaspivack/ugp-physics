#!/usr/bin/env python3
"""
gte_stability_api.py — GTE Particle Candidate Lookup API

Looks up GTE particle candidates from the canonical candidates.csv database by mass (MeV),
returning stability score, lifetime, n-value, tier, confidence, and quantum numbers.

Usage:
    python tools/gte_stability_api.py --mass 105.7
    python tools/gte_stability_api.py --mass 105.7 --tolerance 2.0
    python tools/gte_stability_api.py --mass 105.7 --top-n 5
    python tools/gte_stability_api.py --mass 105.7 --tier Green
    python tools/gte_stability_api.py --mass 105.7 --output results.json

Arguments:
    --mass         Target mass in MeV (required)
    --tolerance    Search window half-width in MeV (default: 1.0)
    --top-n        Maximum number of results to return (default: 10)
    --tier         Filter by tier: Green, Yellow, Red, or all (default: all)
    --candidates   Path to candidates.csv (default: papers/02_GTE_spectrum/candidates.csv)
    --output       Write JSON output to FILE instead of stdout

Output (JSON):
    {
        "query": {"mass_MeV": 105.7, "tolerance_MeV": 1.0},
        "n_matches": 3,
        "candidates": [
            {
                "id": "particle_muon",
                "mass_MeV": 105.658,
                "delta_MeV": 0.042,
                "tier": "Green",
                "confidence": 0.983,
                "stability_score": 1.0,
                "gte_score": 1.0,
                "lifetime_s": 2.197e-6,
                "n_value": 73,
                "a": 1, "b": 73, "c": 823,
                "generation": 1,
                "canonical_match": "muon",
                "is_rejected": false,
                "is_novel_prediction": false
            },
            ...
        ]
    }

Column definitions (candidates.csv):
    id                  Unique candidate identifier
    classification_color  Tier: Green (high-confidence) / Yellow / Red
    confidence          GTE match confidence [0, 1]
    mass_mev_calibrated UCL-calibrated mass (MeV); preferred for matching
    mass_mev            Raw GTE mass (MeV); used if calibrated not available
    lifetime_s          Predicted lifetime (seconds); 1e30 = effectively stable
    n_value             GTE n-value (integer; lower = more fundamental)
    a, b, c             GTE trajectory triple
    generation          Lepton/quark generation
    gte_score           GTE internal score [0, 1]
    stability_score     Predicted stability [0, 1]; 1.0 = stable
    viability_score     Viability metric [0, 1]
    canonical_match     PDG particle name if matched to SM; empty if novel
    is_rejected         True if excluded from top-tier by quality filters
    is_novel_prediction Computed: True if canonical_match is empty and not is_rejected

Database:
    papers/02_GTE_spectrum/candidates.csv
    1,000,035 candidates — SHA256: 5c113e62468d19fbda73d9df06a3740f1dbd7609c8eee6ecb1ac6039f38f72db

Source: papers/02_GTE_spectrum/Particle_Spectrum_From_UGP_Paper.tex
        papers/02_GTE_spectrum/REPRODUCE.md
"""

from __future__ import annotations
import argparse
import json
import os
import sys

# Default path relative to repo root
_DEFAULT_CANDIDATES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "papers", "02_GTE_spectrum", "candidates.csv",
)

_TIER_ORDER = {"Green": 0, "Yellow": 1, "Red": 2}


def _effective_mass(row: dict) -> float:
    """Return the best available mass (calibrated preferred, raw fallback)."""
    cal = row.get("mass_mev_calibrated", "")
    if cal and cal not in ("", "nan", "None"):
        try:
            return float(cal)
        except (ValueError, TypeError):
            pass
    raw = row.get("mass_mev", row.get("mass_mev_raw", ""))
    if raw:
        try:
            return float(raw)
        except (ValueError, TypeError):
            pass
    raise ValueError(f"No valid mass found in row: {row.get('id', '?')}")


def lookup_candidates(
    mass_mev: float,
    tolerance_mev: float = 1.0,
    top_n: int = 10,
    tier_filter: str | None = None,
    candidates_path: str = _DEFAULT_CANDIDATES,
) -> dict:
    """
    Look up GTE candidates within `tolerance_mev` of `mass_mev`.

    Returns structured dict suitable for JSON serialization.

    Raises FileNotFoundError if candidates.csv is not present.
    """
    if not os.path.exists(candidates_path):
        raise FileNotFoundError(
            f"candidates.csv not found at: {candidates_path}\n"
            "Run the discovery engine (Step 1 in papers/02_GTE_spectrum/REPRODUCE.md) "
            "or verify the file path with --candidates."
        )

    import csv

    results = []
    with open(candidates_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                m = _effective_mass(row)
            except ValueError:
                continue
            if abs(m - mass_mev) > tolerance_mev:
                continue
            tier = row.get("classification_color", "Unknown")
            if tier_filter and tier_filter != "all" and tier != tier_filter:
                continue
            canonical = row.get("canonical_match", "").strip()
            is_rejected = row.get("is_rejected", "False").strip().lower() in ("true", "1")
            is_novel = (not canonical) and (not is_rejected)
            try:
                lifetime = float(row.get("lifetime_s", "nan"))
            except (ValueError, TypeError):
                lifetime = None
            try:
                n_value = int(float(row.get("n_value", "0")))
            except (ValueError, TypeError):
                n_value = None
            entry = {
                "id": row.get("id", ""),
                "mass_MeV": round(m, 6),
                "delta_MeV": round(abs(m - mass_mev), 6),
                "tier": tier,
                "confidence": _safe_float(row.get("confidence")),
                "stability_score": _safe_float(row.get("stability_score")),
                "gte_score": _safe_float(row.get("gte_score")),
                "viability_score": _safe_float(row.get("viability_score")),
                "lifetime_s": lifetime,
                "n_value": n_value,
                "a": _safe_int(row.get("a")),
                "b": _safe_int(row.get("b")),
                "c": _safe_int(row.get("c")),
                "generation": _safe_int(row.get("generation")),
                "canonical_match": canonical if canonical else None,
                "is_rejected": is_rejected,
                "is_novel_prediction": is_novel,
            }
            results.append(entry)

    results.sort(key=lambda x: (
        _TIER_ORDER.get(x["tier"], 99),
        x["delta_MeV"],
    ))
    results = results[:top_n]

    return {
        "query": {
            "mass_MeV": mass_mev,
            "tolerance_MeV": tolerance_mev,
            "tier_filter": tier_filter or "all",
        },
        "n_matches": len(results),
        "candidates": results,
        "database": {
            "path": candidates_path,
            "sha256": "5c113e62468d19fbda73d9df06a3740f1dbd7609c8eee6ecb1ac6039f38f72db",
            "total_candidates": 1_000_035,
            "note": "Verify SHA256 against papers/02_GTE_spectrum/REPRODUCE.md before production use",
        },
    }


def _safe_float(val) -> float | None:
    if val is None or str(val).strip() in ("", "nan", "None"):
        return None
    try:
        return round(float(val), 6)
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> int | None:
    if val is None or str(val).strip() in ("", "nan", "None"):
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="GTE Particle Candidate Lookup API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python tools/gte_stability_api.py --mass 105.658 --tier Green",
    )
    parser.add_argument("--mass", type=float, required=True,
                        help="Target mass in MeV")
    parser.add_argument("--tolerance", type=float, default=1.0,
                        help="Search window half-width in MeV (default: 1.0)")
    parser.add_argument("--top-n", type=int, default=10,
                        help="Maximum number of results (default: 10)")
    parser.add_argument("--tier", choices=["Green", "Yellow", "Red", "all"],
                        default="all",
                        help="Filter by tier (default: all)")
    parser.add_argument("--candidates", default=_DEFAULT_CANDIDATES,
                        help=f"Path to candidates.csv (default: {_DEFAULT_CANDIDATES})")
    parser.add_argument("--output", metavar="FILE",
                        help="Write JSON output to FILE instead of stdout")

    args = parser.parse_args()

    try:
        result = lookup_candidates(
            mass_mev=args.mass,
            tolerance_mev=args.tolerance,
            top_n=args.top_n,
            tier_filter=args.tier if args.tier != "all" else None,
            candidates_path=args.candidates,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    output = json.dumps(result, indent=2)

    if args.output:
        with open(args.output, "w") as fh:
            fh.write(output + "\n")
        print(
            f"Found {result['n_matches']} candidate(s). Results written to {args.output}",
            file=sys.stderr,
        )
    else:
        print(output)


if __name__ == "__main__":
    main()
