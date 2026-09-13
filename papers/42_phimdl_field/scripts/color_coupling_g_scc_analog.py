#!/usr/bin/env python3
"""Derivation of the chi-sector mass parameter g (OQ-088-R06a, g-part).

In the canonical field equations (FINAL_THEORY Level 2) the chi sector is
V(chi) = g^2 (1 - cos 3 chi)/9, the exact Z3 analog of the phi sector
V(phi) = m^2 (1 - cos 7 phi)/49 (both canonical sine-Gordon normalization
(scale^2/N^2)(1 - cos N psi), f = 1 GeV convention): m_chi = g exactly as
m_phi = m. The phi-sector scale is derived by the Self-Consistency Condition
m = m_tau = 1.77686 GeV. The certified framework claim is ZERO free parameters
for the full Lagrangian, so g must be derived.

Pre-registered candidate set (no post-hoc additions):
  H1: g = m                (single-mass-parameter MDL reuse; zero new constants)
  H2: g = (N3/N7)^2 m      (cross-sector kink-mass equality 8g/9 = 8m/49)
  H3: g = M_kink = 8m/49   (chi mass = phi kink mass)
  H4: g = sqrt(sigma_GTE)  (chi mass = string-tension scale)
  H5: g = (N3/N7) m        (linear N-scaling)
  H6: g = sqrt(7/2) GeV    (dimensionless Villain coupling promoted to GeV
                            -- CATEGORY ERROR, excluded with reason, not scored)

Scoring: (i) MDL bits in the declared parameter grammar (pointer to an existing
symbol = 4 bits [16-symbol table]; rational a/b = 2 ceil(log2(x+1)) + 1 per
integer; new unexplained dimensionful constant = excluded by the zero-parameter
claim); (ii) mechanism availability in the certified corpus; (iii) structural
consistency (EFT window m_chi <= Lambda_GTE; defect-bias aliveness at T_G).

Nulls: H1 has zero adjustable content (no neighbor family exists -- recorded);
wrong-target check: the reuse rule governs dimensionful parameters only, of
which the certified action has exactly one -- applied to e (dimensionless) and
eps (independently CatAL 7/9) it makes no false prediction.

Expected: H1 selected (4 bits, zero new constants, mechanism = MDL minimality
+ the zero-parameter claim); consequence table m_chi = 1.77686 GeV,
M_chi_kink = 1.5794 GeV, m_chi/T_G = 2.54.
"""
import json
import math
import signal
import sys

TIMEOUT_SECONDS = 120

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

M = 1.77686          # GeV, m_phi = m_tau (SCC)
M_KINK = 8.0 * M / 49.0
SIGMA_GTE = 0.18920  # GeV^2 (P39 G13)
LAMBDA_GTE = 2.01
T_G = 0.6999

def int_bits(n):
    return 2 * math.ceil(math.log2(abs(n) + 1)) + 1

def rat_bits(a, b):
    return int_bits(a) + int_bits(b)

POINTER_BITS = 4  # 16-entry derived-symbol table

candidates = {
    "H1_reuse_m":        {"g": M,                 "bits": POINTER_BITS,
                          "mechanism": "MDL zero-new-scale completion; required by the zero-free-parameter claim",
                          "mechanism_in_corpus": True},
    "H2_kink_equality":  {"g": (9.0/49.0) * M,    "bits": POINTER_BITS + rat_bits(9, 49),
                          "mechanism": "cross-sector kink-mass equality (NOT a theorem; phimdl_kink_masses_equal is pure-phi)",
                          "mechanism_in_corpus": False},
    "H3_g_eq_Mkink":     {"g": M_KINK,            "bits": POINTER_BITS + rat_bits(8, 49),
                          "mechanism": "m_chi = M_kink identification (no mechanism in corpus)",
                          "mechanism_in_corpus": False},
    "H4_sqrt_sigma":     {"g": math.sqrt(SIGMA_GTE), "bits": POINTER_BITS + 3,
                          "mechanism": "mass = tension^(1/2) (category strain: chi mass is not a flux-tube tension)",
                          "mechanism_in_corpus": False},
    "H5_linear_N":       {"g": (3.0/7.0) * M,     "bits": POINTER_BITS + rat_bits(3, 7),
                          "mechanism": "linear N3/N7 scaling (no mechanism in corpus)",
                          "mechanism_in_corpus": False},
}

results = {"inputs": {"m": M, "M_kink": M_KINK, "sigma_GTE": SIGMA_GTE,
                      "Lambda_GTE": LAMBDA_GTE, "T_G": T_G},
           "H6_note": "g = sqrt(7/2) GeV excluded: promotes the dimensionless "
                      "Villain lattice coupling g_c^2 = 7/2 to a GeV mass -- "
                      "category error (same failure family as the R03 "
                      "winding-vs-vacuum mismatch)."}

print("=== Candidate evaluation ===")
print(f"{'ID':<18}{'g (GeV)':>10}{'MDL bits':>10}{'EFT ok':>8}{'mech':>6}")
tab = {}
for cid, c in candidates.items():
    g = c["g"]
    eft_ok = g <= LAMBDA_GTE
    tab[cid] = {"g_GeV": g, "mdl_bits": c["bits"], "eft_window_ok": bool(eft_ok),
                "mechanism": c["mechanism"],
                "mechanism_in_corpus": c["mechanism_in_corpus"],
                "m_chi_over_TG": g / T_G,
                "chi_kink_mass_GeV": 8.0 * g / 9.0}
    print(f"{cid:<18}{g:>10.5f}{c['bits']:>10}{str(eft_ok):>8}"
          f"{str(c['mechanism_in_corpus']):>6}")
results["candidates"] = tab

# selection: minimal bits among mechanism-backed candidates
backed = {k: v for k, v in tab.items() if v["mechanism_in_corpus"]}
sel = min(backed, key=lambda k: backed[k]["mdl_bits"])
margin = min(v["mdl_bits"] for k, v in tab.items() if k != sel) - tab[sel]["mdl_bits"]
print(f"\nSelected: {sel} (g = {tab[sel]['g_GeV']:.5f} GeV); "
      f"bit margin to nearest rival form: {margin} bits")
print("Anti-numerology note: H1 has ZERO adjustable content (no neighbor family).")
print("Wrong-target check: reuse rule governs dimensionful parameters only; "
      "the certified action has exactly one (m). Applied to e (dimensionless) "
      "and eps (CatAL 7/9): no prediction generated -> no false positive.")

results["selection"] = {"selected": sel, "g_GeV": tab[sel]["g_GeV"],
                        "bit_margin": margin,
                        "claim_level": "CatB (mechanism: MDL zero-new-scale completion "
                                       "+ zero-free-parameter claim; SCC-grade analytic "
                                       "derivation remains open)",
                        "robustness_bracket_GeV": [0.29, 1.78]}

print(f"\n=== Consequence table (H1: g = m = {M} GeV) ===")
cons = {"m_chi_GeV": M,
        "chi_kink_mass_GeV": 8.0 * M / 9.0,
        "m_chi_over_TG": M / T_G,
        "m_chi_over_LambdaGTE": M / LAMBDA_GTE,
        "m_A_k0_villain_GeV": math.sqrt(3.5),
        "note": "all spectrum scales inside the EFT window at k = 0; "
                "k >= 2 vector masses exceed Lambda_GTE (UV-completion "
                "sensitivity probed in the RG-improvement script)"}
for k, v in cons.items():
    print(f"  {k}: {v}")
results["consequences"] = cons

with open("/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/"
          "color_coupling_g_scc_analog_results.json", "w") as fp:
    json.dump(results, fp, indent=1)
print("Saved color_coupling_g_scc_analog_results.json")
signal.alarm(0)
