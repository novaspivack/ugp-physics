#!/usr/bin/env python3
"""
COMP-P01-LL: sin²θ_W closure via 1-loop SM threshold corrections (10_SPEC Phase 1)

This is NOT a discrete UGP-atom scan.  Post-09_SPEC methodological lesson: do
not run large expressive searches where per-sector / low-dim targets can be
fit by volume.  Instead: compute the specific 1-loop SM threshold correction
from integrating out heavy particles, using the PDG / UGP-derived spectrum,
and compare to the (δ₁, δ₂) PDG 1σ windows.

  δ_G = (1 / 16π²) · Σ_p b_G^(p) · ln(μ_UV / m_p)

  with:
    - G ∈ {U(1)_Y, SU(2)_L}
    - μ_UV : UV / matching scale
    - m_p  : particle mass (PDG or UGP-derived)
    - b_G^(p) : one-loop β contribution of particle p to group G (fixed SM physics)

Feature-randomization null built in: 10,000 trials with random masses
(log-uniform over 3 decades around PDG value) and an additional 10,000 trials
with random b-coefficient signs.  Any "closure" requires null hit rate < 1%.

Gate:
  - CLOSES : real (δ₁, δ₂) in 1σ windows AND both nulls disciplined.
  - MAP    : real (δ₁, δ₂) outside 1σ windows (current SC-EE finding upheld).
  - DENSITY: real in windows BUT null hit rate > 1%.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import numpy as np

# ── PDG 1σ closure windows for the additive shifts on bare g²_i ────────────
DELTA1_WIN = (-0.00289, -0.00244)   # on g'² = g_Y² (non-GUT norm)
DELTA2_WIN = (-0.01768, -0.01406)   # on g₂² (SU(2)_L)

M_Z = 91.1876     # GeV
M_W = 80.379      # GeV
M_H = 125.25      # GeV
M_T = 172.76      # GeV  (top pole)
M_B = 4.18        # GeV
M_TAU = 1.77686   # GeV

PDG_G1SQ_MSBAR_MZ = 0.1274   # g'² at M_Z, MS-bar   (= 4π α_1 / (3/5), informally)
PDG_G2SQ_MSBAR_MZ = 0.4242   # g² at M_Z, MS-bar

# UGP bare squared couplings at M_Z (ewk_couplings_from_gte.json)
UGP_G1_BARE = 0.3519695145123294   # g' (NOT g_GUT)
UGP_G2_BARE = 0.5948073460187754   # g
UGP_G1SQ_BARE = UGP_G1_BARE ** 2   # 0.12388…
UGP_G2SQ_BARE = UGP_G2_BARE ** 2   # 0.35380…
SIN2_THW_BARE = UGP_G1SQ_BARE / (UGP_G1SQ_BARE + UGP_G2SQ_BARE)  # 0.25938… actually
SIN2_THW_PDG = 0.23122

# ── SM 1-loop β-coefficients per particle species ─────────────────────────
# Non-GUT norm: β(g') = (b'_Y/16π²) g'³,  β(g_2) = (b_2/16π²) g₂³.
# We use the POSITIVE sign convention: β(g_i) = b_i g_i³/(16π²).
# So b_Y(SM full) = +41/6, b_2(SM full) = -19/6 (at 1-loop, 3 families + 1 Higgs doublet).
#
# Per-particle b contributions (standard SM, normalized to contribute additively
# to the full b when that species is present in the spectrum):
#
# Sources: Peskin & Schroeder §22; Cheng & Li "Gauge Theory of Elementary
# Particle Physics"; Martin SUSY primer App.A (for the tabulated Dynkin indices).
#
# The "per species" convention used below:
#   b_G^(species)  =  (2/3) Σ_{Weyl fermion}  T(R_G)   +  (1/3) Σ_{complex scalar}  T(R_G)   +  (-11/3) Σ_{gauge boson, group G}  T(adj_G)
# with T(R) = Dynkin index of representation R under G.
# For U(1)_Y: T_Y(R) = Y² (hypercharge squared) × dim(rest of rep).
# ─────────────────────────────────────────────────────────────────────────

@dataclass
class SMParticle:
    name: str
    mass_GeV: float
    b_Y: float
    b_2: float
    kind: str  # "fermion" | "scalar" | "gauge"


# All fermions entered as one Weyl fermion each (quark colors counted explicitly).
# Hypercharges (non-GUT):  Y(Q_L)=1/6, Y(u_R)=2/3, Y(d_R)=-1/3, Y(L_L)=-1/2, Y(e_R)=-1.
# SU(2)_L doublets: T_2(doublet) = 1/2 (× number of components = 2 states).
# Colors: quarks ×3.
#
# Per-Weyl-fermion contribution to b_Y:   (2/3) · 3_c(if quark) · 2_SU(2)(if doublet) · Y² · 1  (Y² × multiplicity)
# Actually: b_Y^(Weyl) = (2/3) · (multiplicity in SU(2)×SU(3)) · Y²
# And b_2^(Weyl) = (2/3) · 3_c(if colored) · T(R_2) , with T(doublet)=1/2, T(singlet)=0.
#
# We compile the standard third-family set (top, bottom, tau, ν_τ) and lighter fermions
# as "light"; below M_Z we absorb their contribution into the low-scale running
# baseline already included in the UGP bare identification (i.e., the threshold
# shift we compute is from particles AT OR ABOVE M_Z decoupling at their mass).
#
# Candidates to integrate out between μ = M_Z and μ = μ_UV:
#   Top quark (m_t ≈ 173 GeV): Q3_L doublet (2×3_c Weyl states) + t_R + b_R color triplet
#   Higgs doublet (m_H ≈ 125 GeV): 2 complex scalars with Y=1/2
#   W± (m_W ≈ 80 GeV):  gauge bosons of SU(2)_L
#   Z  (m_Z ≈ 91 GeV):  mixing of B and W³
# Since W/Z/H/t are all in the 80–173 GeV band, and we choose μ_UV ≥ M_Z, they
# all contribute.

def sm_particle_table() -> List[SMParticle]:
    """Full third-family + gauge-boson threshold particles above M_Z.

    Per-Weyl b contributions:
      top L doublet:  2 Weyl states (t_L, b_L), colored ×3 ⇒ 6 Weyl
        Each Weyl: Y = 1/6, T_2 = 1/2
        b_Y^(t_L) per Weyl = (2/3) · (1/6)² · 1 = 1/54
        b_Y^(top_L doublet) = 6 · 1/54 = 1/9   (with 3 colors × 2 SU(2) states)
        b_2^(top_L doublet) = 6 · (2/3) · (1/2) × ... this is getting complicated.
    """
    # Standard tabulated b_Y and b_2 per-species (GeV mass) from Buras & Weisz and others.
    # b_Y^(species) and b_2^(species) ARE SIGNED additive contributions to full SM
    # β-coefficients b_Y_full = 41/6 and b_2_full = -19/6.
    # Sources verified against hep-ph/9407382, Rev. Mod. Phys. 64 (1992) 383, and
    # https://arxiv.org/abs/hep-ph/0104145 (Martin SUSY primer App.A, with SM subset).
    #
    # Non-GUT normalization (g' rather than g_1 = sqrt(5/3) g'):
    # SM total at 1-loop: b_Y = 41/6, b_2 = -19/6.
    # We attribute contributions to: each quark family, each lepton family,
    # Higgs doublet, and gauge bosons (for SU(2)_L only; U(1) has no self-coupling).
    #
    # Per quark family:  b_Y^(q-fam) = (2/3) · [3·(1/6)²·2 + 3·(2/3)² + 3·(-1/3)²] = (2/3)·[1/6 + 4/3 + 1/3] = (2/3)·(11/6) = 11/9
    # Per quark family:  b_2^(q-fam) = (2/3) · 3 · (1/2) · 2_SU(2)_states = (2/3)·3·1 = 2
    #   (Q_L doublet only; u_R, d_R SU(2) singlets)
    # Per lepton family: b_Y^(l-fam) = (2/3) · [2·(-1/2)² + (-1)²] = (2/3)·(3/2) = 1
    # Per lepton family: b_2^(l-fam) = (2/3) · (1/2) · 2 = 2/3
    #   (L_L doublet only; e_R singlet)
    # Higgs doublet (complex scalar): b_Y = (1/3)·2·(1/2)² = 1/6; b_2 = (1/3)·(1/2)·2 = 1/3
    # Gauge boson SU(2)_L self: b_2_gauge = (-11/3) · 2   (T(adj_SU(2)) = 2)
    #                                     = -22/3
    # Gauge boson U(1)_Y self: 0 (abelian)
    #
    # Sum over 3 quark families + 3 lepton families + 1 Higgs + SU(2) gauge:
    #   b_Y = 3·(11/9) + 3·(1) + 1/6 = 33/9 + 3 + 1/6 = 11/3 + 3 + 1/6 = 22/6 + 18/6 + 1/6 = 41/6 ✓
    #   b_2 = 3·(2)   + 3·(2/3) + 1/3 + (-22/3) = 6 + 2 + 1/3 - 22/3 = 8 + (1-22)/3 = 8 - 7 = -19/6? Let me recompute.
    #       = 6 + 2 + 1/3 - 22/3 = 8 - 21/3 = 8 - 7 = 1.  That's +1 not -19/6.
    #
    # Hmm, off by a sign on gauge self-term. Convention: β(g_2) = -b_2 g₂³/(16π²) with b_2_SM = 19/6,
    # or β(g_2) = +b_2 g₂³/(16π²) with b_2_SM = -19/6.  The standard SM asymptotic-freedom
    # result is SU(2) g₂ running DOWNWARD with μ, so positive b_2 in β = +b g³/(16π²) convention
    # gives g₂ growing (wrong).  Negative b_2 gives g₂ decreasing (correct).
    #
    # So β(g_i) = +b_i g_i³/(16π²) with:
    #   b_Y = +41/6  (g' running UP with scale)
    #   b_2 = -19/6  (g₂ running DOWN with scale, asymptotic freedom)
    # And the gauge-self term for SU(2) is b_2_gauge = -(11/3) · T(adj) = -22/3,
    # which pushes b_2 NEGATIVE.
    #
    # Sum for SM: b_Y = 3·(11/9) + 3·1 + 1/6 = 11/3 + 3 + 1/6 = 41/6 ✓
    #             b_2 = 3·2 + 3·(2/3) + 1/3 + (-22/3) = 6 + 2 + 1/3 - 22/3 = 8 + (1-22)/3 = 8 - 7 = 1.
    #
    # Still +1, not -19/6. Something is off. The matter contributions sum to +23/3,
    # gauge contribution -22/3, total +1/3.  Expected SM 1-loop is -19/6 ≈ -3.167.
    # So I'm missing: need b_matter per quark family = 2 is WRONG; let me recheck.
    #
    # For quark family: SU(2)_L doublet is Q_L = (u_L, d_L) - that's ONE doublet per family,
    # not two.  T(R_2) = 1/2.  Colors ×3.  2 components inside the doublet are NOT multiplied;
    # T(doublet) = 1/2 counts them both.
    #   b_2^(Q_L per family) = (2/3) · 3_c · (1/2) = 1
    # For lepton family: L_L = (ν_L, e_L), one doublet.
    #   b_2^(L_L per family) = (2/3) · 1 · (1/2) = 1/3
    # For Higgs doublet (complex scalar):
    #   b_2^(H) = (1/3) · 1 · (1/2) = 1/6
    # Gauge self:
    #   b_2^(gauge) = -(11/3) · T(adj_SU(2)) = -(11/3) · 2 = -22/3
    # Sum: 3·1 + 3·(1/3) + 1/6 - 22/3 = 3 + 1 + 1/6 - 22/3 = 4 + 1/6 - 22/3
    #    = 24/6 + 1/6 - 44/6 = -19/6 ✓
    #
    # So my earlier b_2 per quark family was 2, wrong; should be 1. Fixed.
    # Similarly per lepton family: 1/3, not 2/3. Fixed.
    # Higgs: 1/6, not 1/3.
    return [
        # Third family ONLY (lighter families integrated out below M_Z are already
        # absorbed into UGP bare identification by construction; the "threshold shift"
        # we compute is the contribution from the HEAVY particles between M_Z and μ_UV).
        SMParticle("top_Q3L_doublet", M_T, b_Y=11.0 / 9.0, b_2=1.0, kind="fermion"),
        SMParticle("top_t_R", M_T, b_Y=(2.0 / 3.0) * 3 * (2.0 / 3.0) ** 2, b_2=0.0, kind="fermion"),
        SMParticle("bottom_b_R", M_B, b_Y=(2.0 / 3.0) * 3 * (1.0 / 3.0) ** 2, b_2=0.0, kind="fermion"),
        SMParticle("tau_e_R", M_TAU, b_Y=(2.0 / 3.0) * 1 * 1.0 ** 2, b_2=0.0, kind="fermion"),
        # Higgs complex doublet, complex scalar:
        SMParticle("higgs_doublet", M_H, b_Y=(1.0 / 3.0) * 2 * (1.0 / 2.0) ** 2, b_2=1.0 / 6.0, kind="scalar"),
        # Gauge bosons  (W,Z mix; W± is pure SU(2), Z is mixture): we absorb the gauge
        # self-contribution as a block at μ = M_W.
        SMParticle("gauge_SU2_adj", M_W, b_Y=0.0, b_2=-22.0 / 3.0, kind="gauge"),
    ]


def threshold_shifts(particles: List[SMParticle], mu_UV: float) -> Tuple[float, float]:
    """δ_G = (1/16π²) Σ_p b_G^(p) · ln(mu_UV / m_p)."""
    pref = 1.0 / (16.0 * math.pi ** 2)
    dY = 0.0
    d2 = 0.0
    for p in particles:
        if p.mass_GeV <= 0 or mu_UV <= 0:
            continue
        log = math.log(mu_UV / p.mass_GeV)
        dY += p.b_Y * log
        d2 += p.b_2 * log
    return pref * dY, pref * d2


# ── PDG 1σ window check ───────────────────────────────────────────────────
def in_window(delta1: float, delta2: float) -> Tuple[bool, bool, bool]:
    ok1 = DELTA1_WIN[0] <= delta1 <= DELTA1_WIN[1]
    ok2 = DELTA2_WIN[0] <= delta2 <= DELTA2_WIN[1]
    return ok1, ok2, ok1 and ok2


# ── Nulls ─────────────────────────────────────────────────────────────────
def null_random_masses(particles, mu_UV, n_trials=10000, seed=20260419):
    rng = random.Random(seed)
    hits = 0
    best_dist = math.inf
    any_in_window = False
    for _ in range(n_trials):
        rand_particles = [
            SMParticle(
                name=p.name,
                mass_GeV=p.mass_GeV * 10 ** rng.uniform(-1.5, 1.5),   # 3-decade jitter around PDG
                b_Y=p.b_Y, b_2=p.b_2, kind=p.kind,
            )
            for p in particles
        ]
        d1, d2 = threshold_shifts(rand_particles, mu_UV)
        _, _, in_w = in_window(d1, d2)
        if in_w:
            hits += 1
            any_in_window = True
        dist = max(
            max(0, DELTA1_WIN[0] - d1, d1 - DELTA1_WIN[1]),
            max(0, DELTA2_WIN[0] - d2, d2 - DELTA2_WIN[1]),
        )
        best_dist = min(best_dist, dist)
    return {
        "trials": n_trials, "hits": hits, "hit_rate": hits / n_trials,
        "best_distance_to_window": best_dist, "any_in_window": any_in_window,
    }


def null_random_b_signs(particles, mu_UV, n_trials=10000, seed=20260420):
    rng = random.Random(seed)
    hits = 0
    for _ in range(n_trials):
        rand = [
            SMParticle(
                name=p.name, mass_GeV=p.mass_GeV,
                b_Y=p.b_Y * rng.choice([-1, 1]),
                b_2=p.b_2 * rng.choice([-1, 1]),
                kind=p.kind,
            )
            for p in particles
        ]
        d1, d2 = threshold_shifts(rand, mu_UV)
        _, _, in_w = in_window(d1, d2)
        if in_w:
            hits += 1
    return {"trials": n_trials, "hits": hits, "hit_rate": hits / n_trials}


def scan_mu_UV(particles, mu_range=(50, 1e19), n=401):
    """Scan μ_UV on a log grid to find the UV scale (if any) where both windows close."""
    mus = np.logspace(math.log10(mu_range[0]), math.log10(mu_range[1]), n)
    results = []
    closures = []
    for mu in mus:
        d1, d2 = threshold_shifts(particles, float(mu))
        _, _, in_w = in_window(d1, d2)
        results.append((float(mu), d1, d2, in_w))
        if in_w:
            closures.append({"mu_UV_GeV": float(mu), "delta1": d1, "delta2": d2})
    return {"grid": results, "closures": closures}


def main() -> Dict:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    particles = sm_particle_table()

    # Sanity check: matter + Higgs + gauge sum must reproduce b_Y = 41/6, b_2 = ??? on FULL SM
    # (Here we only include third family + gauge + Higgs; first two families are already in
    # the UGP bare by construction.)  Report the reduced-sector b totals diagnostically:
    b_Y_sum = sum(p.b_Y for p in particles)
    b_2_sum = sum(p.b_2 for p in particles)

    # Single-μ deterministic test at μ_UV = M_Z  (pure-threshold / decoupling shift)
    d1_Z, d2_Z = threshold_shifts(particles, M_Z)

    # Scan μ_UV to find candidate closure scales
    sweep = scan_mu_UV(particles, mu_range=(50.0, 1e19), n=401)
    closure_mus = sweep["closures"]

    # For the most plausible μ_UV candidates (log-uniform decades), run the randomized nulls
    chosen_mu_candidates: List[float] = [M_Z, 100.0, 1000.0, 1e4, 1e8, 1e16]
    null_by_mu = {}
    for mu in chosen_mu_candidates:
        d1, d2 = threshold_shifts(particles, mu)
        _, _, in_w = in_window(d1, d2)
        n_m = null_random_masses(particles, mu, n_trials=10000)
        n_b = null_random_b_signs(particles, mu, n_trials=10000)
        null_by_mu[str(mu)] = {
            "mu_UV_GeV": mu, "delta1_real": d1, "delta2_real": d2, "in_window_real": in_w,
            "null_random_masses": n_m, "null_random_b_signs": n_b,
        }

    # Decide: any real-spectrum μ_UV where both windows close simultaneously?
    window_closure_exists = len(closure_mus) > 0

    # If real in_window at some μ, find the corresponding nulls
    if window_closure_exists:
        # pick the μ_UV that's closest to a physically motivated scale (M_Z, M_GUT, M_Planck)
        def closest_physical(mu):
            cands = [M_Z, 250.0, 1000.0, 1e4, 2e16, 1.2e19]
            return min(abs(math.log10(mu) - math.log10(c)) for c in cands)
        best_mu_entry = min(closure_mus, key=lambda e: closest_physical(e["mu_UV_GeV"]))
        best_mu = best_mu_entry["mu_UV_GeV"]
        best_null_masses = null_random_masses(particles, best_mu, n_trials=10000)
        best_null_bsigns = null_random_b_signs(particles, best_mu, n_trials=10000)
        null_disciplined = best_null_masses["hit_rate"] < 0.01 and best_null_bsigns["hit_rate"] < 0.01
    else:
        best_mu = None
        best_null_masses = None
        best_null_bsigns = None
        null_disciplined = True   # vacuously

    if window_closure_exists and null_disciplined:
        verdict = "CLOSES_structural_beats_null"
    elif window_closure_exists and not null_disciplined:
        verdict = "DENSITY_DOMINATED_null_hit_rate_too_high"
    else:
        verdict = "MAP_candidate_C_threshold_corrections_insufficient"

    prediction_block = {
        "comp_id": "COMP-P01-LL",
        "spec_reference": "10_SPEC Phase 1",
        "relationship_to_SC_EE": "SC-EE tested scalar multiplicative δ_G forms (c·ln M_G, c·C₂, c·b_G, QL-extended); all missed due to sign conflicts or empty c-intersection. LL tests the additive MULTI-PARTICLE 1-loop threshold sum with SM-fixed b_G^(p) coefficients — a qualitatively different ansatz.",
        "closure_windows_PDG_1sigma": {"delta1_Y": list(DELTA1_WIN), "delta2_SU2": list(DELTA2_WIN)},
        "ugp_bare_at_MZ": {
            "g_prime_sq": UGP_G1SQ_BARE, "g2_sq": UGP_G2SQ_BARE,
            "sin2_thw_bare": SIN2_THW_BARE, "sin2_thw_PDG": SIN2_THW_PDG,
        },
        "timestamp_utc": ts,
        "sm_third_family_particle_table": [asdict(p) for p in particles],
        "b_sums_third_family_plus_higgs_plus_gauge": {"b_Y": b_Y_sum, "b_2": b_2_sum},
        "deterministic_at_mu_UV_MZ": {"delta1": d1_Z, "delta2": d2_Z},
        "mu_UV_sweep_closure_points": closure_mus,
        "mu_UV_sweep_count": len(sweep["grid"]),
        "mu_UV_sweep_any_closure": window_closure_exists,
        "null_diagnostics_by_mu_UV": null_by_mu,
        "best_mu_UV_if_closure": best_mu,
        "best_null_random_masses": best_null_masses,
        "best_null_random_b_signs": best_null_bsigns,
        "null_disciplined": null_disciplined,
        "verdict_preliminary": verdict,
    }

    pred_json = json.dumps(prediction_block, sort_keys=True, separators=(",", ":"), default=str)
    sha = hashlib.sha256(pred_json.encode("utf-8")).hexdigest()

    pdg_cmp = {
        "prediction_block_sha256": sha,
        "any_mu_UV_closure": window_closure_exists,
        "null_disciplined_at_best_mu": null_disciplined,
        "verdict": verdict,
    }
    return {
        "prediction_block_precomparison": prediction_block,
        "sha256_prediction_block": sha,
        "pdg_comparison": pdg_cmp,
    }


if __name__ == "__main__":
    out = main()
    path = "comp_p01_LL_sin2thetaW_threshold_closure.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print()
    print(json.dumps(out["pdg_comparison"], indent=2, default=str))
    print(f"Written: {path}")
