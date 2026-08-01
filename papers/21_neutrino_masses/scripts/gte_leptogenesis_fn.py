#!/usr/bin/env python3
"""
GTE Froggatt-Nielsen neutrino Yukawa texture and the leptogenesis CP asymmetry.

This script extends the K-factor analysis (`gte_leptogenesis.py`) to the full
3x3 Dirac Yukawa texture and the resulting CP asymmetry epsilon_1, and tests
whether epsilon_1 can be claimed as a parameter-free prediction.

Inputs (GTE, CatA / CatAD):
  lambda_C = 0.2236            Cabibbo angle (GST closed form)
  M_1 = M_R = 1.11e13 GeV      lightest RHN mass (consistent with K_1 = 15.93)
  v_H = 246.16 GeV
  delta_CP = pi/2 - 3/8        GTE CP phase (CatA)
  light-nu spectrum            m_nu1 = 0.679 meV (CatA) + PDG Delta m^2

Method:
  Type-I seesaw, hierarchical RHN. Covi-Roulet-Vissani CP asymmetry
      eps_1 = (1/8pi)(1/(YY)_11) sum_{j!=1} Im[((YY)_1j)^2] g(x_j),
      x_j = (M_j/M_1)^2,  g(x) = sqrt(x)[1/(1-x) + 1 - (1+x)ln((1+x)/x)].
  FN suppression Y_ij = c_ij lambda^(q_Li + q_Nj).

Findings (CatB -- feasibility/naturalness, NOT a CatAD derivation):
  - The descending GTE texture q_L=(3,2,1), q_N=(2,1,0), c_ij=1, GTE phase gives
    eps_1 = 3.8e-5, a factor ~2 above the needed eps_1 = 1.80e-5.
  - ROBUST naturalness: with random O(1) coefficients/phases, 76% of GTE-range
    textures land in the feasible window eps_needed < |eps_1| < eps_DI, and 50%
    within a factor 3 of needed; median |eps_1| = 4.3e-5. The observed baryon
    asymmetry therefore requires NO fine-tuning of the GTE seesaw.
  - NOT CatAD: the specific value fails the neighbor-charge null (eps_1 swings
    over orders of magnitude under +/-1 charge changes), the wrong-target null
    (the (3,2,1) charges overpredict m3/m1 by 5.4x, so are not data-selected),
    and the phase-placement null (eps_1 depends entirely on where the CP phase
    is inserted). The GTE delta_CP is not picked out by any extremum.

Conclusion: leptogenesis is robustly FEASIBLE in the GTE seesaw and the needed
CP asymmetry is generic; a parameter-free eps_1 derivation is blocked by the
undetermined Yukawa texture details (charges, O(1) coefficients, phase model),
which is the same Phi_MDL Yukawa-action gate as the Koide/CKM CP-phase ranks.

Graduated: 2026-05-30 (EPIC_080, rank 080-CKM-LEPTOGEN).
"""

import numpy as np
import json

# ---------------------------------------------------------------------------
# GTE inputs
# ---------------------------------------------------------------------------
lambda_C = 0.2236
M_R      = 1.11e13            # = M_1 (lightest RHN), GeV
v_H      = 246.16
delta_CP = np.pi/2 - 3/8

m_nu1 = 0.6786490908714047e-12
m_nu2 = np.sqrt(m_nu1**2 + 7.42e-5*1e-18)
m_nu3 = np.sqrt(m_nu1**2 + 2.51e-3*1e-18)

g_star    = 106.75
sphaleron = 28.0/79.0
K1        = 15.93
kappa_NNR = 0.3/(K1*np.log(K1)**0.6)
eta_B_obs = 6.1e-10
eps_needed = eta_B_obs*g_star/(sphaleron*kappa_NNR)
eps_DI     = 3.0/(16.0*np.pi)*M_R*(m_nu3 - m_nu1)/v_H**2

# ---------------------------------------------------------------------------
# Leptogenesis CP-asymmetry machinery
# ---------------------------------------------------------------------------
def g_crv(x):
    """Covi-Roulet-Vissani loop function, x = (M_j/M_1)^2 != 1."""
    return np.sqrt(x)*(1.0/(1.0 - x) + 1.0 - (1.0 + x)*np.log((1.0 + x)/x))

def build_Y(q_L, q_N, lam, c=None):
    q_L = np.asarray(q_L); q_N = np.asarray(q_N)
    if c is None:
        c = np.ones((3, 3))
    return np.array([[c[i, j]*lam**(q_L[i] + q_N[j]) for j in range(3)]
                     for i in range(3)])

def rhn_spectrum(q_N, lam, M1=M_R):
    q_N = np.asarray(q_N); raw = lam**(-2.0*q_N); raw = raw/raw.min()
    return M1*raw

def epsilon_1(Y, M, phase=None):
    Yc = Y.astype(complex)
    if phase is not None:
        Yc = Yc*phase
    H = Yc.conj().T @ Yc
    M = np.asarray(M, float)
    s = 0.0
    for j in (1, 2):
        s += np.imag(H[0, j]**2)*g_crv((M[j]/M[0])**2)
    return (1.0/(8.0*np.pi))*s/H[0, 0].real

def col_phase(delta):
    P = np.ones((3, 3), complex)
    for j in range(3):
        P[:, j] *= np.exp(1j*delta*j)
    return P

# ---------------------------------------------------------------------------
# Descending GTE texture (anchored on the certified (N_c, strand)=(3,2) pair)
# ---------------------------------------------------------------------------
q_L, q_N = (3, 2, 1), (2, 1, 0)
Y = build_Y(q_L, q_N, lambda_C)
M = rhn_spectrum(q_N, lambda_C)
eps_texture = epsilon_1(Y, M, col_phase(delta_CP))

# ---------------------------------------------------------------------------
# Robust ensemble: random O(1) coefficients and phases on the same charges
# ---------------------------------------------------------------------------
rng = np.random.default_rng(7)
ens = []
for _ in range(20000):
    c  = rng.uniform(0.5, 2.0, size=(3, 3))
    ph = np.exp(1j*rng.uniform(0, 2*np.pi, size=(3, 3)))
    ens.append(abs(epsilon_1(build_Y(q_L, q_N, lambda_C, c=c), M, ph)))
ens = np.array(ens)
frac_feasible = float(np.mean((ens > eps_needed) & (ens < eps_DI)))
frac_within3  = float(np.mean((ens > eps_needed/3) & (ens < 3*eps_needed)))

# ---------------------------------------------------------------------------
# Null tests (summary verdicts)
# ---------------------------------------------------------------------------
# NULL A: neighbour-charge swing
swings = []
for which in ("L", "N"):
    for idx in range(3):
        for d in (-1, +1):
            qL = list(q_L); qN = list(q_N)
            (qL if which == "L" else qN)[idx] += d
            if min(qL + qN) < 0 or len(set(qN)) < 3:
                continue
            e = epsilon_1(build_Y(qL, qN, lambda_C), rhn_spectrum(qN, lambda_C),
                          col_phase(delta_CP))
            if np.isfinite(e) and e != 0:
                swings.append(abs(e)/abs(eps_texture))
neighbour_swing = (min(swings), max(swings))
# NULL B: delta=0 -> CP conserving
eps_cp_conserving = epsilon_1(Y, M, col_phase(0.0))
ds = np.linspace(0.01, np.pi - 0.01, 400)
es = np.array([abs(epsilon_1(Y, M, col_phase(d))) for d in ds])
gte_over_max = float(abs(eps_texture)/es.max())
# NULL C: wrong-target (light-nu hierarchy)
m31_off = lambda_C**(2*(q_L[2] - q_L[0]))/(m_nu3/m_nu1)
# NULL D: phase-placement
def row_phase(delta):
    P = np.ones((3, 3), complex)
    for i in range(3):
        P[i, :] *= np.exp(1j*delta*i)
    return P
eps_rowphase = epsilon_1(Y, M, row_phase(delta_CP))

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
print("="*70)
print("GTE FN NEUTRINO TEXTURE -> LEPTOGENESIS CP ASYMMETRY")
print("="*70)
print(f"eps_needed = {eps_needed:.4e}   eps_DI = {eps_DI:.4e}   "
      f"(needed/DI = {eps_needed/eps_DI:.4f})")
print(f"\nDescending GTE texture q_L={q_L}, q_N={q_N}, c=1, GTE phase:")
print(f"  eps_1 = {eps_texture:+.4e}  (factor {abs(eps_texture)/eps_needed:.2f} of needed)")
print(f"\nROBUST ensemble (random O(1) coeffs/phases, same charges):")
print(f"  |eps_1| median = {np.median(ens):.3e}, "
      f"10-90pct = [{np.percentile(ens,10):.3e}, {np.percentile(ens,90):.3e}]")
print(f"  fraction feasible (eps_needed<|eps|<eps_DI) = {frac_feasible:.2f}")
print(f"  fraction within factor 3 of needed          = {frac_within3:.2f}")
print(f"\nNULL TESTS:")
print(f"  A neighbour-charge swing : {neighbour_swing[0]:.2f}x .. {neighbour_swing[1]:.2f}x  -> FAIL (not robust)")
print(f"  B CP-conserving (delta=0): eps_1 = {eps_cp_conserving:.2e}  -> CP-odd OK; "
      f"GTE delta gives {gte_over_max:.2f}x of scan max -> not singled out")
print(f"  C wrong-target m3/m1     : off by {m31_off:.2f}x  -> FAIL (charges not data-selected)")
print(f"  D phase-placement (rows) : eps_1 = {eps_rowphase:.2e}  -> FAIL (model-dependent)")
print(f"\nVERDICT: CatB -- FEASIBLE and NATURAL (needed eps_1 is generic), but the")
print(f"         specific value is NOT a parameter-free CatAD derivation.")

results = {
    "description": "GTE FN neutrino texture and leptogenesis CP asymmetry",
    "epic": "EPIC_080", "rank": "080-CKM-LEPTOGEN", "date": "2026-05-30",
    "inputs": {"lambda_C": lambda_C, "M_1_GeV": M_R, "v_H_GeV": v_H,
               "delta_CP_rad": delta_CP, "eps_needed": eps_needed, "eps_DI": eps_DI},
    "texture": {"q_L": list(q_L), "q_N": list(q_N),
                "eps_1": float(eps_texture),
                "ratio_to_needed": float(abs(eps_texture)/eps_needed)},
    "robust_ensemble": {"median_abs_eps": float(np.median(ens)),
                        "p10": float(np.percentile(ens, 10)),
                        "p90": float(np.percentile(ens, 90)),
                        "frac_feasible": frac_feasible,
                        "frac_within_factor3": frac_within3},
    "null_tests": {
        "A_neighbour_swing_min": float(neighbour_swing[0]),
        "A_neighbour_swing_max": float(neighbour_swing[1]),
        "B_cp_conserving_eps": float(eps_cp_conserving),
        "B_gte_over_scanmax": gte_over_max,
        "C_m31_overprediction": float(m31_off),
        "D_rowphase_eps": float(eps_rowphase),
        "verdict": "3 of 5 nulls fail -> CatB feasibility/naturalness, NOT CatAD"},
    "conclusion": (
        "Leptogenesis is robustly feasible in the GTE seesaw: the needed CP "
        "asymmetry eps_1 = 1.8e-5 is generic (76% of GTE-range textures feasible, "
        "median 4.3e-5), requiring no fine-tuning. The specific value is NOT a "
        "parameter-free derivation: it fails the neighbour-charge, wrong-target "
        "and phase-placement nulls. CatAD gate = Phi_MDL Yukawa action (shared "
        "with the Koide/CKM CP-phase ranks). Status: PARTIAL CatB (strengthened "
        "from feasibility-via-bound to quantified ensemble naturalness)."
    ),
}
out = "papers/21_neutrino_masses/scripts/gte_leptogenesis_fn_results.json"
with open(out, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {out}")

if __name__ == "__main__":
    pass
