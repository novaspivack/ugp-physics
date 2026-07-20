# Reproduction Guide — P52: The PSL(2,7) Algebraic Structure of the GTE Framework

## LaTeX compilation

```bash
cd papers/52_psl27_unification
pdflatex -interaction=nonstopmode psl27_unification.tex
bibtex psl27_unification
pdflatex -interaction=nonstopmode psl27_unification.tex
pdflatex -interaction=nonstopmode psl27_unification.tex
```

Expected output: PDF with approximately 16 pages, zero undefined references.

## Lean verification

All CatAL theorems can be verified by building the `ugp-lean-exp` development
repository (pending graduation to canonical `ugp-lean`):

```bash
cd /path/to/ugp-lean-exp
lake build UgpLean
```

A clean build (no errors, no `sorry` warnings) confirms all certifications in
this paper.

### Key theorem locations

| Theorem | Module path | Statement |
|---------|-------------|-----------|
| `f21_is_borel_psl27` | `UgpLean/Polynomial/PSL27Unification.lean` | F₂₁ = Stab(∞) in PSL(2,7), order 21 |
| `pgl27_generated_by_singer_and_borel` | `UgpLean/Polynomial/PSL27Unification.lean` | ⟨Fibonacci–Möbius, F₂₁⟩ = PGL(2,7), order 336 |
| `psl27_is_aut_fano` | `UgpLean/Polynomial/PSL27Unification.lean` | \|PSL(2,7)\| = 168, unique simple group |
| `f21_regular_on_fano_flags` | `UgpLean/Algebra/FanoRegularAction.lean` | F₂₁ simply transitive on 21 Fano flags |
| `eisenstein_a4_from_inert_2` | `UgpLean/Algebra/EisensteinFunctor.lean` | A₄ = V₄ ⋊ ℤ₃ from ℤ[ω]/(2) |
| `gte_manifest_flavor_is_s3_in_a4` | `UgpLean/Algebra/FlavorGroupStructure.lean` | S₃ ≤ A₄ from manifest GTE generators |
| `klein_quartic_genus_eq_n_gen` | `UgpLean/Cosmology/CCBracketHurwitz.lean` | genus(Klein quartic) = N_gen = 3 |

### Supporting modules imported by P52 theorems

These modules must also build cleanly:
- `UgpLean/Polynomial/DynamicalZeta.lean` — provides `moebiusP1`, `P1GF7` (used by PSL27Unification)
- `UgpLean/Cosmology/CCBracketHurwitz.lean` — also contains `cc_hurwitz_arithmetic_identity`,
  `fgci_hurwitz_triple`, `hurwitz_orbifold_gauss_bonnet` (supporting orbifold arithmetic)

## UgpLean module imports

The following lines appear in `ugp-lean-exp/UgpLean.lean`, confirming the
modules are registered:

```
import UgpLean.Polynomial.PSL27Unification
import UgpLean.Algebra.FanoRegularAction
import UgpLean.Algebra.EisensteinFunctor
import UgpLean.Algebra.FlavorGroupStructure
```

`CCBracketHurwitz` is imported via `UgpLean.Cosmology.CCBracketHurwitz` (part of the Cosmology directory).

## No computational scripts for this paper

All quantitative results in this paper follow from pure group-theoretic
calculations verified by Lean's `native_decide` and `norm_num` tactics.
No separate Python scripts are required for reproduction.
