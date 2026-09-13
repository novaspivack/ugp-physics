# P37 — Quantum Mechanics from Rule 110: Hilbert Space, Hamiltonian, and Born Rule

**Paper:** P37 in the UGP Physics series  
**Status:** Draft (2026-05-20)  
**Author:** Nova Spivack

## Summary

This paper applies 't Hooft's cellular automaton interpretation of quantum
mechanics to the GTE cellular automaton $f_{\rm MDL}$ on $\mathbb{Z}_7^5$
(the 16,807-state visible-sector ring encoding the SM generation structure),
establishing a coherent quantum mechanical framework for the GTE.

### Key results

1. **One-dimensional Hilbert space (CatA):** Exhaustive orbit decomposition
   of $f_{\rm MDL}$ on $\mathbb{Z}_7^5$ reveals a single cycle — the vacuum
   fixed point $(0,0,0,0,0)$ with $E=0$. The physical Hilbert space is
   $\mathcal{H}_{\rm phys} = \mathbb{C}|\text{vac}\rangle$.

2. **Information-loss regime (CatA):** $f_{\rm MDL}$ is a Chapter-7
   (information-loss) automaton: 98.71% GoE states, maximum tail length 7
   steps, universal vacuum attractor.

3. **Stability hierarchy (CatA):** Tail-length ordering
   $\ell(\text{gen}_1)=3 > \ell(\text{gen}_2)=2 > \ell(\text{gen}_3)=1$
   matches the SM generation stability ordering exactly.

4. **Eigenvalue-mass falsification (CatA):** Direct eigenvalue-to-mass
   correspondence fails on all formulations tested (>10,000% discrepancy
   for the lepton mass ratios).

5. **Two-Role Theorem (CatAD):** The 't Hooft cogwheel provides QM
   structure (Hilbert space, unitarity, Born rule); the GTE $N_{\rm eff}$
   cascade provides mass content (Yukawa-analog). Complementary,
   non-redundant contributions.

6. **SM gauge groups from winding classes (CatAD, CatAL components):**
   The 7 winding-equivalence classes of $\mathbb{Z}_7^5$ (2,401 states each)
   yield $G_{\rm SM} = SU(3)_c \times SU(2)_L \times U(1)_{\rm EM}$ via
   't Hooft's §9.3 information-equivalence mechanism. Two missing classes
   $\{W=1, W=5\}$ predict $SU(5)$ leptoquark mediators.

7. **Dark sector (CatAL):** $\mathbb{Z}_7^4$ dark ring has a 5-dimensional
   Hilbert space with stable $E=\pi$ doublet states, Lean-certified.

8. **Born rule (CatAD):** Structural derivation from information loss,
   with comparison to the independent UGP derivation.

## Files

| File | Description |
|------|-------------|
| `quantum_mechanics_paper.tex` | Main paper (LaTeX) |
| `quantum_mechanics_refs.bib` | Local bibliography entries for P31, P32 |
| `nova_zenodo_doi_placeholder.tex` | Zenodo DOI placeholder |
| `README.md` | This file |
| `REPRODUCE.md` | Reproduction instructions |
| `PROVENANCE.md` | Provenance and derivation record |

## Building

```bash
cd papers/37_quantum_mechanics
pdflatex quantum_mechanics_paper.tex
bibtex quantum_mechanics_paper
pdflatex quantum_mechanics_paper.tex
pdflatex quantum_mechanics_paper.tex
```

Requires: LaTeX distribution with standard packages (amsmath, booktabs,
tcolorbox, hyperref, cleveref, amsthm).

## Key open problems

1. **Continuum limit** (CatD): recovering continuous QFT from the discrete CA.
2. **Lean certification of gauge identification** (CatAD → CatAL): formal
   proof that Z₇ winding classes satisfy 't Hooft's §9.3 gauge-equivalence
   conditions.
3. **Multi-particle Hilbert space**: tensor-product structure for multiple CA rings.
4. **Quantitative tail-length mass formula**: relating tail lengths to
   generation mass ratios.
