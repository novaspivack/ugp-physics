# REPRODUCE — The Canonical Braid Atlas v2.0

**Requirements (optional ML block):** Python 3.10+, scikit-learn, numpy, pandas, matplotlib.

## 0) Clone and paths

```bash
git clone https://github.com/novaspivack/ugp-physics.git
cd ugp-physics
```

Lean formalization (separate repository):

```bash
git clone https://github.com/novaspivack/ugp-lean.git
cd ugp-lean
```

## 1) Reproduce the ~91.65% in-sample R² (Voting Ensemble)

```bash
cd topology_lab/pillar2c_foundational_fortification
pip install scikit-learn numpy pandas matplotlib
python3 Advanced_Feature_Engineering.py
```

**Expected:** Voting Ensemble \(R^2 \approx 0.9165\) on the hardcoded 12-fermion set. See `PROVENANCE.md` for CV caveats at \(n=12\).

## 2) Rosetta Stone labs (optional)

```bash
cd topology_lab/pillar2a_rosetta_stone
python3 Rosetta_Stone_Lab.py
```

```bash
cd topology_lab/pillar2a_refinement
python3 Advanced_Rosetta_Stone_Lab.py
```

## 3) Compile this paper

From the `ugp-physics` root (adjust engine as needed):

```bash
cd papers/17_braid_atlas
latexmk -pdf -interaction=nonstopmode Braid_Atlas_v2_First_Principles.tex
```

## 4) Mirror-branch quantum number computation (GTE-P7, new in v3.0)

Runs the Braid Atlas computation for the mirror triple (a=1, b=73, c=2137; g=1)
and derives Q=0, color-singlet, spin-1/2 for GTE-P7 (dark matter candidate).

```bash
cd papers/02_GTE_spectrum
python3 mirror_branch_quantum_numbers.py
```

**Requirements:** Python 3.9+, `sympy` (`pip install sympy`)

**Expected output:**
```
All SM charges verified. ✓
...
RESULT: GTE-P7 QUANTUM NUMBERS
  Electric charge: Q = 0 (NEUTRAL)  ✓
  Color: SU(3) singlet (colorless)  ✓
  Spin: 1/2 (Dirac fermion)         ✓
  SM-neutral: YES
  Claim grade: [B] bridge
```

**Lean verification of arithmetic foundation:**

```bash
# Verify the 4 mirror-triple theorems (in ugp-lean):
lake build UgpLean.GTE.GeneralTheorems
```

Key identifiers (zero sorry, native_decide):
- `mirror_triple_residue`: gteRemainder 2137 73 = 20
- `mirror_prime_2137`: Nat.Prime 2137
- `mirror_quotient_q1`: gteQuotient 2137 73 = 29
- `mirror_triple_prime_lock`: 73 × 29 + 20 = 2137

---

## 5) Verify Lean modules (Theorem C-W, composites, charge derivation)

```bash
cd /path/to/ugp-lean
lake build UgpLean.BraidAtlas.ChargeTheorem \
           UgpLean.BraidAtlas.CompositeTriples \
           UgpLean.BraidAtlas.ChiralitySquaring \
           UgpLean.BraidAtlas.ChargeDerivation \
           UgpLean.BraidAtlas.CoxeterConductor \
           UgpLean.BraidAtlas.CoxeterConductorTowerLaw
```

**Expected:** `Build completed successfully` with zero errors and zero `sorry` in these modules.

Key identifiers:

- `sm_charge_leptons`, `anomaly_cancellation_forces_Nc_3` — `BraidAtlas.ChargeTheorem`
- `sm_winding_numbers_from_Nc`, `y_ql_unifies_vv_and_winding`, `alpha_d_value` — `BraidAtlas.ChargeDerivation`
- `p_rat_no_roots`, `p_rat_irreducible`, `e7_arithmetic_evidence`, `tower_obstruction` — `BraidAtlas.CoxeterConductorTowerLaw`
- `phi_120`, `three_not_dvd_32`, `e7_coxeter_not_dvd`, `e7_coxeter_conductor_obstruction` — `BraidAtlas.CoxeterConductor`
- Baryon triple lemmas — `BraidAtlas.CompositeTriples`
- `mirror_triple_residue`, `mirror_prime_2137`, `mirror_quotient_q1`, `mirror_triple_prime_lock` — `GTE.GeneralTheorems` (mirror-branch GTE-P7)

Full library (see companion formalization paper~\cite{SpivackUGPFormalization}):

```bash
lake build
```

## Notes

- Particle tuples for the ML scripts are embedded in `topology_lab/feature_engineering/Dynamic_Feature_Analysis.py` (see file for line range).
- GTE-to-braid mapping scripts: `papers/17_braid_atlas/scripts/braid_to_gte_mapper.py` and `papers/17_braid_atlas/scripts/test_all_particles.py` (verifies all 12 SM fermion mappings). Run from `papers/17_braid_atlas/scripts/`.
- The \(\Psi\) pipeline pseudocode is Appendix B of the PDF; research implementations may live outside the public tree; the published paper is self-contained for the theorem layer.
