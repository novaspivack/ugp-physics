# P43 — Paper Notes

**Working title:** The Complete Φ_MDL Framework: Quantum Mechanics, Gravity, and the Impossibility of a Cellular Automaton Universe
**Status:** STUB — do not write until EPIC_075 (gravity/GR) is complete
**Primary epic:** EPIC_074 (QM/discrete) + EPIC_075 (gravity, TBD)
**Page target:** ~25–30 pp
**Last updated:** 2026-05-26

---

## Scientific purpose

This paper presents the complete, unified picture of the GTE/Φ_MDL framework as a finished physical theory. It synthesizes results from P40–P42 (and EPIC_075 gravity results) into a single coherent statement of what the framework claims and what it proves.

---

## What this paper IS

P43 is the "final model" paper — it makes the strong claim that Φ_MDL is the complete description of the universe and proves why no cellular automaton (discrete or quantum) can replace it. It addresses:
1. The complete QM picture (Born rule, measurement, EPR, quantum eraser — from EPIC_074 + OIR)
2. The no-CA-replica theorem (Lean-certified)
3. The gravity sector (from EPIC_075 — Einstein equations, spacetime emergence)
4. Why the two-level framework (CMCA + Φ_MDL) is the right picture
5. Comparison to other frameworks (Copenhagen, many-worlds, Wolfram, etc.)

NEW NOTE - please alse read the epic 072 FINAL_THEORY and the OIR to integrate those into this paper - in particular we need to explain the measurement theory angle as well 

---

## What this paper is NOT

- Not a replacement for P41 (CMCA technical details) or P42 (Φ_MDL field theory)
- Not a repeat of P36 (emergent gravity basics) or P37 (QM from Rule 110)
- Not a review paper — it has specific new theorems as its core

---

## Core new theorems (already proved, from EPIC_074)

| # | Theorem name | File | Sorry | Cat | Physical meaning |
|---|---|---|---|---|---|
| 1 | `no_finite_ca_exact_lorentz_replica` | `CMCAContinuumLimit.lean` | 0 | CatAL | No finite-M CA has exact Lorentz invariance; ε₀(M) = π²/(3M²) > 0 for all M > 0 |
| 2 | `phimdl_is_unique_exact_lorentz_model` | `CMCAContinuumLimit.lean` | 0 | CatAL | Φ_MDL is the unique zero-error limit (M → ∞) |
| 3 | `outer_totalistic_is_reflection_invariant` | `NoClass4OuterTotalisticZ7.lean` | 0 | CatAL | Outer-totalistic rules cannot be chiral |
| 4 | `no_class4_outer_totalistic_z7_3d` | `NoClass4OuterTotalisticZ7.lean` | 0 | CatAL conditional | No outer-totalistic Z₇ CA has Class 4 behavior (1 physics axiom: chirality necessary for Class 4) |
| 5 | `commutes_with_winding_iff_diagonal` | `WindingCoinDecoupling.lean` | 0 | CatAL | Z₇-winding-conserving quantum coins are diagonal; diagonal coins decouple sectors |
| 6 | `diagonal_coin_decouples_sectors` | `WindingCoinDecoupling.lean` | 0 | CatAL | Structural impossibility of linear QCA localization |
| 7 | `phimdl_domain_wall_junction_tension_exact` | `WindingCoinDecoupling.lean` | 0 | CatAL | λ_dim = −16/49 exactly (attractive domain wall junctions) |

All theorems from ugp-lean, committed 2026-05-26. Zero sorry (theorems 1–7 have no custom physics axioms except theorem 4's single physics axiom).

---

## Key computational results (from EPIC_074 sessions)

- **Dimensional dissipation staircase** (074-2D-DISSIP-STAIRCASE, CatA):
  1+1D persistent gliders / 2+1D transient marginal (T~200) / 3+1D pure vacuum-chaos bifurcation
- **λ(step_fmdl3d) = 0.8575 ≈ 6/7** (074-3D-LAMBDA-VERDICT, CatAD): chaos saturation, exhaustive 823,543 inputs
- **No-Class-4 phase** (074-3D-NOCLASS4-THM, CatA): 0 Class 4 hits across 510 outer-totalistic Z₇ vN-6 rule trials; sharp λ_c ≈ 0.54 ± 0.04
- **Descent map** (074-DESCENT-EXPLICIT, CatA): Cook A-glider → Φ_MDL BPS kink, RMSD = 5.34% < ε₀(7) = 6.71%, Q = 1/7 exactly, Pearson r = 0.994
- **QCA** (074-QCA-3D + 074-QCA-WINDING-COIN, CatAD): Z₇ quantum walk spreads ballistically but winding-conserving coins are diagonal → sectors decouple → no localized kinks; wave-packet only
- **Z₇-GoL** (074-Z7GOL-3D, CatA): decorating 3D GoL with Z₇ winding gives non-PSC-admissible, winding-non-conserving structures; Conway B3/S23 lift equally robust — Z₇ winding is arithmetic ledger, not topological invariant
- **MDL distinguisher** (074-3D-MDL-DISTINGUISH, CatAD): K_CMCA = 19 bits ≪ K_Z₇GoL ≥ 40 bits (≥21-bit deficit)
- **Domain wall junction** (074-VORTEX-3D, CatA): λ = −1654.77 MeV/fm (analytically exact: λ_dim = −16/49); junctions release energy; no topological vortex strings (π₁(Z₇) = 0)
- **3D-CA comprehensive search**: 19 distinct rule families × ≥1,030 random + structured seeds across 6 Genius Team sessions = 0 GTE-consistent 3D discrete particles found

---

## QM/measurement section (from OIR and FINAL_THEORY in EPIC_072)

Content to draw from:
- **Objective Reduction (OR):** [D]-selection = PSC/PI minimization (not gravitational). P⊤ = argmin_ρ D(ρ|w) is objective, determinate, non-computable; replaces Copenhagen collapse
- **EPR/Bell:** resolved via semantic nonlocality (NEMS P45/P46; GTE escapes Bell via non-computable D3)
- **Quantum eraser:** resolved via [D]-selection (determinate, non-computable)
- **Transputation P⊤** (CatAL conditional, `TransputationStateSelector.lean`)
- **Born rule** from Hamiltonian thermal state on PSC-admissible kink sectors (`born_rule_unconditional`, zero custom axioms; `PhiMDLThermalState.lean` 277 lines zero sorry)
- **Two-function QM:** Born (B) + Transputation (P⊤)
- **L3 thermal state** (76-L3-LEAN, CatAL conditional): equal BPS mass 8m/49; vacuum-dominance at cosmic temperatures (P_vac/P_particle = e^{M_k/T} ≫ 1 at T_CMB)
- **Comparison to Copenhagen:** GTE is objective collapse via [D]-minimization, not observer-dependent
- **Comparison to many-worlds:** GTE has P⊤ selecting ONE branch; no proliferation; no-emulation theorem rules out block universe

---

## EPIC_075 placeholder (gravity sector — write when ready)

**[PLACEHOLDER: Insert EPIC_075 results here]**

Expected content:
- Einstein equations from Φ_MDL stress tensor (emergent GR)
- Spacetime curvature from [D]-weighted kink density
- Black hole thermodynamics from domain wall entropy (H3 holography — 2+1D Φ_MDL continuum domain walls as codimension-1 boundary, consistent with S = A/4)
- Planck scale: discrete CMCA lattice at a = l_P
- Connection to CDT/LQG/string theory comparison

---

## Proposed section structure

1. Abstract
2. Introduction — the final model statement
3. The substrate: Φ_MDL as the unique Z₇-symmetric field
   - MDL-minimality → Φ_MDL uniqueness
   - The no-finite-CA-replica theorem (theorems 1–2)
4. The discrete-to-continuum bridge
   - 1+1D CMCA as algebraic certificate
   - The dimensional dissipation staircase
   - The descent map (Cook A-glider → BPS kink)
   - Why QCA cannot replace Φ_MDL (theorems 5–6)
   - Why outer-totalistic Z₇ cannot produce Class 4 (theorems 3–4)
5. Quantum mechanics from Φ_MDL
   - Born rule, thermal state, transputation (theorem from P42)
   - Measurement, EPR, quantum eraser
   - Comparison to Copenhagen, many-worlds
6. Gravity from Φ_MDL [EPIC_075 section — placeholder]
   - Einstein equations, spacetime emergence
   - Black hole entropy from domain walls (H3 holography; theorem 7)
7. The complete two-level framework
   - Discrete level: algebraic certificate (F_21, Z₇, confinement)
   - Continuum level: dynamics (Φ_MDL field equation)
   - Why both are needed, why neither is sufficient alone
8. Conclusions
- Appendix A: Lean inventory
- Appendix B: Computational methods

---

## Papers to cite heavily

P28, P34, P35, P36, P37, P40, P41, P42 (all in `Spivack_Papers_Bibliography.bib` — use concept DOIs)

---

## What to wait for before writing

- EPIC_075 results on Einstein equations / emergent gravity
- Updated P36 (if EPIC_075 extends it significantly)
- Any new Lean theorems from EPIC_075
- Final graduation of P41/P42 Lean modules to ugp-lean
- Do a read-through of epic 072 FINAL_THEORY and the OIR to see if we need to include anything else (measurement theory explaining SR reference frames with D minimization?)

---

## Timeline

- P41 and P42 updates: 2026-05-26 ✓
- EPIC_075: next epic
- P43 draft: after EPIC_075 completes
- P43 submission: after 2 revision passes

---

## EPIC_075 Results to Include (added 2026-05-26)

### New theorems from EPIC_075 (all CatAD unless noted)

| Result | Status | Source |
|--------|--------|--------|
| T_μν = ∂_μΦ ∂_νΦ − g_μν ℒ (fully derived, numerically verified) | CatAD | P38, phimdl_tmunu_full.py |
| G_μν = 8πG T_μν derived (not postulated) via MDL-Lovelock + minimal coupling | CatAD | P38, P35 |
| ∫T_00 dx = M_kink = 290.0996 MeV (rel. error 1.4×10⁻⁶) | CatA | P38 |
| Classical Λ = 0 exactly at all 7 Z₇ vacua (Lean-certified) | CatAL | P38, StressEnergyTensor.lean |
| M_Pl^GTE = π/√3 ≈ 1.81 lattice units (τ_c fluctuation scale) | CatAD | P38, 28-QGR |
| Penrose OR time ~20.8 Myr for single kink | CatAD | P38, 80-QGR |
| 17-GEO Pass 4: 7 new CatAL theorems (PSC preservation, Ehrenfest) | CatAL | GeodesicTheorem.lean |
| 32-ALT2 async lifting = sync ALT (one-line proof) | CatAL | AsyncLiftingTheorem.lean |
| T_μν symmetry, vacuum-zero, gravity prerequisites bundle | CatAL | StressEnergyTensor.lean |

### New open problems from EPIC_075 (for §Open Problems section)

1. **Newton's G (075-HIER):** M_Pl/m_τ ≈ 7×10¹⁸ with no Z₇ arithmetic mechanism identified. Newton's constant G is not yet derivable from GTE. This is EPIC_075's deepest open problem — the gravitational hierarchy problem in GTE form.

2. **Cosmological constant quantum corrections (075-COSMO):** Classical Λ = 0 is a natural GTE prediction (Z₇ vacua are exactly at V = 0). But one-loop ZPE is 10⁴⁵ above observed dark energy. The classical result is favorable vs generic QFTs, but the quantum hierarchy remains open.

3. **Lorentzian causal OR (075-CAGEO):** The CA/continuum bridge for gravity requires Lorentzian (not spacelike) Ollivier-Ricci curvature. Spacelike OR measures boundary curvature; bulk Ricci scalar requires timelike/lightlike edges. This is a deep geometric open problem.

4. **Full geodesic theorem CatAL (17-GEO):** Needs distributed P34 [D] measure + Ollivier-Ricci curvature correction. Pass 4 achieved orbital persistence; full dynamical geodesic remains CatAD.

5. **Full QGR (80-QGR):** Operator EFE, graviton Fock space, non-perturbative QGR. Prerequisite: G from GTE (075-HIER). Multi-year programme.

### Papers to reference from §Gravity

- P36: Emergent gravity, τ_c geodesics, equivalence principle, discrete track
- P38: Φ_MDL stress-energy, EFE, kink mass, Λ = 0, QGR scale
- P35: MDL-Lovelock (gravity action from MDL-minimality)
- P37: Quantum mechanics from Rule 110 (for QM sector)
- P42: Φ_MDL field (for QM/field theory sector)

### Updated timeline note

P43 can now be written with QM (EPIC_074) and gravity fundamentals (EPIC_075 Cluster F). The main blocking item for a truly complete synthesis is:
1. Newton's G derivation (075-HIER) — or honest disclosure of this as open
2. Full QGR (80-QGR) — or honest disclosure as long-term programme

A strong P43 CAN be written now with these as clearly disclosed open problems. The paper's central result (no-CA-replica theorem + two-level framework completeness) does not require closing these gaps.
