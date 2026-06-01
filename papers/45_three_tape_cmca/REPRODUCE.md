# P45 — REPRODUCE

## Compilation

```bash
cd papers/45_three_tape_cmca
pdflatex three_tape_cmca_paper.tex
bibtex three_tape_cmca_paper
pdflatex three_tape_cmca_paper.tex
pdflatex three_tape_cmca_paper.tex
```

Expected output: `three_tape_cmca_paper.pdf`, ~40–50 pages, no errors.

## Lean verification

Key theorems are in the `ugp-lean` repository (commits c654f32, 4ac790a, 243764d and later).

```bash
cd /path/to/ugp-lean
lake build
# Expected: zero sorry in the modules listed in Appendix A
```

Key modules:
- `UgpLean/Gravity/RelationalTime.lean` — DPP master bundle (CatAL)
- `UgpLean/Gravity/GorardRicciFlatVacuum.lean` — vacuum Ricci-flat, causal diamond T^4/4 (CatAL)
- `UgpLean/Gravity/PMDLGravityTheorems.lean` — vacuum fixed-point, MDL uniqueness, σ-correction bound (CatAL/CatAD)
- `UgpLean/Gravity/PageWoottersZ7.lean` — τ_c PW clock validity, Z₇ Born rule, PW prerequisites (CatAL/CatAD)
- `UgpLean/Universality/BellViolationGTE.lean` — GTE polynomial qutrit values, S=2.4459 axiom, co-generation theorem (CatAL/CatA)
- `UgpLean/Algebra/SU3GluonCount.lean` — 8 gluon generators, baryon color neutrality (CatAL)
- `UgpLean/Algebra/ColorConfinementMDL.lean` — ΔK = log₂(9) (CatAL)
- `UgpLean/Algebra/BaryonNumber.lean` — B=(1/3)Σχ_q (CatAL)
- `UgpLean/Algebra/ChiralDoublet.lean` — Rule124 = Rule110 reflected (CatAL)
- `UgpLean/Algebra/ChargeFromPolynomial.lean` — 3Q(w)=p(0,w,0)=w (CatAL)
- `UgpLean/Gravity/LorentzGroupSO13.lean` — Lorentz algebra 12/12 (CatAL)
- `UgpLean/BraidAtlas/WindingToBraidRep.lean` — fermionic sector algebraic ID (CatAL)
- `UgpLean/Gravity/FermionicStatistics.lean` — zero sorry fermionic chain (CatAL)
- `ugp-physics-lean/UgpPhysicsLean/Lorentzian/MinkowskiSpace.lean` — Minkowski metric, LorentzGroup (CatAL)
- `ugp-physics-lean/UgpPhysicsLean/Lorentzian/SpinorRep.lean` — spinor 2π rotation = -1 (CatAL)
- `UgpLean/Spacetime/HolographicScaling.lean` — card = 7^{3L}, ratio 3/L² → 0 (CatAL), commit 4ac790a
- `UgpLean/Algebra/ChargeFromPolynomial.lean` (additions) — l_tape_zero_source, tape_role_asymmetry, non_separability_witness (CatAL), commit 243764d

## Key numerical scripts

All computation scripts are in `papers/45_three_tape_cmca/scripts/`.

| Computation | Script | Key result |
|---|---|---|
| Gravity coupling power law | `gradient_kick_gravity.py` | F ~ b^{-2.30}, Newtonian (b=5-70, all attracted) |
| Z7 compact Poisson gravity | `coulomb_regime_gravity.py` | F ~ b^{-2.23} instantaneous; b^{-2.41} drift (CatA) |
| **Newtonian force law continuum limit** | **`gravity_force_law_continuum_limit.py`** | **F = G·M/(4πb²)·[1+O(σ/b)²], exponent→-2.000 (CatAD)** |
| **Bell inequality violation + Born rule** | **`born_rule_bell_violation.py`** | **S = 2.4459 at G_eff=0.5; LHV excluded; threshold G≈0.095 (CatA)** |
| **Page-Wootters Born rule verification** | **`pw_born_rule_verification.py`** | **τ_c valid PW clock; P(k\|τ) independent of clock distribution (CatAD)** |
| Bell inequality violation | `bell_inequality_test.py` | CHSH S=2.44 (87% Tsirelson) |
| **L1→L2 gravity bridge (G2)** | **`level1_level2_gravity_bridge.py`** | **φ_L1=φ_L2 when G_eff·M_PMDL=4π·G_N·M_kink; G2 CLOSED (CatAD)** |
| **Born rule bridge PW→field (G3)** | **`born_rule_bridge_pw_to_field.py`** | **P_PW=P_field via ψ=∂_xΦ/√Z; G3 CLOSED (CatAD)** |
| **Bell layer reconciliation (G4)** | **`bell_layer_reconciliation.py`** | **L1 CHSH vs L2 EPR are distinct layers; G4 CLOSED (CatAD)** |
| **Polynomial continuum bridge (G1)** | **`polynomial_continuum_bridge.py`** | **p≠V_{Z7}: different physics (update vs potential); G1 CLOSED (CatAD)** |
| Gorard coefficient | `gorard_coefficient_rule110.py` | C_Gorard = 0.0923 = κ₃D/(8π); log₁₀(gap)=77.46 |
| SM particle spectrum + vertices | `three_tape_sm_particles.py` | 33 SM Z₇ vertices conserved; uniform triples (w,w,w) |
| W propagator | inline Python | G_W(r) = e^{-m_W r}/(4πr) |
| CA-native clock-gradient gravity | `clock_gradient_geodesic.py` | b^{-2.46} at α=0.1, 5/5 attracted (CatA) |
| Self-consistent gravity | `selfconsistent_gravity.py` | 5/5 attracted (CatA) |
| Tape role asymmetry | `positional_nonlocality_analysis.py` | Non-separability, 64/125 witnesses (CatA) |
| SR clock ratio | `sr_ratio_measurement.py` | 3/7 ≈ 0.4286 exact rational |

## Baryon number

B = (1/3)Σ_j χ_q(w_j) where χ_q(w) = +1 for w∈{2,6}, -1 for w∈{1,5}, 0 otherwise.
All 33 SM Z₇ vertices conserve B (CatA, exhaustive check).

## SR time-dilation ratio (corrected value)

The paper reports τ_inner/τ_outer = 3/7 ≈ 0.4286. This is the exact rational value for
a cell in the period-7 ether background under Rule 110. To reproduce:

```bash
cd papers/45_three_tape_cmca/scripts
python3 sr_ratio_measurement.py
# Expected: ratio = 0.4286 ± 0.01
```

Note: The value 0.382 reported in earlier EPIC_078 experiments was a transient artifact
from all-zero initial conditions and does not represent an invariant property of the system.

## CA-native clock-gradient gravity

Two gravity implementations are now available:

### 1. Explicit Poisson-kernel (original)
```bash
python3 scripts/three_tape_cmca.py  # native_geodesic=False
# Expected force law: b^{-2.23}
```

### 2. CA-native clock-gradient (new)
```bash
python3 scripts/three_tape_cmca.py  # native_geodesic=True (default)
# Expected force law: b^{-2.46} at alpha=0.1
```

Both give the same σ→0 Newtonian limit b^{-2.00} (CatAD).

### Supporting scripts (graduated from research-sandbox)
- `clock_gradient_geodesic.py` — CA-native gravity test (Run 079-CLOCK-GRAD)
- `selfconsistent_gravity.py` — self-consistent source test (Run 079-SELFCONSIST)
- `positional_nonlocality_analysis.py` — tape role asymmetry and non-separability (Run 079-NONLOCALITY)
- `sr_ratio_measurement.py` — SR clock ratio exact measurement

### EPIC_080 additions (2026-05-29)

| Script | Computes | Key result |
|--------|----------|------------|
| `z7_qudit_bell_cglmp.py` | Sector-dependent Bell nonlocality: (A) 3×3 qutrit CHSH; (B) full Z₇³ seven-level CGLMP | (A) S=2.4459 (CHSH violated); (B) PPT-entangled (N≤0.32) but CHSH≤2, CGLMP d=7 I₇≤1.97 (CatAD) |

Artifact: `scripts/z7_qudit_bell_cglmp_results.json`

Two-layer picture: the 3×3 qutrit sector (H_free + H_grav) violates CHSH; the full Z₇³
Hilbert space is PPT-entangled but not CHSH-violating — these are distinct physics layers.

## Gravity pipeline

Three-step: ρ(x) = p(w_x,w_y,w_z)/6 [local] → φ(x) = Σ ρ(x')/|x-x'| [Poisson] → F = +∇φ [gradient kick]
See §6 of paper for full derivation.

## Additional Lean certificates

| Theorem | Module | Commit | Statement |
|---|---|---|---|
| `particles_computation_spacetime_trinity` | `UgpLean/Universality/ParticlesComputationSpacetimeTrinity.lean` | `63c015b` | Particles--computation--spacetime trinity (CatAL) |
| `su2l_l2_from_phimdl_potential_catad` | `UgpLean/Algebra/GaugeMDL.lean` | `378ff20` | SU(2)_L from PMDL; zero named axioms (CatAL) |
| `phimdl_potential_su2l_invariant` | `UgpLean/Algebra/GaugeMDL.lean` | `378ff20` | L2 norm preserved under SU(2) |
| `su2l_covariant_derivative_minimal` | `UgpLean/Algebra/GaugeMDL.lean` | `378ff20` | Covariant derivative MDL-minimal |
| `su2l_wpm_generator_algebra` | `UgpLean/Algebra/GaugeMDL.lean` | `378ff20` | W± satisfy SU(2) Lie algebra |

Verify with `lake build` from the `ugp-lean` repository root.
