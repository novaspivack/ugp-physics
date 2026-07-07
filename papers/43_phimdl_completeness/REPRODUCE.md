# P43 — REPRODUCE

## Compilation

```bash
cd papers/43_phimdl_completeness
pdflatex phimdl_completeness_paper.tex
bibtex phimdl_completeness_paper
pdflatex phimdl_completeness_paper.tex
pdflatex phimdl_completeness_paper.tex
```

Expected output: `phimdl_completeness_paper.pdf`, ~28–32 pages, no errors.

## Lean verification

All theorems in Appendix A are in the `ugp-lean` canonical repository.

```bash
cd /path/to/ugp-lean
lake build
# Expected: zero sorry in the modules listed in Appendix A
```

Key modules:
- `UgpLean/Universality/CMCAContinuumLimit.lean`
- `UgpLean/Universality/NoClass4OuterTotalisticZ7.lean`
- `UgpLean/Universality/WindingCoinDecoupling.lean`
- `UgpLean/Universality/BeableWindingPartitionInstance.lean`
- `UgpLean/Universality/PhiMDLThermalState.lean`
- `UgpLean/Spacetime/QECStabilizer.lean`
- `UgpLean/Substrate/QECStabilizer.lean`
- `UgpLean/Substrate/TransputationStateSelector.lean`
- `UgpLean/Spacetime/StressEnergyTensor.lean`
- `UgpLean/Spacetime/GeodesicTheorem.lean`  ← now CatAL, zero custom axioms for timelike
- `UgpLean/Universality/BetaCoefficientIdentity.lean`
- `UgpLean/Universality/FrobeniusPrimeIdentity.lean`
- `UgpLean/Universality/LorentzInvariance.lean`
- `UgpLean/Universality/PhiMDLUniversality.lean`

## Key numerical scripts

All computation scripts are in `papers/43_phimdl_completeness/scripts/`.

| Computation | Script | Key result |
|---|---|---|
| T_μν tensor, kink mass | `papers/38_geocomp_gte/scripts/phimdl_tmunu_full.py` | M_kink = 290.10 MeV |
| Hierarchy scan | `papers/43_phimdl_completeness/scripts/gte_g_hierarchy_scan.py` | 21^10 × 7^7 / 2 at 0.040% |
| PSC λ stability | `papers/43_phimdl_completeness/scripts/psc_lambda_stability.py` | Λ upper bound |
| Graviton Fock space | `papers/43_phimdl_completeness/scripts/phimdl_graviton_fock.py` | h₀₀, α_g, S_BH(M☉), τ_grav |
| Wald entropy derivation | `papers/43_phimdl_completeness/scripts/epic076_wald_entropy.py` | Wald factor chain = 1/4 |
| Planck-scale EFT | `papers/43_phimdl_completeness/scripts/epic076_planck_eft.py` | α_g running, M_BH_min, T_H^max |
| Non-perturbative QGR | `papers/43_phimdl_completeness/scripts/epic076_npg_pathint_qbh.py` | ε₀=1, α_g=1, S(M_Pl)=4π |

### Running the hierarchy scan

```bash
cd papers/43_phimdl_completeness
python3 scripts/gte_g_hierarchy_scan.py
```

Pre-registered search over forms $7^a \cdot 3^b \cdot 21^c / K$.
Expected output: unique hit $21^{10} \cdot 7^7/2$ at 0.040% precision.

### Running graviton Fock computations

```bash
python3 scripts/phimdl_graviton_fock.py
```
Expected: h₀₀(1 fm) = 1.54×10⁻³⁹; α_g = 5.65×10⁻⁴⁰; r_S(M☉) = 2956.5 m; S_BH(M☉) = 1.050×10⁷⁷.

### Running Wald entropy derivation

```bash
python3 scripts/epic076_wald_entropy.py
```
Expected: Wald factor chain = 0.250000 = 1/4; S_BH(M☉) = 1.048×10⁷⁷.

### Running Planck-scale EFT

```bash
python3 scripts/epic076_planck_eft.py
```
Expected: M_Pl^GTE = 1.2204×10¹⁹ GeV (0.040% from PDG); M_BH_min = 8.630×10²¹ MeV; T_H^max = 6.867×10²⁰ MeV.

### Running non-perturbative QGR

```bash
python3 scripts/epic076_npg_pathint_qbh.py
```
Expected: ε₀(M_Pl) = 1.000000; α_g(M_Pl) = 1.0; S_BH(M_Pl) = 4π ≈ 12.566; T_H^max = 6.867×10²⁰ MeV.

## Cosmological constant formula (P01)

Formula: Λ = (ln2/π) · log₂(2000/3) · H₀²/c²  
Using H₀ = 67.36 km/s/Mpc (Planck 2018): Λ = 1.097×10⁻⁵² m⁻²  
PDG/Planck: Λ_Planck = 1.088×10⁻⁵² m⁻² (0.31σ)  
See P01 (`papers/01_SM/standard_model_from_ugp.tex`, §Extensions).
