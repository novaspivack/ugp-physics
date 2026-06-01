# P45 — PROVENANCE

**Paper:** The Three-Tape Chiral Minkowski Cellular Automaton: Spacetime, Particles, and Gravity from a Shared Clock Protocol
**Status:** Draft (2026-05-28)
**Primary author:** Nova Spivack
**Created:** 2026-05-28 (EPIC_079 session)

## Research provenance

This paper presents results from EPIC_079 (Three-Tape CMCA Research Programme), which began 2026-05-28 as an extension of EPIC_078.

### Three-tape CMCA breakthrough (2026-05-28)

The three-tape architecture ((R110⊕R124⊕inner_τc)^3 with shared outer τ_c clock) was identified as the correct 3+1D GTE dynamics. Key results established in the initial session:

- Three-tape Class 4 dynamics with sustained gliders (CatA)
- SR time dilation: τ_inner/τ_outer = 3/7 ≈ 0.4286 (CatA; corrected from initial 0.382 transient)
- V-A chirality: Rule 110 right-chiral, Rule 124 left-chiral (CatA)
- SM particle spectrum from uniform triples (25 vertices, CatA)
- DPP: shared clock as 3+1D synchronization (CatAD, CatAL)
- Gravitational coupling: τ_c clock-rate modulation (CatA)
- Gorard curvature: vacuum Ricci-flat (CatAL), matter curvature (CatA)
- Bell inequality violation: S=2.44 from gravitational coupling (CatA)
- Baryon number: B=(1/3)Σχ_q from N_tapes=3 (CatAD+CatAL)
- Color confinement: ΔK=log₂(9) from MDL (CatAL)
- SU(3): 8 gluons from Δw=±1 (CatAL)
- Proton structure: (2,2,6) non-uniform triple encoding (CatAD)
- Permanent CMCA solitons via ether-period-14 resonance (CatA)
- W boson propagator: G_W = e^{-m_W r}/(4πr) from universal propagator (CatAD)
- Three colored chiral doublets (u,d)_r,g,b from three tapes (CatA)
- W± = Δw=3 angular mode of Z₇ doublet (CatAD-Provisional)

### Lean certifications (from ugp-lean, 2026-05-28)

- DPP theorems: commit from EPIC_079 DPP session
- Gorard vacuum Ricci-flat + causal diamond: commit 0b17663
- PMDLGravityTheorems: commits from PMDL session
- SU3GluonCount (8 gluons, baryon color): commit f4167a8
- ColorConfinementMDL (ΔK=log₂9): commit 97ca987
- BaryonNumber (B topological charge): commit 89d009e
- ChiralDoublet (Rule124 = Rule110 reflected): commit c654f32
- ChargeFromPolynomial (3Q=p(0,w,0)=w): commit 2637246
- WindingToBraidRep (fermionic sector algebraic ID): commit ee16be9
- FermionicStatistics (zero sorry chain): commit 055ae51
- LorentzGroupSO13 (12/12 commutation): commit 0dc2cfd
- SRRGCABridge (1/φ = CA fixed point): commit c654f32
- GaugeMDL (SU(2)_L mechanism): commit a82b711
- Lorentzian library Stage 1+2: commit aa3af4a (ugp-physics-lean)

### Cross-references

- P41 (CMCA Algebraic Certificate): Three-tape CMCA extends P41 to 3+1D
- P42 (Φ_MDL Field): Born rule 3D from this paper
- P43 (Φ_MDL Completeness): Gorard, SR, DPP connect here
- P44 (QGR Completeness): Shared gravity coupling mechanism
- P46 (GTE Polynomial Unification): Companion algebraic paper

## Evening session additions (2026-05-28)

### New Lean certifications
- `UgpLean.Spacetime.HolographicScaling` (commit 4ac790a, ugp-lean):
  - `three_tape_state_card`: card = 7^{3L}
  - `naive_3d_state_card`: card = 7^{L³}
  - `three_tape_smaller_than_3d`: 7^{3L} < 7^{L³} for L ≥ 2
  - `holographic_ratio_formula`: 3L/L³ = 3/L²
  - `holographic_ratio_vanishes`: 3/L² → 0
  - `three_tape_holographic_L7`: L=7 instance
- `UgpLean.Algebra.ChargeFromPolynomial` (commit 243764d, ugp-lean, additions):
  - `l_tape_zero_source`: p(w,0,0)=0 for all w
  - `tape_role_asymmetry`: p(0,w,0)=w and p(0,0,w)=w
  - `non_separability_witness`: p(0,2,2)≠p(0,2,0)+p(0,0,2)
  - `gravity_requires_cross_tape_coordination`

### SR ratio reconciliation (commit aed6cd07, ugp-physics)
- Corrected τ_inner/τ_outer from transient 0.382 (all-zero IC artifact) to exact rational 3/7 ≈ 0.4286
- Period-7 ether orbit: odd-parity cells fire 3/7 steps; even cells 5/7; global average 4/7
- Updated `verification_suite.py`, paper §5/SR theorem, Appendix B verification table
- Analytic script: `sr_ratio_measurement.py`

### New computational results (CatA)
- CA-native clock-gradient gravity: b^{-2.46} at α=0.1, 5/5 attracted (`clock_gradient_geodesic.py`)
- Self-consistent gravity: attraction confirmed, 5/5 (`selfconsistent_gravity.py`)
- Positional non-locality: tape role asymmetry, non-separability 64/125 witnesses (`positional_nonlocality_analysis.py`)
- SR clock ratio: 3/7 ≈ 0.4286 exact rational from period-7 ether orbit (`sr_ratio_measurement.py`)

### Holographic structure
The three-tape CMCA is holographic: three 1D arrays of length L encode 3+1D physics
with |State_space|=7^{3L}, while the corresponding 3D lattice would require 7^{L³}.
The ratio 3L/L³ = 3/L² → 0 (proved CatAL, HolographicScaling.lean).

### Tape role asymmetry
The polynomial p(L,C,R)=C+R-CR-LCR has degree-stratified physical roles:
- Degree-1 (EM charge): p(0,w,0) = p(0,0,w) = w (tape_y/z alone)
- Degree-3 (gravity): -LCR cross-term requires all three tapes non-vacuum
- tape_x alone (L position): p(w,0,0) = 0 for all w (notation artifact, S₃ symmetric)

## AI disclosure

This research was conducted with assistance from AI coding tools (Cursor, Claude) for computation, Lean verification, and manuscript preparation, subject to independent verification of all results. The scientific content, direction, and interpretation are the sole work of the author.
