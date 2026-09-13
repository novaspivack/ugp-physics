# REPRODUCE — Paper 21: Predicting the Neutrino Mass-Squared Ratio from Braid Atlas Topological Invariants

**Paper:** `neutrino_masses_from_braid_atlas.tex`
**Last verified:** 2026-05-09

---

## Quick Start

The central prediction ($\Delta m^2_{21}/\Delta m^2_{31} = 0.02936$) can be
verified with a single computation:

```python
# Python one-liner
b = [5, 11, 19]; a = 29/9
print((b[1]**(2*a) - b[0]**(2*a)) / (b[2]**(2*a) - b[0]**(2*a)))
# Expected: 0.029359... (0.4% from NuFIT-5.2 value 0.02948)
```

---

## 1. Reproduce the Braid Atlas neutrino computations

```bash
cd papers/01_SM/canonical_run

# Neutrino mass-squared ratio prediction (EBF_17)
python3 comp_p01_EBF_17_neutrino_survey.py

# dim(126) cross-sector bridge (EBF_18)
python3 comp_p01_EBF_18_neutrino_126_bridge.py

# 29/9 structural decomposition (EBF_19)
python3 comp_p01_EBF_19_neutrino_29_9_derivation.py

# Absolute mass scale (EBF_20)
python3 comp_p01_EBF_20_neutrino_absolute_scale.py

# Full structural decomposition (EBF_21)
python3 comp_p01_EBF_21_neutrino_29_9_structural_decomp.py

# Full seesaw mechanism (EBF_22)
python3 comp_p01_EBF_22_neutrino_full_mechanism.py

# SO(10) CG / Majorana (EBF_24)
python3 comp_p01_EBF_24_SO10_CG_majorana.py

# Froggatt-Nielsen texture identification
cd ../../../papers/21_neutrino_masses/scripts
python3 comp_p21_SP2_fn_texture_b29_9.py
```

Each script emits a JSON artifact with a SHA-256 hash. Expected verdicts:
- EBF_17: ratio = 0.02936, deviation = 0.4%
- EBF_19: three decompositions all yield 29/9
- FN texture: `TEXTURE_3_2_FROM_Nc`

---

## 2. Reproduce the null test

The null test (Section 3.3) checks how many integer triples
$\{b_1 < b_2 < b_3\} \subset [2, 30]$ match the target ratio within 1%:

```python
from itertools import combinations
target = 0.02948; alpha = 29/9; hits = 0; total = 0
for b1, b2, b3 in combinations(range(2, 31), 3):
    total += 1
    r = (b2**(2*alpha) - b1**(2*alpha)) / (b3**(2*alpha) - b1**(2*alpha))
    if abs(r - target) / target < 0.01:
        hits += 1
print(f"{hits} / {total} = {100*hits/total:.2f}%")
# Expected: 8 / 3654 = 0.22%
```

---

## 3. Verify Lean theorems

```bash
git clone https://github.com/novaspivack/ugp-lean
cd ugp-lean

# Seesaw exponent structural decompositions
lake build UgpLean.MassRelations.SeesawIndex
# Proves: seesaw_index_is_gauge_matter_defect (45 - 16 = 29)

# Three decompositions of 29/9
lake build UgpLean.MassRelations.NeutrinoSeesawExponent
# Proves: nu_seesaw_exponent_three_decompositions

# Froggatt-Nielsen texture uniqueness
lake build UgpLean.MassRelations.NeutrinoFroggattNielsen
# Proves: fn_structural_texture_existence_and_uniqueness

# Koide angle from N_c
lake build UgpLean.MassRelations.KoideAngle
# Proves: koide_angle_from_N_c_pure (θ = 2/9 from N_c = 3)

# Scale independence of mass ratios
lake build UgpLean.MassRelations.ScaleTransport
# Proves: mass_ratio_Z_independent
```

Expected: All build successfully with 0 sorry.
Lean 4.29.0-rc6, Mathlib 4.29.0-rc6.

---

## 4. Build the PDF

```bash
cd papers/21_neutrino_masses
pdflatex neutrino_masses_from_braid_atlas.tex
bibtex neutrino_masses_from_braid_atlas
pdflatex neutrino_masses_from_braid_atlas.tex
pdflatex neutrino_masses_from_braid_atlas.tex
```

Expected: ~18 pages, 0 undefined citations, 0 errors.

---

## Key Data Sources

- NuFIT-5.2 global fit: $\Delta m^2_{21} = 7.42 \times 10^{-5}$ eV²,
  $\Delta m^2_{31} = 2.517 \times 10^{-3}$ eV²
- Braid Atlas right-handed neutrino $b$-values: {5, 11, 19}
- Planck 2018 bound: $\sum m_\nu < 0.12$ eV (95% C.L.)

## Dependencies

- Python 3.9+ (numpy, scipy)
- TeX Live 2025 (pdflatex + bibtex)
- ugp-lean (Lean 4.29.0-rc6, Mathlib 4.29.0-rc6) — for Lean verification only

---

## 5. NeutrinoMassRatio.lean — Lean Certification (complete, all phases)

**Module path:** `UgpLean.MassRelations.NeutrinoMassRatio`
**File:** `~/ugp-lean/UgpLean/MassRelations/NeutrinoMassRatio.lean`
**Graduated to ugp-lean:** 2026-05-16 (EPIC_052 Phase 1+2, zero sorry)

### What it proves

Five theorems, all zero sorry:

1. **`fn_texture_gives_seesaw_exponent`** — The FN charge pair (q₁,q₂)=(3,2) satisfies
   q₁ + q₂/N_c² = 3 + 2/9 = 29/9 = nuSeesawExponent. Proves the arithmetic link
   from the MDL-unique FN texture to the seesaw exponent.

2. **`seesaw_ratio_independent_of_MR`** — In a Type-I seesaw with m_i = C·x_i,
   the mass-squared ratio (m₂²−m₁²)/(m₃²−m₁²) = (x₂²−x₁²)/(x₃²−x₁²) is
   independent of C (hence independent of M_R). Proves the Category A (parameter-free)
   status of the ratio by pure ring algebra.

3. **`neutrino_mass_ratio_coarse_bound`** — Certifies 0.029 < R < 0.030 where
   R = (11^{58/9}−5^{58/9})/(19^{58/9}−5^{58/9}). Proved via monotone 9th-power
   integer comparisons: each b^{58/9} is bounded by checking (lower)⁹ < b⁵⁸ < (upper)⁹
   using `norm_num` on exact integers.

4. **`neutrino_mass_ratio_tight_bound`** — Certifies |R − 0.02936| < 0.0001 via
   unit-width integer bounds: 31950 < 5^(58/9) < 31951, 5142772 < 11^(58/9) < 5142773,
   174123159 < 19^(58/9) < 174123160 (all verified by `norm_num`). Reducing to
   exact ~74-digit integer comparisons closes the tight bound without sorry.

5. **`neutrino_mass_ratio_within_1pct_of_nufit`** — Certifies |R − 0.02951| < 0.01 × 0.02951;
   R is within 1% of the NuFIT 6.0 central value 0.02951. Follows from the tight bound
   via `linarith` on the interval R ∈ (0.02926, 0.02946).

### Scope

The arithmetic/algebraic chain is complete: FN texture → exponent 29/9 → M_R cancellation
→ coarse bound 0.029 < R < 0.030 → tight bound |R − 0.02936| < 0.0001 → NuFIT 1%
comparison. The full Lagrangian bridge (formal derivation that Yukawa couplings scale as
b^{q₁} and b^{q₂} from the FN texture) remains open and will require a companion
`NeutrinoLagrangian.lean` module.

### Verification

```bash
cd ~/ugp-lean
lake build UgpLean.MassRelations.NeutrinoMassRatio
# Expected: 0 errors, 0 sorry
```

## 083C additions (2026-06-02): PMNS mixing angles and Jarlskog invariant

New scripts graduated from research-sandbox:

| Script | Produces |
|---|---|
| `papers/21_neutrino_masses/scripts/pmns_orbit_ratio_final.py` | Three PMNS angles: sin²θ₁₂=4/13 (+0.27σ), sin²θ₂₃=19/42 (+0.22σ), sinθ₁₃=11/73 (+0.67σ); χ²=0.564 |
| `papers/21_neutrino_masses/scripts/pmns_jarlskog_derivation.py` | Jarlskog J_GTE = −(8184√437/5057221)×sin(π/7) |

Run with `python3 <script path>` from the repo root.

New Lean certificates (all zero sorry, `ugp-lean/UgpLean/MassRelations/NeutrinoSector.lean`):
- `pmns_solar_sin_sq` — sin²θ₁₂ = 4/13
- `pmns_atm_sin_sq` — sin²θ₂₃ = 19/42
- `pmns_reactor_sin_val` — sinθ₁₃ = 11/73
- `gte_jarlskog` — J_GTE formula
- `fn_dirac_yukawa_rank_theorem` — FN rank-1 structure (CatAL)
- `pmns_cp_phase_from_z7_winding` — δ_CP = 205.71° from Z₇ winding (CatAL)

## 083D additions (2026-06-04): M_R GUT-scale common seesaw denominator

The GTE derivation of M_R via the seesaw chain E_D²/C can be reproduced with:

```bash
python3 research-sandbox/mr1_derivation.py
```

Key computation (Mechanism E in the script):
```python
alpha = 29/9; b = [5, 11, 19]
C = 0.0594 / sum(bi**alpha for bi in b)   # eV
E_D = 246.16 / 29                          # GeV
M_R = (E_D * 1e9)**2 / C / 1e9            # GeV
# Result: M_R ≈ 1.897e16 GeV ≈ 0.90 × M_GUT
```

All inputs are GTE-structural (Σm_ν = 59.4 meV CatA; E_D = v_H/29 CatAD; α = 29/9 CatAL; b-values {5,11,19} CatAL). Result in `research-sandbox/mr1_derivation_results.json`.

Note: this M_R is the common GUT-scale seesaw denominator, distinct from the leptogenesis M_R1 ≈ 1.11×10¹³ GeV in companion cosmological work.

## 083D additions (2026-06-03): θ₂₃ NLO orbit search

New script graduated from research-sandbox:

| Script | Produces |
|---|---|
| `papers/21_neutrino_masses/scripts/theta23_orbit_search.py` | Orbit-ratio candidates within 0.5σ/1σ of NuFIT 6.0 IC24 NH sin²θ₂₃ = 0.470; NLO correction mechanism survey (mechanisms A–K); null tests confirming 19/42 is structurally pinned |

Run with `python3 papers/21_neutrino_masses/scripts/theta23_orbit_search.py` from the repo root.
Results written to `theta23_orbit_search_results.json` in the working directory.
