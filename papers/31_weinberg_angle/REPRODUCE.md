# Reproduction Guide — P31 Weinberg Angle Paper

**Paper:** Arithmetic Derivation of the Electroweak Mixing Angle from Rule 110 Orbit Arithmetic
**Status:** Draft — Python scripts graduated 2026-05-20; Lean graduation pending

---

## Lean 4 Certification

Machine-certified results are formalized in `ugp-lean` (graduate to `ugp-lean` before Zenodo).

### Repository

```
ugp-lean (graduate to ugp-lean before submission)
```

### Key modules

| Module | Contents |
|---|---|
| `UgpLean/Universality/GUTStructure.lean §10` | Palindrome decomposition theorems (Steps 7a/7b) |
| `UgpLean/Universality/GUTStructure.lean §12` | Weinberg closure theorems (Steps 7c/7d/8); commit `596b190` |
| `UgpLean/Universality/GUTStructure.lean §4–6` | GUT Weinberg formula (`gut_weinberg_angle_pow2`) |
| `UgpLean/Universality/GUTStructure.lean §13` | Running shift identity (`running_shift_is_z5_ring`) |
| `UgpLean/Universality/EWBosonStructure.lean` | EW c-staircase; scalar boundary |
| `UgpLean/GTE/BraidAtlas.lean` | N_gen = 3 (GoE orbit); b_H = 3; N_fam = 5 |

### Key theorems (zero sorry)

| Theorem | Module | Tactic |
|---|---|---|
| `fmdl_palindrome_nonwplus_count_eq_ngen` | GUTStructure §10 | `native_decide` |
| `fmdl_nonpalindrome_nonzero_count_eq_two_nfam` | GUTStructure §10 | `native_decide` |
| `weinberg_angle_closure` | GUTStructure §12 | `norm_num` |
| `weinberg_angle_derivation` | GUTStructure §12 | `native_decide + norm_num` |
| `gut_weinberg_angle_pow2` | GUTStructure §4–5 | `norm_num` |
| `running_shift_is_z5_ring` | GUTStructure §13 | `norm_num` |
| `gte_family_capacity_identity` | GUTStructure §13 | `norm_num` |

### Remaining Lean task (pre-submission)

```lean
-- In GUTStructure.lean §12, add:
import UgpLean.Dynamics.EWStructure   -- P22 bridge module

-- Then instantiate the conditional:
theorem weinberg_angle_unconditional :
    sin²θ_W = (3 : ℚ) / 13 := by
  exact weinberg_angle_derivation doublet_partner_is_left_chiral
```

---

## Python scripts (graduated 2026-05-20)

```bash
cd papers/31_weinberg_angle/scripts
python3 double_mersenne_endpoint.py     # n=3 uniqueness; other-universe parameter table
python3 palindrome_identification.py    # 343-neighborhood palindrome census; Z₂ orbit split
python3 weinberg_angle_arithmetic.py    # sin²θ_W = 3/13; bare/running arithmetic
```

All three scripts produce stdout only. Key output values:
- `double_mersenne_endpoint.py`: n=3 is the unique integer ≥2 with both 2ⁿ-n and 2ⁿ⁺¹-n Mersenne prime exponents (verified to n≤130)
- `palindrome_identification.py`: exactly 3 non-W⁺ palindromes + 10 non-palindromes in the 14-neighborhood f_MDL catalog
- `weinberg_angle_arithmetic.py`: sin²θ_W = 3/13 ≈ 0.2308; Z₇ orbit arithmetic

---

## Compilation

```bash
cd papers/31_weinberg_angle
pdflatex weinberg_angle_paper.tex
bibtex weinberg_angle_paper
pdflatex weinberg_angle_paper.tex
pdflatex weinberg_angle_paper.tex
```

---

## Graduation status

### Python ✅ (2026-05-20)
| Script | Location |
|--------|----------|
| `double_mersenne_endpoint.py` | `scripts/` ✅ |
| `palindrome_identification.py` | `scripts/` ✅ |
| `weinberg_angle_arithmetic.py` | `scripts/` ✅ |

### Lean ⏳ (`ugp-lean` → `ugp-lean`)

| Module | Key theorems |
|--------|-------------|
| `GUTStructure.lean` §§10,12,13,18–21,23,24,27,37,45,49,50,63,78 | `weinberg_angle_closure`, palindrome counts, orbit-average |
| `EWChiralBridge.lean` | P22 parity bridge |
| `EWBosonStructure.lean` | EW c-staircase |
| `GTE/BraidAtlas.lean` | N_gen, N_fam |

**Open Lean:** import P22 `doublet_partner_is_left_chiral` → `weinberg_angle_unconditional`.

After Lean graduation: update Lean appendix commit SHAs from `ugp-lean` to `ugp-lean`.

---

*REPRODUCE.md — P31 — 2026-05-20*
