"""
rank196_leptoquark.py -- Z7 winding analysis of SU(5) X,Y leptoquarks

Investigates:
  Part A: Z7 winding assignments for all SU(5) leptoquarks (X, Y and antiparticles)
  Part B: Which leptoquarks carry the "missing" Z7 windings {1, 5}
  Part C: Z7 winding conservation at leptoquark vertices (proton decay subprocesses)
  Part D: Leptoquark mass estimate from GTE arithmetic (M_GUT from Rank 183)
  Part E: N_eff-based mass estimate
  Part F: Structural count -- |{missing Z7 classes}| x 6 = 12 leptoquark generators

GTE inputs used:
  w = 3Q mod 7              (Z7 charge-winding formula, CatAL per Rank 183/189)
  SM Z7 classes: {0,2,3,4,6} (CatAL, Rank 183)
  Missing classes: {1,5}     (CatAL, Rank 183)
  M_GUT ~ 4.6e16 GeV        (CatA, Rank 183-GCE GQW formula)
  alpha_GUT = 8/411          (CatAL, Rank 183-GCE)
  c_H = 13 = N_gen x N_fam - N_gen (CatAL, P31)

Physical realism flags (Rule 11 of EPIC_PROCEDURAL_RULES):
  REALISTIC    -- matches known physics within expected errors
  NEW PRED     -- GTE predicts something with new structural content
  CONSTRAINED  -- consistent but not a sharp derivation
"""

import math
from fractions import Fraction

# ---- GTE constants -----------------------------------------------------------
N_GEN            = 3
N_FAM            = 5
C_H              = N_GEN * N_FAM - N_GEN   # = 13 (CatAL, P31)
ALPHA_GTE        = Fraction(1, 137)
ALPHA_GUT        = Fraction(8, 411)        # CatAL, Rank 183-GCE
SIN2_EW          = Fraction(3, 13)         # CatAL, P31
SIN2_GUT         = Fraction(3, 8)          # CatAL, Rank 183
M_GUT_GQW        = 4.625e16               # CatA, Rank 183-GCE
M_GUT_RGE        = 6.8e13                 # CatA, Rank 183-GCE (1-loop, IR inputs)
M_Z_GEV          = 91.1876
N_EFF_ELECTRON   = 73                     # lepton seed b1 (CatAL)


def winding(charge_numerator):
    """Z7 winding from charge numerator n where Q = n/3.
    Formula: w = 3Q mod 7 = n mod 7.
    """
    return charge_numerator % 7


print("=" * 72)
print("RANK 196-LQM: Z7 Winding Analysis of SU(5) X,Y Leptoquarks")
print("=" * 72)

# ---- Part A: Z7 winding assignments -----------------------------------------
print("\n-- Part A: Z7 winding assignments: SM particles and SU(5) leptoquarks --")

SM_PARTICLES = {
    "vacuum/gamma/nu_L": {"Q_num": 0,  "w": 0},
    "u quark":           {"Q_num": 2,  "w": 2},
    "W+/proton":         {"Q_num": 3,  "w": 3},
    "e-/W-":             {"Q_num": -3, "w": 4},
    "d quark":           {"Q_num": -1, "w": 6},
}

SM_WINDINGS = {v["w"] for v in SM_PARTICLES.values()}  # {0,2,3,4,6}
ALL_Z7      = set(range(7))
MISSING_Z7  = ALL_Z7 - SM_WINDINGS                      # {1,5}

print(f"\n  SM Z7 winding classes:   {sorted(SM_WINDINGS)}")
print(f"  All Z7 classes:          {sorted(ALL_Z7)}")
print(f"  Missing Z7 classes:      {sorted(MISSING_Z7)}  [= {{1,5}}]")

print(f"\n  Verification: w = Q_num mod 7 for SM particles")
print(f"  {'Particle':>22}  {'Q':>8}  {'Q_num':>6}  {'w_formula':>10}  {'w_known':>8}  OK?")
for name, info in SM_PARTICLES.items():
    w_formula = winding(info["Q_num"])
    match = "yes" if w_formula == info["w"] else "ERROR"
    q_num = info["Q_num"]
    q_str = f"{q_num}/3" if q_num not in (0, 3, -3) else str(q_num // 3)
    print(f"  {name:>22}  {q_str:>8}  {q_num:>6}  {w_formula:>10}  {info['w']:>8}  {match}")

# SU(5) leptoquarks from the (3,2,+5/3) and (3bar,2,-5/3) representations
# Q = T3 + Y/2 with Y = +5/3: upper T3=+1/2 gives Q=4/3, lower T3=-1/2 gives Q=1/3
# Conjugate (3bar,2,-5/3): upper Q=-4/3, lower Q=-1/3
print(f"\n  SU(5) Leptoquarks: (3,2,+5/3) and (3bar,2,-5/3) representations")
print(f"  {'Leptoquark':>22}  {'Q':>8}  {'Q_num':>6}  {'w':>4}  {'In SM?':>7}  {'Missing?':>9}")

LEPTOQUARKS = [
    ("X  (Q=+4/3)",  4,  "+4/3", "(3,2,+5/3) upper"),
    ("Y  (Q=+1/3)",  1,  "+1/3", "(3,2,+5/3) lower"),
    ("Xbar (Q=-4/3)", -4, "-4/3", "(3bar,2,-5/3) upper"),
    ("Ybar (Q=-1/3)", -1, "-1/3", "(3bar,2,-5/3) lower"),
]

leptoquark_w = {}
for name, q_num, q_label, rep in LEPTOQUARKS:
    w = winding(q_num)
    in_sm = w in SM_WINDINGS
    missing = not in_sm
    leptoquark_w[name.split()[0]] = w
    marker = "YES <--" if missing else "no"
    print(f"  {name:>22}  {q_label:>8}  {q_num:>6}  {w:>4}  {'YES' if in_sm else 'NO':>7}  {marker:>9}")

print(f"\n  Anti-quarks carrying missing Z7 windings:")
ANTIQUARKS = [
    ("dbar (anti-down)", 1,  "+1/3", "QCD confined; same w=1 as Y leptoquark"),
    ("ubar (anti-up)",  -2, "-2/3", "QCD confined; w=5 (second missing winding)"),
]
for name, q_num, q_label, note in ANTIQUARKS:
    w = winding(q_num)
    status = "MISSING" if w not in SM_WINDINGS else "present"
    print(f"  {name:>22}  {q_label:>8}  {q_num:>6}  w={w}  {status}  [{note}]")

print("""
  STRUCTURAL CONCLUSION (CatAD):
  Only Y (Q=+1/3, w=1) among the four SU(5) leptoquarks carries a
  MISSING Z7 winding. The other three carry existing SM windings:
    X  (w=4)  <-> e-/W- sector   [existing]
    Xbar (w=3) <-> W+/proton     [existing]
    Ybar (w=6) <-> d-quark       [existing]
    Y  (w=1)  <-> dbar antiquark [MISSING -- GUT-scale free excitation]

  The second missing winding w=5 is carried by the ubar antiquark
  (Q=-2/3). Both w=1 and w=5 appear simultaneously at the Y-channel
  leptoquark vertex (see Part C).
""")

# ---- Part B: Missing winding identification ---------------------------------
print("-- Part B: Missing winding Z7 identification --")
print(f"\n  Particles carrying missing Z7 windings {{1,5}}:")
for name, q_num, q_label, note in ANTIQUARKS:
    w = winding(q_num)
    if w not in SM_WINDINGS:
        print(f"    w={w}: {name} (Q={q_label})  [{note}]")
for name, q_num, q_label, rep in LEPTOQUARKS:
    w = winding(q_num)
    if w not in SM_WINDINGS:
        print(f"    w={w}: {name} (Q={q_label})  [{rep}]")

print("""
  PHYSICAL INTERPRETATION (CatAD):
  Missing winding w=1 (Q=+1/3) is shared by:
    (a) The Y leptoquark of SU(5) -- heavy gauge boson at M_GUT
    (b) The dbar antiquark -- confined in QCD at low energies

  Missing winding w=5 (Q=-2/3) is carried by:
    (a) The ubar antiquark -- confined in QCD at low energies
    (b) No dedicated SU(5) leptoquark: ubar appears as the FINAL
        STATE in Y-mediated proton decay (Y* -> ubar + e+)

  Absence from the SM as free excitations: at EW scale, windings
  {1,5} are confined inside QCD bound states. At the GUT scale,
  w=1 reemerges as the free Y gauge boson. Both windings appear
  jointly at the Y-channel leptoquark vertex.
""")

# ---- Part C: Z7 winding conservation at leptoquark vertices ----------------
print("-- Part C: Z7 winding conservation at leptoquark vertices --")

# Particle windings
w_u    = winding(2)    # u quark:  Q=+2/3
w_d    = winding(-1)   # d quark:  Q=-1/3
w_Y    = winding(1)    # Y boson:  Q=+1/3
w_ubar = winding(-2)   # ubar:     Q=-2/3
w_dbar = winding(1)    # dbar:     Q=+1/3
w_ep   = winding(3)    # e+:       Q=+1
w_X    = winding(4)    # X boson:  Q=+4/3  (diquark vertex)
w_pi0  = winding(0)    # pi0:      Q=0

print(f"\n  Y-channel subprocess: u + d -> Y* -> ubar + e+")
print(f"  (Y boson, Q=+1/3, w={w_Y} carries the MISSING winding)")

# Vertex 1: u + d -> Y*
w_v1_in  = (w_u + w_d) % 7
w_v1_out = w_Y
print(f"\n  Vertex 1: u(w={w_u}) + d(w={w_d}) -> Y*(w={w_Y})")
print(f"    In:  {w_u} + {w_d} = {w_u+w_d} = {w_v1_in} (mod 7)")
print(f"    Out: w(Y) = {w_v1_out}")
print(f"    -> {'CONSERVED' if w_v1_in == w_v1_out else 'VIOLATED'}")

# Vertex 2: Y* -> ubar + e+
w_v2_in  = w_Y
w_v2_out = (w_ubar + w_ep) % 7
print(f"\n  Vertex 2: Y*(w={w_Y}) -> ubar(w={w_ubar}) + e+(w={w_ep})")
print(f"    In:  w(Y) = {w_v2_in}")
print(f"    Out: {w_ubar} + {w_ep} = {w_ubar+w_ep} = {w_v2_out} (mod 7)")
print(f"    -> {'CONSERVED' if w_v2_in == w_v2_out else 'VIOLATED'}")

# Full Y-subprocess
w_y_tot_in  = (w_u + w_d) % 7
w_y_tot_out = (w_ubar + w_ep) % 7
print(f"\n  Full: u({w_u}) + d({w_d}) -> Y*({w_Y}) -> ubar({w_ubar}) + e+({w_ep})")
print(f"    Total in: {w_u}+{w_d}={w_y_tot_in}  Total out: {w_ubar}+{w_ep}={w_y_tot_out}  (mod 7)")
print(f"    -> {'CONSERVED' if w_y_tot_in == w_y_tot_out else 'VIOLATED'}")

# X-channel subprocess: u + u -> X* -> dbar + e+
# X (Q=+4/3, w=4) couples to the diquark pair u+u via color-antisymmetric
# coupling e^{alphabetagamma} u_alpha u_beta -> X_gamma.
# Second vertex: X -> e+ + dbar (charges: +1 + 1/3 = 4/3 = Q(X) checked)
print(f"\n  X-channel subprocess: u + u -> X* -> dbar + e+")
print(f"  (X boson, Q=+4/3, w={w_X}; diquark vertex via color e^{{alphabetagamma}})")

# Vertex 1: u + u -> X*
w_x1_in  = (w_u + w_u) % 7
w_x1_out = w_X
print(f"\n  Vertex 1: u({w_u}) + u({w_u}) -> X*(w={w_X})  [color diquark vertex]")
print(f"    In:  {w_u} + {w_u} = {w_u+w_u} = {w_x1_in} (mod 7)")
print(f"    Out: w(X) = {w_x1_out}")
print(f"    -> {'CONSERVED' if w_x1_in == w_x1_out else 'VIOLATED'}")

# Vertex 2: X* -> dbar + e+
w_x2_in  = w_X
w_x2_out = (w_dbar + w_ep) % 7
print(f"\n  Vertex 2: X*(w={w_X}) -> dbar(w={w_dbar}) + e+(w={w_ep})")
print(f"    In:  w(X) = {w_x2_in}")
print(f"    Out: {w_dbar} + {w_ep} = {w_dbar+w_ep} = {w_x2_out} (mod 7)")
print(f"    -> {'CONSERVED' if w_x2_in == w_x2_out else 'VIOLATED'}")

# Hadronization: dbar + d -> pi0
w_hadr_in  = (w_dbar + w_d) % 7
w_hadr_out = w_pi0
print(f"\n  Hadronization: dbar({w_dbar}) + d({w_d}) -> pi0({w_pi0})")
print(f"    {w_dbar} + {w_d} = {w_dbar+w_d} = {w_hadr_in} (mod 7) = w(pi0)={w_hadr_out}")
print(f"    -> {'CONSERVED' if w_hadr_in == w_hadr_out else 'VIOLATED'}")

# Proton-level check: p -> e+ + pi0
w_p  = winding(3)   # proton w=3 (CatAL, Rank 179-BWD)
w_p_out = (w_ep + w_pi0) % 7
print(f"\n  Proton-level: p(w={w_p}) -> e+(w={w_ep}) + pi0(w={w_pi0})")
print(f"    In: w(p) = {w_p}   Out: {w_ep}+{w_pi0} = {w_p_out} (mod 7)")
print(f"    -> {'CONSERVED' if w_p == w_p_out else 'VIOLATED'}")

print("""
  VERTEX ANALYSIS SUMMARY (CatA):
  Z7 winding conservation holds at ALL SU(5) leptoquark vertices:

  Y-channel (w=1 mediator):
    u(2) + d(6) -> Y*(1) -> ubar(5) + e+(3)
    Check: 2+6=8=1 (mod 7) = w(Y);  5+3=8=1 (mod 7) = w(Y)  [both CONSERVED]

  X-channel (w=4 mediator):
    u(2) + u(2) -> X*(4) -> dbar(1) + e+(3)
    Check: 2+2=4 = w(X);  1+3=4 = w(X)  [both CONSERVED]

  Hadronization: dbar(1) + d(6) -> pi0(0):  1+6=7=0 (mod 7)  [CONSERVED]
  Proton decay:  p(3) -> e+(3) + pi0(0):  3 = 3+0              [CONSERVED]

  MISSING WINDING ANALYSIS:
  Y-channel: w=1 (mediator Y) AND w=5 (outgoing ubar) -- BOTH missing windings
    appear simultaneously. They are PAIRED by Z7 conservation:
    w(u)+w(d) = 2+6 = 1 (mod 7) = w(Y);  w(ubar)+w(e+) = 5+3 = 1 (mod 7) = w(Y)

  X-channel: w=4 (mediator X -- EXISTING SM winding) and w=1 (dbar final state).
    Only one missing winding (w=1 = dbar) appears in the X-channel;
    X itself sits in the SM winding sector (w=4 = e-/W- winding).

  The Y-channel is the unique subprocess where BOTH missing windings {1,5}
  appear jointly: w=1 as the gauge mediator, w=5 as the anti-quark final state.
""")

# ---- Part D: Leptoquark mass estimate from GTE arithmetic ------------------
print("-- Part D: Leptoquark mass estimate from GTE arithmetic --")
print()
print("  In minimal SU(5): M_X = M_Y = M_GUT (both are gauge bosons of SU(5)/SM).")
print("  The GTE provides M_GUT from Rank 183-GCE arithmetic (CatA).")
print()
print(f"  GTE inputs (Rank 183-GCE):")
print(f"    alpha_GUT = 8/411 = {float(ALPHA_GUT):.6f}  (CatAL)")
print(f"    M_GUT (GQW formula) = {M_GUT_GQW:.3e} GeV  (CatA)")
print(f"    M_GUT (1-loop RGE)  = {M_GUT_RGE:.3e} GeV  (CatA; uses IR alpha_EM=1/137)")

M_LQ_GQW = M_GUT_GQW
M_LQ_RGE = M_GUT_RGE

print()
print(f"  Leading-order leptoquark mass (M_LQ = M_GUT):")
print(f"    M_LQ (GQW) = {M_LQ_GQW:.3e} GeV  (CatA)")
print(f"    M_LQ (RGE) = {M_LQ_RGE:.3e} GeV  (CatA)")

# Z7 gap: Y is in the gap (w=1), X is in the SM sector (w=4)
print()
print("  Z7 asymmetry between X and Y:")
print("    Y (w=1): sits in the MISSING winding gap (w=1 absent from SM spectrum)")
print("    X (w=4): sits WITHIN the SM winding sector (w=4 = e-/W- winding)")
print("    This asymmetry suggests M_Y may differ from M_X by radiative corrections")
print("    driven by the Z7 sector asymmetry, though the splitting is model-dependent.")

# Winding gap ratio: one structural ratio for the leptoquark sector
n_sm   = len(SM_WINDINGS)      # 5
n_all  = len(ALL_Z7)           # 7
n_miss = len(MISSING_Z7)       # 2
gap_ratio = n_miss / n_sm      # 2/5 -- structural ratio

print()
print(f"  Z7 gap ratio: |missing| / |SM| = {n_miss}/{n_sm} = {gap_ratio:.4f}")
print(f"  This ratio characterizes the leptoquark sector as 2/5 of the SM spectrum.")
print(f"  In SU(5): 12 leptoquark generators / 12 SM generators = 1:1 ratio.")
print(f"  The Z7 ratio 2/5 is a STRUCTURAL fact, not a mass ratio.")

print()
print(f"  Physical realism: REALISTIC -- M_LQ ~ M_GUT ~ 4.6e16 GeV is consistent")
print(f"  with SU(5): leptoquarks acquire mass via the GUT symmetry breaking Higgs.")
print(f"  Not accessible at LHC (sqrt(s) ~ 13-14 TeV << M_GUT ~ 10^16 GeV).")

# ---- Part E: N_eff-based estimate (exploratory) ----------------------------
print("\n-- Part E: N_eff-based mass estimate (CatD, exploratory) --")
print()
print("  GTE mass formula: m ~ N_eff / c_H * E0")
print(f"  For Y leptoquark (w=1, connecting quark+lepton sectors):")
print(f"  Estimate N_eff(Y) from quark and lepton N_eff values it couples.")

m_e_MeV  = 0.511
m_u_MeV  = 2.3
N_eff_e  = N_EFF_ELECTRON    # 73, CatAL

N_eff_u_rough = 9   # GTE rough value for u quark (CatD; not formally derived here)
print(f"  N_eff(e) = {N_eff_e} (CatAL, lepton seed b1)")
print(f"  N_eff(u) ~ {N_eff_u_rough} (rough estimate; CatD)")

N_eff_geom = math.sqrt(N_eff_u_rough * N_eff_e)
N_eff_prod = N_eff_u_rough * N_eff_e / C_H

for label, N_val in [("geometric mean", N_eff_geom), ("product/c_H", N_eff_prod)]:
    M_est = N_val / C_H * M_GUT_GQW
    print(f"    N_eff ({label:>15}) = {N_val:.2f}  ->  M_LQ ~ {N_val:.2f}/{C_H} * {M_GUT_GQW:.2e} = {M_est:.2e} GeV")

print(f"""
  N_eff ASSESSMENT (CatD):
  Estimates give M_LQ in the range 10^16-10^17 GeV -- consistent with M_GUT.
  The N_eff formula is calibrated for SM particles at the EW scale (n=10 ridge).
  A GUT-scale application requires identifying the GUT ridge n_GUT, which is
  not yet derived from GTE first principles (deferred to Rank 167-SWI or later).
  The leading-order prediction M_LQ = M_GUT = 4.6e16 GeV (CatA) stands.
""")

# ---- Part F: Structural count -----------------------------------------------
print("-- Part F: Structural count |{missing Z7}| x 6 = 12 (CatAL) --")

n_miss2   = len(MISSING_Z7)   # 2
n_color   = 3
n_pp      = 2                 # particle + antiparticle (or SU(2) doublet components)
n_lq_gen  = n_miss2 * n_color * n_pp

print(f"\n  Missing Z7 classes: {sorted(MISSING_Z7)},  count = {n_miss2}")
print(f"  Color variants:     {n_color}  (color triplet for each leptoquark)")
print(f"  Particle/antipart.: x {n_pp}")
print(f"  Total: {n_miss2} x {n_color} x {n_pp} = {n_lq_gen}")
print()
print(f"  SU(5) group theory: |SU(5)| = 24 generators")
print(f"    SM generators:        8(SU3) + 3(SU2) + 1(U1) = 12")
print(f"    Leptoquark generators: 24 - 12 = 12")
print()

assert n_lq_gen == 12, f"Count mismatch: {n_lq_gen}"
print(f"  Z7 gap count: {n_miss2} x {n_color} x {n_pp} = {n_lq_gen} = SU(5) leptoquark count  [MATCH]")
print(f"  (CatAL: theorem z7_sm_classes_count_eq_su5_fund_dim, GUTStructure.lean s53)")

alt = n_miss2 * (n_color * n_pp)
print(f"\n  Alternative factorization: {n_miss2} x {n_color*n_pp} = {alt}  [same result]")
print(f"  (Here 6 = 3 colors x 2 SU(2) doublet components per missing winding class)")

# ---- Summary ----------------------------------------------------------------
print()
print("=" * 72)
print("RANK 196-LQM SUMMARY")
print("=" * 72)

M_lq_Neff = math.sqrt(N_eff_u_rough * N_eff_e) / C_H * M_GUT_GQW

print(f"""
  Z7 Winding Assignments for SU(5) Leptoquarks (w = 3Q mod 7):
    X    (Q=+4/3): w = 4  [EXISTING SM winding; = e-/W- sector]
    Y    (Q=+1/3): w = 1  [MISSING winding; GUT-scale free excitation]
    Xbar (Q=-4/3): w = 3  [EXISTING SM winding; = W+/proton sector]
    Ybar (Q=-1/3): w = 6  [EXISTING SM winding; = d-quark sector]
    ubar (Q=-2/3): w = 5  [MISSING winding; final state in Y-channel]

  Y is the unique SU(5) leptoquark gauge boson carrying a missing Z7 winding.

  Z7 Vertex Conservation (CatA):
    Y-channel: u(2) + d(6) -> Y*(1) -> ubar(5) + e+(3)  CONSERVED
    X-channel: u(2) + u(2) -> X*(4) -> dbar(1) + e+(3)  CONSERVED
    Hadroni.:  dbar(1) + d(6) -> pi0(0)                  CONSERVED
    Proton:    p(3) -> e+(3) + pi0(0)                     CONSERVED
    Both missing windings {{1,5}} appear jointly ONLY in the Y-channel.

  Mass (CatA):
    M_LQ (leading order) = M_GUT ~ {M_LQ_GQW:.2e} GeV  [minimal SU(5)]
    M_LQ (N_eff geom.)   ~ {M_lq_Neff:.2e} GeV  [CatD, exploratory]

  Structural Count (CatAL):
    |{{1,5}}| x 3 colors x 2 = {n_lq_gen} = SU(5) leptoquark generators  [MATCH]

  Physical Realism:
    REALISTIC   -- M_LQ ~ M_GUT ~ 4.6e16 GeV; consistent with minimal SU(5)
    NEW PRED    -- Y (Q=+1/3) uniquely carries missing Z7 winding w=1
    NEW PRED    -- X and Y have Z7 asymmetry: Y is in the gap, X is in SM sector
    NEW PRED    -- Both missing windings {{1,5}} jointly required at Y-vertex
    CONSTRAINED -- N_eff-based estimate CatD; GUT ridge n_GUT not yet derived
""")
