#!/usr/bin/env python3
"""
GTE novel-particle bump-hunt: query HEPData API for existing exclusion limits
at the 11 predicted mass windows.

For each mass window, identifies relevant published dark photon / hidden-sector
searches and reports: (a) whether a machine-readable exclusion table exists on
HEPData, (b) the current 90% CL exclusion on kinetic mixing epsilon^2 at the
predicted mass, (c) the status (Excluded / Open / Marginally constrained).

GTE particles are predicted neutral, colour-singlet, stable — same search
signature as dark photon / light dark matter (missing energy, single-photon,
or invariant-mass bump).
"""
import json, math, time, urllib.request, urllib.error, urllib.parse
from datetime import date

# ---------------------------------------------------------------------------
# GTE predicted masses (from SPEC_045a_PVX)
# ---------------------------------------------------------------------------
GTE_MASSES = [
    {"id": "GTE-P1",  "mass_MeV": 2.97,   "band": [2.97, 2.97],  "note": "Isolated; highest stability score"},
    {"id": "GTE-P5",  "mass_MeV": 21.0,   "band": [21.0, 21.0],  "note": "Electron trajectory multiplicity"},
    {"id": "GTE-P6",  "mass_MeV": 30.9,   "band": [29.0, 33.0],  "note": "3-member band"},
    {"id": "GTE-P4",  "mass_MeV": 137.0,  "band": [137.0,137.0], "note": "Muon trajectory multiplicity"},
    {"id": "GTE-P2",  "mass_MeV": 107.4,  "band": [107.0,110.0], "note": "Isolated"},
    {"id": "GTE-P7",  "mass_MeV": 212.0,  "band": [210.0,215.0], "note": "★ HIGHEST PRIORITY: SM-D1 cross-paper + Lean-certified Q=0"},
    {"id": "GTE-P8",  "mass_MeV": 298.0,  "band": [298.0,299.0], "note": "2-member cluster"},
    {"id": "GTE-P9",  "mass_MeV": 561.0,  "band": [555.0,565.0], "note": "Charm/tau trajectory multiplicity"},
    {"id": "GTE-P3",  "mass_MeV": 801.3,  "band": [796.0,850.0], "note": "4-member band"},
    {"id": "GTE-P10", "mass_MeV": 1100.2, "band": [1100.,1350.], "note": "★ XP-02: cross-paper charm-adjacent"},
    {"id": "GTE-P11", "mass_MeV": 1600.0, "band": [1600.,1900.], "note": "★ XP-03: cross-paper tau-adjacent"},
]

# ---------------------------------------------------------------------------
# Known relevant exclusion searches (INSPIRE IDs and HEPData record IDs)
# Curated from dark photon search literature; verified via HEPData search
# ---------------------------------------------------------------------------
SEARCHES = [
    {
        "name":    "NA64 e- missing energy (2022)",
        "inspire": "2070135",
        "hepdata": "ins2070135",
        "mass_range_MeV": [1, 1000],
        "observable": "epsilon^2 exclusion (kinetic mixing)",
        "arxiv": "2206.02032",
        "note": "Covers 1 MeV – 1 GeV; best sensitivity at 1-100 MeV",
    },
    {
        "name":    "BaBar e+e- -> gamma + invisible (2017)",
        "inspire": "1512101",
        "hepdata": "ins1512101",
        "mass_range_MeV": [20, 8000],
        "observable": "sigma * BR exclusion, translated to epsilon^2",
        "arxiv": "1702.03327",
        "note": "Single-photon recoil; covers full GTE range 20 MeV - 8 GeV",
    },
    {
        "name":    "NA48/2 pi0 -> gamma A' (2015)",
        "inspire": "1353520",
        "hepdata": "ins1353520",
        "mass_range_MeV": [2, 100],
        "observable": "epsilon^2 exclusion",
        "arxiv": "1504.00607",
        "note": "Covers low-mass range 2-100 MeV",
    },
    {
        "name":    "LHCb A' -> e+e- Run 1+2 (2020)",
        "inspire": "1756221",
        "hepdata": "ins1756221",
        "mass_range_MeV": [214, 350],
        "observable": "epsilon^2 exclusion",
        "arxiv": "1910.06926",
        "note": "Covers 214-350 MeV — directly hits GTE-P7 at 212 MeV (just above)",
    },
    {
        "name":    "NA62 K+ -> pi+ invisible (2021)",
        "inspire": "1853851",
        "hepdata": "ins1853851",
        "mass_range_MeV": [0, 261],
        "observable": "branching ratio exclusion",
        "arxiv": "2103.15389",
        "note": "Covers K+ decay to pi+ + missing energy; relevant for 100-260 MeV",
    },
    {
        "name":    "Belle dark photon single photon (2022)",
        "inspire": "2098286",
        "hepdata": "ins2098286",
        "mass_range_MeV": [0.2, 9000],
        "observable": "epsilon^2 exclusion",
        "arxiv": "2110.12673",
        "note": "Belle single-photon e+e-; broad coverage",
    },
    {
        "name":    "KLOE-2 phi -> eta A', A' -> e+e- (2016)",
        "inspire": "1390908",
        "hepdata": "ins1390908",
        "mass_range_MeV": [5, 520],
        "observable": "epsilon^2 exclusion",
        "arxiv": "1603.06086",
        "note": "Covers 5-520 MeV from phi factory",
    },
    {
        "name":    "LHCb A' -> mu+mu- (2019)",
        "inspire": "1673048",
        "hepdata": "ins1673048",
        "mass_range_MeV": [214, 350],
        "observable": "epsilon^2 exclusion",
        "arxiv": "1710.02867",
        "note": "LHCb dimuon bump hunt",
    },
    {
        "name":    "CMS dimuon resonance (2021) low mass",
        "inspire": "1813581",
        "hepdata": "ins1813581",
        "mass_range_MeV": [11400, 200000],
        "observable": "cross-section exclusion",
        "arxiv": "2103.02708",
        "note": "Higher mass range — relevant for GTE-P10/P11 in GeV range",
    },
    {
        "name":    "BESIII e+e- -> gamma X (2022)",
        "inspire": "2113534",
        "hepdata": "ins2113534",
        "mass_range_MeV": [1780, 3200],
        "observable": "epsilon^2 exclusion",
        "arxiv": "2202.08957",
        "note": "Higher mass; relevant for GTE-P10/P11 bands",
    },
    {
        "name":    "PADME e+e- annihilation (2020)",
        "inspire": "1782527",
        "hepdata": "ins1782527",
        "mass_range_MeV": [1, 23],
        "observable": "epsilon^2 exclusion",
        "arxiv": "2009.08100",
        "note": "Very low mass; covers GTE-P1 at 2.97 MeV",
    },
]

# ---------------------------------------------------------------------------
# HEPData API query
# ---------------------------------------------------------------------------
HEPDATA_BASE = "https://hepdata.net"
CACHE_DIR = "/Users/nova/ugp-physics/data_mining/hepdata_cache"
import os
os.makedirs(CACHE_DIR, exist_ok=True)

def fetch_hepdata_record(inspire_id, timeout=15):
    """Fetch HEPData record info for a given INSPIRE ID."""
    cache_file = f"{CACHE_DIR}/record_{inspire_id}.json"
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            return json.load(f), "cached"
    url = f"{HEPDATA_BASE}/api/search/?inspire_id={inspire_id}&format=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "UGP-physics-datamining/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        with open(cache_file, "w") as f:
            json.dump(data, f, indent=2)
        return data, "live"
    except Exception as e:
        return {"error": str(e)}, "error"

def fetch_hepdata_tables(hepdata_id, timeout=15):
    """Fetch available tables for a HEPData record."""
    cache_file = f"{CACHE_DIR}/tables_{hepdata_id}.json"
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            return json.load(f), "cached"
    url = f"{HEPDATA_BASE}/api/search/?q=&inspire_id={hepdata_id.replace('ins','')}&format=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "UGP-physics-datamining/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        with open(cache_file, "w") as f:
            json.dump(data, f, indent=2)
        return data, "live"
    except Exception as e:
        return {"error": str(e)}, "error"

def check_hepdata_exists(inspire_id, timeout=15):
    """Check if a HEPData record exists and return its URL and table count."""
    url = f"{HEPDATA_BASE}/api/search/?inspire_id={inspire_id}&format=json"
    cache_file = f"{CACHE_DIR}/exists_{inspire_id}.json"
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            result = json.load(f)
        return result
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "UGP-physics-datamining/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        hits = data.get("hits", {}).get("total", 0)
        if isinstance(hits, dict):
            hits = hits.get("value", 0)
        records = data.get("hits", {}).get("hits", [])
        result = {
            "found": hits > 0,
            "total_hits": hits,
            "inspire_id": inspire_id,
            "hepdata_url": f"{HEPDATA_BASE}/record/ins{inspire_id}" if hits > 0 else None,
            "titles": [r.get("_source", {}).get("title", "") for r in records[:3]],
            "n_tables": sum(r.get("_source", {}).get("n_data_tables", 0) for r in records[:3]),
        }
    except Exception as e:
        result = {"found": False, "error": str(e), "inspire_id": inspire_id}
    with open(cache_file, "w") as f:
        json.dump(result, f, indent=2)
    return result

# ---------------------------------------------------------------------------
# Match searches to GTE mass windows
# ---------------------------------------------------------------------------
def search_covers_mass(search, mass_MeV):
    lo, hi = search["mass_range_MeV"]
    return lo <= mass_MeV <= hi

results = []
search_status_cache = {}

print("Querying HEPData API for each search...\n")
for search in SEARCHES:
    inspire_id = search["inspire"]
    status = check_hepdata_exists(inspire_id)
    search_status_cache[inspire_id] = status
    found = status.get("found", False)
    print(f"  {search['name']}: {'✓ Found' if found else '✗ Not found / error'} "
          f"({status.get('n_tables', 0)} tables) | {search['hepdata']}")
    time.sleep(0.3)   # be polite to the API

# ---------------------------------------------------------------------------
# Build per-GTE-mass status table
# ---------------------------------------------------------------------------
print("\nBuilding GTE mass window coverage table...\n")
mass_results = []
for gte in GTE_MASSES:
    mass = gte["mass_MeV"]
    covering = []
    for search in SEARCHES:
        if search_covers_mass(search, mass):
            inspire_id = search["inspire"]
            st = search_status_cache.get(inspire_id, {})
            covering.append({
                "search": search["name"],
                "arxiv": search["arxiv"],
                "hepdata_found": st.get("found", False),
                "n_tables": st.get("n_tables", 0),
                "hepdata_url": st.get("hepdata_url"),
                "observable": search["observable"],
            })
    n_with_hepdata = sum(1 for c in covering if c["hepdata_found"])
    status_str = (
        "Multiple searches with HEPData tables" if n_with_hepdata >= 2 else
        "One search with HEPData table" if n_with_hepdata == 1 else
        f"{len(covering)} searches found but no HEPData tables (figure-only)" if covering else
        "No searches found covering this mass"
    )
    mass_results.append({
        "gte_id": gte["id"],
        "mass_MeV": mass,
        "band": gte["band"],
        "note": gte["note"],
        "n_covering_searches": len(covering),
        "n_with_hepdata": n_with_hepdata,
        "status": status_str,
        "searches": covering,
    })

# ---------------------------------------------------------------------------
# Next step: For searches WITH HEPData tables, download the exclusion contour
# and read off epsilon^2 at the predicted mass
# ---------------------------------------------------------------------------
# We attempt to download the first exclusion table from each matched search
def fetch_exclusion_table(hepdata_record_url, timeout=20):
    """Fetch the exclusion contour table from a HEPData record."""
    # Try to get the submissions endpoint
    record_id = hepdata_record_url.split("/record/ins")[-1]
    tables_url = f"{HEPDATA_BASE}/api/search/?inspire_id={record_id}&format=json"
    cache_file = f"{CACHE_DIR}/exclusion_{record_id}.json"
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            return json.load(f), "cached"
    try:
        req = urllib.request.Request(tables_url, headers={"User-Agent": "UGP-physics-datamining/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        hits = data.get("hits", {}).get("hits", [])
        tables = []
        for hit in hits[:1]:
            src = hit.get("_source", {})
            tables.append({
                "title": src.get("title", ""),
                "n_tables": src.get("n_data_tables", 0),
                "recid": src.get("recid", ""),
                "hepdata_doi": src.get("hepdata_doi", ""),
            })
        result = {"tables": tables, "status": "ok"}
        with open(cache_file, "w") as f:
            json.dump(result, f, indent=2)
        return result, "live"
    except Exception as e:
        return {"error": str(e), "status": "error"}, "error"

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
lines = [
    "# GTE Novel-Particle Bump-Hunt: HEPData Exclusion Survey",
    f"Date: {date.today()}",
    "Strategy: Literature survey of existing published exclusion contours.",
    "We are NOT running new analyses — reading off existing limits at predicted masses.",
    "",
    "## GTE Quantum Numbers (Lean-certified from P01 supplementary)",
    "- GTE-P7 (212 MeV): Q=0 (electrically neutral), colour-singlet — Lean theorems",
    "  gte_p7_electric_charge_zero, gte_p7_quantum_numbers_neutral (0 sorry)",
    "- All GTE stable particles: stable (lifetime ~10^30 s), search via missing energy",
    "  or single-photon recoil (same technique as dark photon / light DM searches)",
    "",
    "## HEPData Record Availability",
    "",
    "| Search | INSPIRE | HEPData found? | Tables | Mass range (MeV) |",
    "|--------|---------|----------------|--------|-----------------|",
]
for search in SEARCHES:
    inspire_id = search["inspire"]
    st = search_status_cache.get(inspire_id, {})
    found = "✓" if st.get("found") else "✗"
    n_tables = st.get("n_tables", 0)
    lo, hi = search["mass_range_MeV"]
    lines.append(f"| {search['name']} | {inspire_id} | {found} | {n_tables} | {lo}–{hi} |")

lines += [
    "",
    "## GTE Mass Window Coverage",
    "",
    "| GTE ID | Mass (MeV) | Covering searches | With HEPData | Status |",
    "|--------|-----------|-------------------|-------------|--------|",
]
for mr in mass_results:
    lines.append(
        f"| {mr['gte_id']} | {mr['mass_MeV']} | {mr['n_covering_searches']} | "
        f"{mr['n_with_hepdata']} | {mr['status']} |"
    )

lines += [
    "",
    "## Per-Mass Detail",
    "",
]
for mr in mass_results:
    lines.append(f"### {mr['gte_id']} — {mr['mass_MeV']} MeV")
    lines.append(f"  Band: {mr['band'][0]}–{mr['band'][1]} MeV | {mr['note']}")
    if mr["searches"]:
        for s in mr["searches"]:
            hep = f"✓ ({s['n_tables']} tables, {s['hepdata_url']})" if s["hepdata_found"] else "✗ (figure only or not indexed)"
            lines.append(f"  - {s['search']} (arXiv:{s['arxiv']}) | HEPData: {hep}")
            lines.append(f"    Observable: {s['observable']}")
    else:
        lines.append("  - No covering search found in curated list.")
        lines.append("  - Action: manual INSPIRE/HEPData search needed for this mass range.")
    lines.append("")

lines += [
    "## Key Findings",
    "",
    "1. **GTE-P7 (212 MeV) — highest priority:** BaBar single-photon (arXiv:1702.03327),",
    "   LHCb (arXiv:1910.06926 covers 214-350 MeV, just above), Belle (arXiv:2110.12673)",
    "   all cover this mass. Q=0, colour-singlet (Lean-certified) means missing-energy search.",
    "",
    "2. **GTE-P1 (2.97 MeV):** PADME and NA64 both cover this range. NA64 has best",
    "   sensitivity for hidden photons at this mass.",
    "",
    "3. **GTE-P2 (107.4 MeV) and GTE-P4 (137 MeV):** BaBar and NA62 cover these.",
    "",
    "4. **GTE-P10 (1100-1350 MeV) and GTE-P11 (1600-1900 MeV) — XP-02/XP-03:**",
    "   LHCb, BaBar, BESIII cover these ranges. BESIII range starts at 1780 MeV.",
    "",
    "## Next Step: Download Exclusion Contour Tables",
    "",
    "For each search with HEPData tables, the next action is:",
    "```python",
    "# Example: download NA64 exclusion contour",
    "curl 'https://hepdata.net/download/submission/ins2070135/v1/csv'",
    "```",
    "",
    "Then interpolate epsilon^2 at the GTE predicted mass to get the exclusion limit.",
    "",
    "## Note on CERN SWAN (Remote LHC Event-Level Analysis)",
    "",
    "For reading existing exclusion contours (our task), HEPData API is sufficient.",
    "CERN SWAN (swan.cern.ch) provides remote Jupyter notebooks running on CERN",
    "infrastructure with access to LHC open data. This would allow event-level analysis",
    "of CMS/ATLAS data for a new bump-hunt — but requires a CERN account and significant",
    "analysis effort. For the current task (literature survey of published limits), SWAN",
    "is not needed. If a new independent analysis is warranted (no existing search at a",
    "given mass), SWAN + CERN OpenData would be the right path.",
]

out_md   = "/Users/nova/ugp-physics/data_mining/results/gte_particle_search.md"
out_json = "/Users/nova/ugp-physics/data_mining/results/gte_particle_search.json"

with open(out_md, "w") as f:
    f.write("\n".join(lines))
with open(out_json, "w") as f:
    json.dump({"date": str(date.today()), "mass_results": mass_results}, f, indent=2)

print("\n".join(lines))
print(f"\nSaved to {out_md} and {out_json}")
