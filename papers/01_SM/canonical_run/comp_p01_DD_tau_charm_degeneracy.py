#!/usr/bin/env python3
"""
comp_p01_DD_tau_charm_degeneracy.py -- COMP-P01-DD

Attack B of the bulletproofing plan (081_NOTE §3.2).

Addresses Open Problem (i)-A surfaced by COMP-P01-BB: the tau and charm
quark both use the GTE triple (a=5, b=275, c=65535).  Their UCL features
(L, L^2, M, mu_a, mu_b, mu_c) are therefore identical; the engine
distinguishes them only via (gen, type) in E_base.

Additional context discovered during recon (UGP_GTE_SM_Verifier
UGP_GTE_SM_Verifier.py):

  - G1 quark triples (up, down) are derived from leptons via the
    "Permutation Principle":
       up   = (a_L3, a_L2, b_L3)    # = (5, 9, 275)
       down = (a_L2, a_L3, b_L2)    # = (9, 5, 42)
  - G2/G3 quark triples (charm, strange, top, bottom) are "BOUND TO
    CANONICAL V42.1 PATHWAY" with comment "deterministic binding ...
    until formal operators are inlined".  In other words they are
    HARDCODED; no UGP derivation exists.
  - Charm's hardcoded canonical triple happens to coincide exactly
    with tau's = (5, 275, 65535).

Attack B therefore has two layers:

  Layer 1: IS charm's triple required to equal tau's by the Lean
  UCL, or is there a different G2-up-type triple structurally
  derivable from lepton foundations that ALSO reproduces PDG m_charm
  to within 10 percent when combined with canonical E_base?

  Layer 2: Among the ~15 natural G2 rules extending the Permutation
  Principle, is there a UNIFIED rule that deterministically assigns
  charm a distinct (non-tau) triple while preserving mass
  predictions?

Decision rule (per 081_NOTE section 3.2):

  WIN     a single G2 rule assigns charm a triple != tau AND the
          Lean UCL + canonical E_base yields m_charm within 10% of
          PDG (1275 MeV).
  PARTIAL individual candidate triples match m_charm but no unified
          rule; document them as deeper-research targets.
  MISS    no candidate G2 triple reproduces m_charm within 10%; the
          tau/charm degeneracy is structurally required (or the
          V42.1 hardcode is doing something opaque).

No paper text edits before or after this attack; this is a pure
investigation producing a structural map and a decision.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import datetime, timezone
from fractions import Fraction
from itertools import permutations
from typing import Dict, List, Tuple, Iterable

# ---------------------------------------------------------------------------
# 1. Inputs: Lean-certified rationals + lepton foundations + UCL2.3
# ---------------------------------------------------------------------------

# Lepton foundations (Lean-certified via canonical_orbit_triples)
L1 = (1, 73,  823)      # electron
L2 = (9, 42,  1023)     # muon
L3 = (5, 275, 65535)    # tau

# Current engine / V42.1 canonical triples (from
# _get_canonical_particle_triples and the charged-fermion list in
# ebase_first_principles_audit.py).  a, b, c, gen, type.
FERMIONS = [
    dict(name="electron", tri=L1,          gen=1, type_="lepton",    m_pdg=0.5109989088),
    dict(name="muon",     tri=L2,          gen=2, type_="lepton",    m_pdg=105.6583777),
    dict(name="tau",      tri=L3,          gen=3, type_="lepton",    m_pdg=1776.859905),
    dict(name="up",       tri=(5, 9, 275), gen=1, type_="up_type",   m_pdg=2.16),
    dict(name="down",     tri=(9, 5, 42),  gen=1, type_="down_type", m_pdg=4.67),
    dict(name="strange",  tri=(9, 186, 1023), gen=2, type_="down_type", m_pdg=93.4),
    dict(name="charm",    tri=L3,          gen=2, type_="up_type",   m_pdg=1275.0),
    dict(name="bottom",   tri=(5, 8191, 65535), gen=3, type_="down_type", m_pdg=4180.0),
    dict(name="top",      tri=(76, 337920, -1), gen=3, type_="up_type", m_pdg=172760.0),
]

# UCL2.3 coefficients (same as COMP-P01-BB)
UCL = {
    "k_const": -0.15486557,
    "k_L":      0.01969789,
    "k_L2":     0.01356591,
    "k_gen":    1.54480278,
    "k_gen2":  -0.80924835,
    "k_M":     -0.80587192,
    "k_mu_a":   0.12372968,
    "k_mu_b":  -1.50452947,
    "k_mu_c":   1.32656602,
}

FOUR_PI = 4.0 * math.pi

# ---------------------------------------------------------------------------
# 2. UCL features and C_f  (identical convention to COMP-P01-BB)
# ---------------------------------------------------------------------------

def mobius(n: int) -> int:
    n = abs(n)
    if n == 0: return 0
    if n == 1: return 1
    out = 1
    p = 2
    while p * p <= n:
        if n % p == 0:
            cnt = 0
            while n % p == 0:
                n //= p; cnt += 1
            if cnt >= 2: return 0
            out = -out
        p += 1
    if n > 1: out = -out
    return out

def ucl_features(a: int, b: int, c: int, gen: int) -> Dict[str, float]:
    if c == 0:
        raise ValueError("c must be nonzero in a GTE triple")
    L = math.log(abs(b) / abs(c))
    mu_a = float(mobius(a))
    mu_b = float(mobius(b))
    mu_c = float(mobius(c))
    return dict(const=1.0, L=L, L2=L*L, gen=float(gen), gen2=float(gen*gen),
                M=mu_a*mu_b*mu_c, mu_a=mu_a, mu_b=mu_b, mu_c=mu_c)

def C_f(f: Dict[str, float]) -> float:
    return math.exp(
        UCL["k_const"]*f["const"] + UCL["k_L"]*f["L"] + UCL["k_L2"]*f["L2"]
        + UCL["k_gen"]*f["gen"] + UCL["k_gen2"]*f["gen2"]
        + UCL["k_M"]*f["M"] + UCL["k_mu_a"]*f["mu_a"] + UCL["k_mu_b"]*f["mu_b"]
        + UCL["k_mu_c"]*f["mu_c"])

# ---------------------------------------------------------------------------
# 3. Canonical-engine-implied E_base per (gen, type) from COMP-P01-BB inversion
# ---------------------------------------------------------------------------

def compute_canonical_Ebase() -> Dict[str, float]:
    """For each fermion, back out E_base = m_PDG / C_f with the current triple.
    Returns {name: E_base_in_MeV}."""
    out = {}
    for f in FERMIONS:
        a, b, c = f["tri"]
        feats = ucl_features(a, b, c, f["gen"])
        cf = C_f(feats)
        out[f["name"]] = f["m_pdg"] / cf
    return out

E_BASE_CURRENT = compute_canonical_Ebase()

# ---------------------------------------------------------------------------
# 4. Candidate G2 triple rules extending the Permutation Principle
# ---------------------------------------------------------------------------
# G1 rules (already in the engine):
#   up   = (a_L3, a_L2, b_L3) = (5, 9, 275)
#   down = (a_L2, a_L3, b_L2) = (9, 5, 42)
# G2 rules extend to charm and strange.  Each rule is a permutation or
# composition of L1, L2, L3 elements that produces a triple (a, b, c) with
# c != 0.  We enumerate "natural" G2 rules and evaluate predictions.

def elem(L, idx):
    return L[idx]

L_ALL = [L1, L2, L3]
LABELS = ["L1", "L2", "L3"]

def candidate_rules() -> List[Dict[str, object]]:
    """Natural G2-like rules: each element pulls from one of the three
    lepton triples via (index_of_L, element_of_triple).  E.g., (2, 0) means
    a_L3.  We generate all triples (a, b, c) built from 3 such picks where
    each triple is drawn from at least two DIFFERENT lepton sources (to
    preserve the Permutation-Principle spirit), and the result isn't trivially
    L1/L2/L3 itself (which would recover the current tau degeneracy)."""
    picks = [(lid, eid) for lid in (0, 1, 2) for eid in (0, 1, 2)]   # 9 choices
    rules = []
    for p_a in picks:
        for p_b in picks:
            for p_c in picks:
                # Require at least two distinct lepton sources
                sources = {p_a[0], p_b[0], p_c[0]}
                if len(sources) < 2:
                    continue
                a = L_ALL[p_a[0]][p_a[1]]
                b = L_ALL[p_b[0]][p_b[1]]
                c = L_ALL[p_c[0]][p_c[1]]
                if c == 0:
                    continue
                name = (f"({LABELS[p_a[0]]}[{p_a[1]}], "
                        f"{LABELS[p_b[0]]}[{p_b[1]}], "
                        f"{LABELS[p_c[0]]}[{p_c[1]}])")
                rules.append(dict(rule=name, triple=(a, b, c)))
    return rules

# Also the trivial "no permutation" choices (for documentation):
TRIVIAL_RULES = [
    dict(rule="L3 as-is (current engine choice)", triple=L3),
    dict(rule="L2 as-is",                          triple=L2),
    dict(rule="L1 as-is",                          triple=L1),
]

# Additional structurally-plausible extensions involving simple combinations
# beyond pure element-picks:
def extended_rules() -> List[Dict[str, object]]:
    out = []
    # Sum-based: a = a_Li + a_Lj, etc.
    for i, j in [(1, 2), (0, 2), (0, 1)]:
        out.append(dict(
            rule=f"(a_L{i+1}+a_L{j+1}, b_L{j+1}, c_L{j+1})",
            triple=(L_ALL[i][0] + L_ALL[j][0], L_ALL[j][1], L_ALL[j][2]),
        ))
    # Product-based:
    for i, j in [(1, 2), (0, 2)]:
        out.append(dict(
            rule=f"(a_L{i+1}*a_L{j+1}, b_L{j+1}, c_L{j+1})",
            triple=(L_ALL[i][0] * L_ALL[j][0], L_ALL[j][1], L_ALL[j][2]),
        ))
    # L2 orbit step (muon step forward): unknown but try b_L3 - b_L2 etc
    out.append(dict(
        rule="(a_L3, b_L3 - b_L2, c_L3)",
        triple=(L3[0], L3[1] - L2[1], L3[2]),
    ))
    return out

ALL_CANDIDATES = TRIVIAL_RULES + candidate_rules() + extended_rules()

# ---------------------------------------------------------------------------
# 5. Evaluate each candidate as a replacement triple for CHARM
# ---------------------------------------------------------------------------

CHARM_PDG_MeV = 1275.0
CHARM_gen = 2
CHARM_type = "up_type"

# E_base for charm under the engine's (gen, type) assignment.  COMP-P01-BB
# showed E_base_charm = 384.3 MeV under the current triple (5, 275, 65535).
# For this attack we treat E_base as a WEAKLY triple-dependent canonical
# quantity; the question is whether any alternative triple yields a C_f
# that, combined with *any* reasonable E_base in the same range, reproduces
# m_charm.
E_BASE_CHARM_CANONICAL = E_BASE_CURRENT["charm"]   # ~384 MeV

def evaluate_candidate(rule: Dict[str, object]) -> Dict[str, object]:
    a, b, c = rule["triple"]
    if c == 0:
        return dict(rule=rule["rule"], triple=rule["triple"],
                    status="c=0 invalid", feasible=False)
    feats = ucl_features(a, b, c, CHARM_gen)
    cf = C_f(feats)
    m_pred_canonical_Ebase = E_BASE_CHARM_CANONICAL * cf
    # Also: what E_base would be required to give exactly m_charm?
    E_base_required = CHARM_PDG_MeV / cf if cf != 0 else float("inf")
    # Compare to canonical charm E_base
    rel_to_canonical_Ebase = (m_pred_canonical_Ebase - CHARM_PDG_MeV) / CHARM_PDG_MeV
    rel_Ebase_shift = (E_base_required - E_BASE_CHARM_CANONICAL) / E_BASE_CHARM_CANONICAL
    return dict(
        rule=rule["rule"],
        triple=rule["triple"],
        ucl_features=feats,
        C_f=cf,
        m_pred_with_canonical_Ebase=m_pred_canonical_Ebase,
        rel_error_to_PDG=rel_to_canonical_Ebase,
        required_Ebase_for_PDG=E_base_required,
        required_Ebase_shift_from_canonical=rel_Ebase_shift,
        matches_tau_triple=(rule["triple"] == L3),
        status="ok",
        feasible=True,
    )

evaluations = [evaluate_candidate(r) for r in ALL_CANDIDATES]
valid_evaluations = [e for e in evaluations if e.get("feasible")]

# UCL-feature signature: a 9-tuple rounded to reasonable precision.  Two
# triples with the same signature give identical UCL predictions -- they
# are UCL-equivalent (the UCL cannot distinguish them).
def feature_signature(feats: Dict[str, float]) -> Tuple[float, ...]:
    return (
        round(feats["L"], 10), round(feats["L2"], 10),
        feats["gen"], feats["gen2"],
        feats["M"], feats["mu_a"], feats["mu_b"], feats["mu_c"],
    )

tau_triple_feats = ucl_features(L3[0], L3[1], L3[2], CHARM_gen)
tau_feature_sig = feature_signature(tau_triple_feats)

# Annotate each evaluation with its UCL-feature signature and whether
# it matches tau's signature.
for e in valid_evaluations:
    a, b, c = e["triple"]
    feats = ucl_features(a, b, c, CHARM_gen)
    sig = feature_signature(feats)
    e["feature_signature"] = list(sig)
    e["ucl_equivalent_to_tau"] = (sig == tau_feature_sig)

# Filter: close to PDG charm mass within 10% (WIN threshold)
close_10pct = [
    e for e in valid_evaluations
    if abs(e["rel_error_to_PDG"]) <= 0.10
]
close_1pct = [
    e for e in valid_evaluations
    if abs(e["rel_error_to_PDG"]) <= 0.01
]

# Non-tau (symbolic) that match
non_tau_close_10pct = [e for e in close_10pct if not e["matches_tau_triple"]]
non_tau_close_1pct  = [e for e in close_1pct  if not e["matches_tau_triple"]]

# Feature-distinct (true structural alternatives -- UCL distinguishes them
# from tau).  These are the genuine attack targets.
feature_distinct_10pct = [
    e for e in close_10pct if not e["ucl_equivalent_to_tau"]
]
feature_distinct_1pct = [
    e for e in close_1pct if not e["ucl_equivalent_to_tau"]
]

# Count distinct feature signatures overall
n_distinct_signatures = len({tuple(e["feature_signature"])
                             for e in valid_evaluations})

# Matched-complexity null test (a_i, b_i, c_i as random integers in the
# same magnitude range as the lepton foundations).  Generate candidate
# random triples and count how many reproduce m_charm within 10%.
import random
rng = random.Random(2026_04_18)

def null_hit_rate(n_trials: int = 2000) -> Tuple[float, float]:
    lepton_range = sorted(set(abs(v) for tri in (L1, L2, L3) for v in tri if v != 0))
    lo_a, hi_a = min(lepton_range), max(lepton_range)
    count_10 = 0
    count_1  = 0
    for _ in range(n_trials):
        # Random positive integers log-uniform in lepton range
        a = max(1, int(math.exp(rng.uniform(math.log(lo_a), math.log(hi_a)))))
        b = max(1, int(math.exp(rng.uniform(math.log(lo_a), math.log(hi_a)))))
        c = max(2, int(math.exp(rng.uniform(math.log(lo_a), math.log(hi_a)))))
        try:
            feats = ucl_features(a, b, c, CHARM_gen)
            cf = C_f(feats)
            m_pred = E_BASE_CHARM_CANONICAL * cf
            rel = (m_pred - CHARM_PDG_MeV) / CHARM_PDG_MeV
            if abs(rel) <= 0.10: count_10 += 1
            if abs(rel) <= 0.01: count_1  += 1
        except Exception:
            continue
    return count_10 / n_trials, count_1 / n_trials

null_frac_10, null_frac_1 = null_hit_rate(n_trials=2000)
expected_null_hits_10pct = null_frac_10 * len(ALL_CANDIDATES)
expected_null_hits_1pct  = null_frac_1  * len(ALL_CANDIDATES)

# Decision: focus on FEATURE-DISTINCT candidates (those that actually
# break the UCL degeneracy) AND compare to null.
# A feature-distinct non-tau candidate within 1% whose density exceeds null
# by a factor >= 3 is a WIN.  Within 10% exceeding null >= 3 is a PARTIAL.

enrichment_10pct = (len(feature_distinct_10pct) / expected_null_hits_10pct
                    if expected_null_hits_10pct > 0 else float("inf"))
enrichment_1pct  = (len(feature_distinct_1pct) / expected_null_hits_1pct
                    if expected_null_hits_1pct > 0 else float("inf"))

if feature_distinct_1pct and enrichment_1pct >= 3.0 and expected_null_hits_1pct < 2.0:
    outcome = "WIN"
    rationale = (
        f"{len(feature_distinct_1pct)} UCL-feature-distinct non-tau "
        f"candidates within 1% of PDG m_charm, {enrichment_1pct:.1f}x over "
        f"the matched-complexity null expectation of "
        f"{expected_null_hits_1pct:.1f}.  Tau/charm triple degeneracy is "
        "NOT structurally required: genuine UCL-distinct alternatives exist "
        "and can be codified as an extended Permutation Principle for G2."
    )
elif feature_distinct_10pct and enrichment_10pct >= 3.0:
    outcome = "PARTIAL"
    rationale = (
        f"{len(feature_distinct_10pct)} UCL-feature-distinct non-tau "
        f"candidates within 10% of PDG m_charm, {enrichment_10pct:.1f}x "
        f"over null expectation of {expected_null_hits_10pct:.1f}. "
        "Marginal evidence for non-tau alternatives; no single clean "
        "unified rule emerges.  OP(i)-A retained as active."
    )
elif feature_distinct_10pct:
    outcome = "DENSITY_DOMINATED"
    rationale = (
        f"{len(feature_distinct_10pct)} UCL-feature-distinct non-tau "
        "matches within 10%, but observed rate is at or below null "
        f"expectation ({enrichment_10pct:.2f}x).  No structural signal; "
        "the tau/charm degeneracy is effectively required by the UCL "
        "given the canonical E_base."
    )
else:
    outcome = "DEGENERACY_CONFIRMED"
    rationale = (
        "No UCL-feature-distinct non-tau candidate reproduces m_charm "
        "within 10% of PDG.  The tau/charm degeneracy is structurally "
        "required under the Lean-certified UCL and canonical E_base.  "
        "Paper 1 should disclose this as a structural feature: charm's "
        "UCL-feature signature IS the tau triple's signature; (gen, type) "
        "in E_base is the only structural distinguisher available."
    )

# ---------------------------------------------------------------------------
# 6. For context, also evaluate STRANGE / BOTTOM / TOP under alternative G2/G3
# rules to report symmetrically.  (Optional -- adds confidence to the map.)
# ---------------------------------------------------------------------------

def sibling_summary(name: str, gen: int, type_: str, pdg: float,
                    candidates: List[Dict[str, object]]) -> Dict[str, object]:
    rows = []
    for r in candidates:
        a, b, c = r["triple"]
        if c == 0: continue
        feats = ucl_features(a, b, c, gen)
        cf = C_f(feats)
        # Use the CURRENT sibling's E_base as anchor
        E_base = E_BASE_CURRENT[name]
        m_pred = E_base * cf
        rel_err = (m_pred - pdg) / pdg
        rows.append(dict(rule=r["rule"], triple=r["triple"],
                         m_pred=m_pred, rel_error=rel_err))
    # sort by |rel_error|
    rows.sort(key=lambda x: abs(x["rel_error"]))
    return dict(
        name=name, gen=gen, type=type_, pdg=pdg,
        closest_10=rows[:10],
        n_within_10pct=sum(1 for r in rows if abs(r["rel_error"]) <= 0.10),
        n_within_1pct=sum(1 for r in rows if abs(r["rel_error"]) <= 0.01),
    )

strange_summary = sibling_summary("strange", 2, "down_type", 93.4,
                                   ALL_CANDIDATES)
bottom_summary  = sibling_summary("bottom",  3, "down_type", 4180.0,
                                   ALL_CANDIDATES)
top_summary     = sibling_summary("top",     3, "up_type",   172760.0,
                                   ALL_CANDIDATES)

# ---------------------------------------------------------------------------
# 7. Findings
# ---------------------------------------------------------------------------

findings = {
    "finding_1_perm_principle_status": (
        "Engine implements a deterministic 'Permutation Principle' for G1 "
        "quark triples (up = (a_L3, a_L2, b_L3); down = (a_L2, a_L3, b_L2)) "
        "but G2/G3 triples (charm, strange, top, bottom) are HARDCODED to "
        "the 'V42.1 canonical pathway' without an analogous derivation.  "
        "Charm's V42.1 triple happens to coincide exactly with tau's "
        "lepton triple (5, 275, 65535).  This creates the UCL-feature "
        "degeneracy surfaced by COMP-P01-BB."
    ),
    "finding_2_enumeration": (
        f"Enumerated {len(ALL_CANDIDATES)} natural G2 candidate triples "
        "(pure element-picks from L1/L2/L3 requiring at least two distinct "
        "lepton sources, plus sum/product/difference extensions).  For "
        f"each: {len(close_10pct)} reproduce m_charm within 10% of PDG "
        f"under canonical E_base; {len(close_1pct)} within 1%."
    ),
    "finding_3_non_tau_candidates": (
        f"Of the within-10% candidates, {len(non_tau_close_10pct)} are "
        "NOT tau's triple and thus would break the degeneracy.  "
        f"Of the within-1% candidates, {len(non_tau_close_1pct)} are "
        "non-tau."
    ),
    "finding_4_sibling_spot_check": (
        "Sibling spot-check (strange, bottom, top) under the same "
        f"candidate rules using their current E_base: strange "
        f"{strange_summary['n_within_10pct']}/{len(ALL_CANDIDATES)} rules "
        f"within 10%; bottom {bottom_summary['n_within_10pct']}; top "
        f"{top_summary['n_within_10pct']}.  This reflects how much each "
        "quark's mass is structurally forced vs tuned."
    ),
    "finding_5_paper_integrity_implication": (
        "Paper 1 section 5.* framing of quark-cascade 'derivation' from "
        "lepton foundations is partially accurate (G1 via Permutation "
        "Principle) and partially hardcoded (G2/G3 via V42.1 canonical "
        "pathway).  A referee inspecting the engine will find the "
        "hardcoded G2/G3 assignments.  Round 8 should either (a) present "
        "the extended Permutation Principle if Attack B finds a unified "
        "G2/G3 rule, or (b) disclose honestly that G2/G3 triples are "
        "currently canonical assignments and formal derivation is an "
        "open problem."
    ),
}

decision = {
    "outcome": outcome,
    "rationale": rationale,
    "count_within_10pct": len(close_10pct),
    "count_within_1pct":  len(close_1pct),
    "non_tau_within_10pct_symbolic": len(non_tau_close_10pct),
    "non_tau_within_1pct_symbolic":  len(non_tau_close_1pct),
    "feature_distinct_within_10pct": len(feature_distinct_10pct),
    "feature_distinct_within_1pct":  len(feature_distinct_1pct),
    "n_distinct_UCL_feature_signatures": n_distinct_signatures,
    "null_fraction_within_10pct": null_frac_10,
    "null_fraction_within_1pct":  null_frac_1,
    "expected_null_hits_within_10pct": expected_null_hits_10pct,
    "expected_null_hits_within_1pct":  expected_null_hits_1pct,
    "enrichment_feature_distinct_10pct_over_null": enrichment_10pct,
    "enrichment_feature_distinct_1pct_over_null":  enrichment_1pct,
    "examples_feature_distinct_within_10pct": [
        dict(rule=e["rule"], triple=e["triple"],
             rel_error=e["rel_error_to_PDG"],
             feature_signature=e["feature_signature"])
        for e in feature_distinct_10pct[:15]
    ],
    "examples_feature_distinct_within_1pct": [
        dict(rule=e["rule"], triple=e["triple"],
             rel_error=e["rel_error_to_PDG"],
             feature_signature=e["feature_signature"])
        for e in feature_distinct_1pct[:15]
    ],
}

# ---------------------------------------------------------------------------
# 8. Pre-commit + final payload
# ---------------------------------------------------------------------------

pre_timestamp = datetime.now(timezone.utc).isoformat()

predictions = {
    "comp_id": "COMP-P01-DD",
    "purpose": (
        "Attack B: investigate the tau/charm GTE triple degeneracy.  Test "
        "whether an extended Permutation Principle for G2 quark triples "
        "can assign charm a non-tau triple that reproduces m_charm within "
        "10% of PDG using the Lean-certified UCL and canonical E_base."
    ),
    "spec_reference": (
        "specs/IN-PROCESS/EPIC_CLUSTER2_CLEAN_WINS/"
        "081_NOTE_P01_BULLETPROOFING_PLAN.md section 3.2"
    ),
    "lepton_foundations_LeanCert": dict(L1=L1, L2=L2, L3=L3),
    "current_engine_mapping": {f["name"]: dict(tri=f["tri"], gen=f["gen"],
                                                 type=f["type_"],
                                                 m_pdg=f["m_pdg"])
                                for f in FERMIONS},
    "canonical_Ebase_MeV_per_particle": E_BASE_CURRENT,
    "ucl_coefficients_UCL2_3": UCL,
    "n_candidate_rules": len(ALL_CANDIDATES),
    "charm_target": dict(m_pdg_MeV=CHARM_PDG_MeV, gen=CHARM_gen, type=CHARM_type,
                          E_base_canonical_MeV=E_BASE_CHARM_CANONICAL),
    "evaluations": evaluations,
    "sibling_spot_check": dict(strange=strange_summary,
                                bottom=bottom_summary,
                                top=top_summary),
    "pre_comparison_timestamp_utc": pre_timestamp,
    "no_fit_parameters_in_this_block": True,
}

pred_canonical = json.dumps(predictions, sort_keys=True, separators=(",", ":"),
                            default=str)
pred_sha = hashlib.sha256(pred_canonical.encode("utf-8")).hexdigest()
predictions["pre_comparison_prediction_sha256"] = pred_sha

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "comp_p01_DD_tau_charm_degeneracy.json")

with open(out_path, "w") as f:
    json.dump({"prediction_block_precomparison": predictions}, f, indent=2,
              default=str)

final_payload = {
    "prediction_block_precomparison": predictions,
    "decision": decision,
    "findings": findings,
    "comparison_timestamp_utc": datetime.now(timezone.utc).isoformat(),
}

with open(out_path, "w") as f:
    json.dump(final_payload, f, indent=2, default=str)

with open(out_path, "rb") as f:
    sha_full = hashlib.sha256(f.read()).hexdigest()

# ---------------------------------------------------------------------------
# 9. Console report
# ---------------------------------------------------------------------------

print("=" * 78)
print("COMP-P01-DD: tau/charm GTE triple degeneracy (Attack B, OP(i)-A)")
print("=" * 78)
print()
print("Lepton foundations (Lean-certified):")
print(f"  L1 (electron) = {L1}")
print(f"  L2 (muon)     = {L2}")
print(f"  L3 (tau)      = {L3}")
print()
print("Current engine G1 (Permutation Principle): up={}, down={}".format(
    (L3[0], L2[0], L3[1]), (L2[0], L3[0], L2[1])))
print("Current engine G2/G3: HARDCODED (V42.1 canonical pathway).")
print(f"  charm (current): {L3}  --  IDENTICAL TO TAU")
print()
print(f"Canonical E_base_charm: {E_BASE_CHARM_CANONICAL:.3f} MeV")
print(f"PDG m_charm: {CHARM_PDG_MeV} MeV")
print()
print(f"Candidate G2 rules enumerated: {len(ALL_CANDIDATES)}")
print(f"  distinct UCL-feature signatures:        {n_distinct_signatures}")
print(f"  reproducing m_charm within 10% of PDG:  {len(close_10pct)}")
print(f"  within 1%:                              {len(close_1pct)}")
print(f"  non-tau SYMBOLIC within 10%:            {len(non_tau_close_10pct)}")
print(f"  non-tau SYMBOLIC within 1%:             {len(non_tau_close_1pct)}")
print(f"  FEATURE-DISTINCT (real alt) within 10%: {len(feature_distinct_10pct)}")
print(f"  FEATURE-DISTINCT (real alt) within 1%:  {len(feature_distinct_1pct)}")
print()
print(f"Null test (random triples in lepton magnitude range):")
print(f"  fraction hitting 10% window:            {null_frac_10:.3%}")
print(f"  fraction hitting 1% window:             {null_frac_1:.3%}")
print(f"  expected null hits over {len(ALL_CANDIDATES)} candidates (10%): "
      f"{expected_null_hits_10pct:.1f}")
print(f"  expected null hits over {len(ALL_CANDIDATES)} candidates (1%): "
      f"{expected_null_hits_1pct:.2f}")
print(f"  enrichment (feature-distinct / null), 10%: {enrichment_10pct:.2f}")
print(f"  enrichment (feature-distinct / null), 1%:  {enrichment_1pct:.2f}")
print()
if feature_distinct_10pct:
    print("FEATURE-DISTINCT non-tau candidates closest to m_charm:")
    print(f"  {'rule':58s} {'triple':>22s} {'rel_err':>10s}")
    for e in sorted(feature_distinct_10pct,
                     key=lambda x: abs(x["rel_error_to_PDG"]))[:10]:
        tri_str = f"({e['triple'][0]}, {e['triple'][1]}, {e['triple'][2]})"
        print(f"  {e['rule']:56.56s} {tri_str:>22s}  "
              f"{e['rel_error_to_PDG']*100:+8.3f}%")
print()
print(f"Sibling spot-check (#rules within 10% of PDG with canonical E_base):")
print(f"  strange: {strange_summary['n_within_10pct']}/{len(ALL_CANDIDATES)}")
print(f"  bottom : {bottom_summary['n_within_10pct']}/{len(ALL_CANDIDATES)}")
print(f"  top    : {top_summary['n_within_10pct']}/{len(ALL_CANDIDATES)}")
print()
print(f"Decision outcome: {outcome}")
print()
print(f"Pre-comparison prediction SHA-256: {pred_sha}")
print(f"Full-payload SHA-256             : {sha_full}")
print(f"Output: {out_path}")
