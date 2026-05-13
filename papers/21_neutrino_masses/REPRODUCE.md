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
python3 comp_p01_EBF_18_126_bridge.py

# 29/9 structural decomposition (EBF_19)
python3 comp_p01_EBF_19_29_9_derivation.py

# Absolute mass scale (EBF_20)
python3 comp_p01_EBF_20_absolute_scale.py

# Full structural decomposition (EBF_21)
python3 comp_p01_EBF_21_structural_decomposition.py

# Full seesaw mechanism (EBF_22)
python3 comp_p01_EBF_22_full_mechanism.py

# SO(10) CG / Majorana (EBF_24)
python3 comp_p01_EBF_24_SO10_CG_Majorana.py

# Froggatt-Nielsen texture identification
python3 comp_p24_SP2_fn_texture_b29_9.py
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
