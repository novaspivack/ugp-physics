# REPRODUCE — P42: The Φ_MDL Field

**Paper:** The Φ_MDL Field: Quantum Structure, Born Rule, and Continuum Completion
of the Chiral Minkowski CA  
**Author:** Nova Spivack  
**Series:** UGP Physics P42

---

## Dependencies

- Python 3.10+: `numpy`, `scipy`
- LaTeX: `pdflatex`, `bibtex`
- Lean 4 (optional): `ugp-lean` repository, `lake build`

---

## Scripts

All computation scripts are in `scripts/`. Each produces a JSON results file.

### `scripts/phimdl_3d_domain_wall.py`

Computes domain wall tension, 3+1D Z₇ superselection, Born rule sector weights,
and SR time dilation for moving domain walls.

```bash
cd papers/42_phimdl_field
python3 scripts/phimdl_3d_domain_wall.py
# → scripts/phimdl_3d_domain_wall_results.json
```

**Key outputs:** σ = 7450.31 MeV/fm², SR time dilation max error < 2×10⁻¹⁶,
Z₇ topological charge = sector label (all 7 sectors).

---

### `scripts/phimdl_vortex_3d.py`

Computes the domain-wall junction tension in 3+1D using the product ansatz
φ(x,y) = kink(x) + kink(y) on a 256×256 grid.

```bash
cd papers/42_phimdl_field
python3 scripts/phimdl_vortex_3d.py
# → scripts/phimdl_vortex_3d_results.json
```

**Key outputs:** λ_dim = −16/49 (analytically exact, confirmed numerically to
convergence error < 10⁻¹⁰); λ = −1654.77 MeV/fm (attractive);
|λ/σ| = 2.000 (wall thickness ratio).

---

### `scripts/cmca_algebraic_descent.py`

Verifies the explicit descent map from the R110 Cook A-glider to the Φ_MDL BPS kink
at lattice resolution M = 7.

```bash
cd papers/42_phimdl_field
python3 scripts/cmca_algebraic_descent.py
# → scripts/cmca_algebraic_descent_results.json
```

**Key outputs:** RMSD = 5.34% ≤ ε₀(7) = 6.71% (Nyquist bound); Pearson r = 0.994;
winding number Q = 1/7 (exact).

---

## Lean 4 Certification

```bash
cd ugp-lean
lake build UgpLean.Universality.PhiMDLThermalState
lake build UgpLean.Universality.DualFrameBornRule
lake build UgpLean.Substrate.TransputationStateSelector
lake build UgpLean.Framework.CMCAContinuumLimit
lake build UgpLean.Universality.LorentzInvariance
lake build UgpLean.Universality.BeableWindingPartitionInstance
lake build UgpLean.Spacetime.LiftingTheorem
lake build UgpLean.Universality.AlgebraicDescentTheorem
lake build UgpLean.Substrate.WindingCoinDecoupling
```

Expected result: all modules build with zero sorry (see Appendix A of paper).

---

## Build Paper

```bash
cd papers/42_phimdl_field
pdflatex phimdl_field_paper.tex
bibtex phimdl_field_paper
pdflatex phimdl_field_paper.tex
pdflatex phimdl_field_paper.tex
```

---

## Previously graduated scripts (not in this directory)

The following scripts are in other paper directories but produce data cited here:

- `papers/41_three_layer_chiral_minkowski_ca/scripts/phiborn1_kg_amplitude_probability.py` — Position Born density normalization
- `phiborn2_kink_overlap_born.py` — Dual-frame Born rule for overlapping kinks
- `phiborn3_measurement_collapse.py` — [D]-collapse Monte Carlo (500k trials)
