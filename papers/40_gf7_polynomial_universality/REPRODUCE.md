# REPRODUCE — P40 — Algebraic Characterization of Rule 110 over GF(7)

**Paper:** P40 — "Algebraic Characterization of Rule 110 over GF(7) and Cook-Independent Turing Universality"  
**Date:** 2026-05-25  
**Author:** Nova Spivack

---

## Compiling the paper

```bash
cd papers/40_gf7_polynomial_universality
pdflatex gf7_polynomial_universality.tex
bibtex gf7_polynomial_universality
pdflatex gf7_polynomial_universality.tex
pdflatex gf7_polynomial_universality.tex
```

Requires: TeX Live 2024+ with `tcolorbox`, `amsmath`, `hyperref`, `cleveref`.

Expected output: `gf7_polynomial_universality.pdf`.

---

## Verifying Lean certifications

### rule110-lean (GF(7) polynomial + NAND gate)

```bash
cd /path/to/rule110-lean
lake build Rule110.AlgebraicUniversality
```

Key theorems (zero sorry except one named axiom):

| Theorem | Method |
|---------|--------|
| `rule110_z7_poly_rep` | `native_decide` — degree-3 multilinear GF(7) polynomial |
| `rule110_center1_is_nand` | `decide` — center cell active ⇒ NAND(L,R) |
| `rule110_z7_nand_identity` | `native_decide` |
| `rule110_algebraic_nand_bundle` | composition |
| `boolean_nand_complete` | 1 named axiom (Sheffer functional completeness) |
| `rule110_turing_universal_algebraic` | follows from axiom |

### ugp-lean (Φ_MDL Turing universality route)

```bash
cd /path/to/ugp-lean
lake build UgpLean.Universality.PhiMDLUniversality
```

| Theorem | Result |
|---------|--------|
| `phimdl_turing_universal` | Cook-independent Turing universality via GF(7) polynomial (zero sorry) |
| `rule110_z7_poly_rep` | cross-ref from PhiMDLUniversality |

### ugp-lean (cross-cited substrate theorems)

```bash
lake build UgpLean.Substrate.LorentzInvariance   # poincare_invariance_of_kg
```

---

## Numerical verification

No standalone Python scripts are required for the current PDF — all polynomial identities are Lean-certified by exhaustive `native_decide` / `decide`.

Sanity check (manual):

```python
# Rule 110 as GF(7) polynomial p(L,C,R) = C + R - C*R - L*C*R mod 7
for L in (0,1):
    for C in (0,1):
        for R in (0,1):
            p = (C + R - C*R - L*C*R) % 7
            # Compare to Rule 110 lookup table
            print(L, C, R, p)
```

---

*REPRODUCE.md — P40 — 2026-05-25*
