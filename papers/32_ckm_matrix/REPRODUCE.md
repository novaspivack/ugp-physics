# Reproduction Guide — P32 CKM Matrix Paper

**Paper:** The CKM Wolfenstein Parameters from Generative Triple Evolution Orbit Arithmetic
**Status:** Draft — reproduction guide stub; to be completed with final script paths and
artifact hashes before submission.

---

## Lean 4 Certification

Machine-certified results formalized in `ugp-lean` (graduate to `ugp-lean` before Zenodo).

### Repository

```
ugp-lean (graduate to ugp-lean before submission)
```

### Key modules

| Module | Contents |
|---|---|
| `UgpLean/Universality/GUTStructure.lean §14` | λ = 9/40 arithmetic theorems |
| `UgpLean/Universality/GUTStructure.lean §15` | Quark N_eff structural formulas; cross-sector identity |

### Key theorems (all zero sorry)

| Theorem | Module | Tactic | Result |
|---|---|---|---|
| `wolfenstein_lambda_formula` | GUTStructure §14 | `norm_num` | λ = 9/40 |
| `ckm_dof_count` | GUTStructure §14 | `norm_num` | N_gen² = 9 |
| `gut_capacity_times_ring` | GUTStructure §14 | `norm_num` | 2^N_gen × N_fam = 40 |
| `wolfenstein_A_sq_rational` | GUTStructure §15 | `norm_num` | A² = 186/275 |
| `ckm_unitarity_triangle_radius_eq_gut_weinberg` | GUTStructure §15 | alias | R_b = 3/8 = sin²θ_W(GUT) |
| `ckm_from_gte_arithmetic` | GUTStructure §15 | `norm_num` | Combined CKM structure |
| `neff_u_eq_ngen_sq` | GUTStructure §15 | `norm_num` | b_u = 9 |
| `neff_d_eq_nfam` | GUTStructure §15 | `norm_num` | b_d = 5 |
| `neff_c_eq_nfam_poly` | GUTStructure §15 | `norm_num` | b_c = 275 |
| `neff_s_eq_gen_higgs_form` | GUTStructure §15 | `norm_num` | b_s = 186 |
| `neff_b_eq_mersenne` | GUTStructure §15 | `norm_num` | b_b = 8191 (Mersenne) |
| `bb_bs_product_not_square` | GUTStructure §15 | bounded arith. | b_b × b_s not a perfect square → tan(γ) irrational |
| `ngen_plus_nfam_eq_pow2` | GUTStructure §13 | `norm_num` | N_gen + N_fam = 2^N_gen |
| `gut_weinberg_angle_pow2` | GUTStructure §5 | `norm_num` | sin²θ_W(GUT) = 3/8 |

**Commit:** `c4b0ae5` (GUTStructure §15 quark N_eff + cross-sector identity)

### Build verification

```bash
cd /Users/nova/ugp-lean
lake build UgpLean.Universality.GUTStructure
```

Expected: all jobs complete, zero errors, zero sorry.

### Remaining Lean task (pre-submission)

Formal derivation of each quark N_eff value from GTE cascade axioms (rather than
from locked finite maps in the discovery engine). This upgrade converts the physical
identification of A, ρ̄, η̄ from CatA to CatAL.

---

## Python scripts (graduated 2026-05-20)

```bash
cd papers/32_ckm_matrix/scripts
python3 ckm_from_gte.py          # primary: all four Wolfenstein parameters, CKM matrix to O(λ⁴), J
python3 cp_violation_mersenne.py # Mersenne hierarchy; CP angle γ; top quark formula
python3 wolfenstein_parameter.py # λ = N_gen²/(2^N_gen × N_fam) = 9/40 verification
python3 ckm_count_theorem.py     # CKM d.o.f. count: U(n) dim = n²; λ = 9/40
```

All scripts produce stdout only. Key expected outputs:
- λ = 9/40 = 0.225000 (PDG 0.22500 ± 0.00067, 0.000% error)
- A = 0.8224, γ = 65.67°, J = 2.999×10⁻⁵

---

## Compilation

```bash
cd papers/32_ckm_matrix
pdflatex ckm_matrix_paper.tex
bibtex ckm_matrix_paper
pdflatex ckm_matrix_paper.tex
pdflatex ckm_matrix_paper.tex
```

---

## Graduation checklist (full reproducibility)

### Lean (`ugp-lean` → `ugp-lean`)

| Section | Key theorems |
|---------|----------------|
| §14 | `wolfenstein_lambda_formula`, `ckm_dof_count` |
| §15 | `neff_*`, `ckm_from_gte_arithmetic`, `ckm_unitarity_triangle_radius_eq_gut_weinberg` |
| §25, §30, §33, §34, §40, §41, §72 | Extended CKM / CP block; §72 commit `aa110d3` |

### Python ✅ (2026-05-20)
| Script | Location |
|--------|----------|
| `ckm_from_gte.py` | `scripts/` ✅ |
| `cp_violation_mersenne.py` | `scripts/` ✅ |
| `wolfenstein_parameter.py` | `scripts/` ✅ |
| `ckm_count_theorem.py` | `scripts/` ✅ |

Scripts are stdout-only. JSON artifact files (`quark_neff_table.json`, `wolfenstein_predictions.json`, `ckm_matrix_olambda4.json`) are not yet generated; scripts can be extended to emit them when needed.

### Lean ⏳ (`ugp-lean` → `ugp-lean`)

After graduation: update REPRODUCE/README Lean repo name; re-pin appendix commits.

---

*REPRODUCE.md — P32 — 2026-05-20*
