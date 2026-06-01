# Reproducing P47 Results

This paper assembles cosmological predictions of the GTE/Φ_MDL framework. The
numerical results are reproduced by the scripts below; the central algebraic steps
are machine-checked in the canonical `ugp-lean` library.

## Scripts

| Script | Produces |
|---|---|
| `papers/45_three_tape_cmca/scripts/cc_temporal_voxel_formula.py` | CC coefficient 9/112 and Ω_Λ = 3π/14 = 0.6732 |
| `papers/45_three_tape_cmca/scripts/sr_ratio_measurement.py` | Proper-time rate τ measurement |
| `papers/18_koide_cyclotomic/scripts/gte_cp_phase_final.py` | δ_CP = π/2 − 3/8 = 68.51° |
| `papers/18_koide_cyclotomic/scripts/jarlskog_from_koide.py` | Jarlskog invariant J = 3.02×10⁻⁵ |
| `papers/18_koide_cyclotomic/scripts/ckm_a_parameter_gte.py` | Wolfenstein A = sin(π/3) |
| `papers/21_neutrino_masses/scripts/neutrino_mass_prediction.py` | m_ν₁ = 0.679 meV, Σm_ν = 59.4 meV |
| `papers/21_neutrino_masses/scripts/gte_leptogenesis.py` | Leptogenesis efficiency K₁ = 15.93 |

Run any script with `python3 <path>`; results are written to the adjacent
`*_results.json` file.

## EPIC_083 additions (2026-05-31): CC ratio formula and N_gen=3 uniqueness

The ratio between the two structural Ω_Λ routes is now derived in closed GTE-atom form
(CatAD; G02 session, all results reproducible from formulas in §cc-range):

```python
import math

# GTE atoms
D, N_fam, N_gen, Z7 = 4, 5, 3, 7

# Route 1 (PSC epoch, §cc-dres)
Omega_PSC  = (math.log(2) / (N_gen * math.pi)) * math.log2(D**2 * N_fam**3 / N_gen)
# Route 2 (holographic mode count, §cc-voxel)
Omega_holo = (N_gen / Z7) * (math.pi / 2)

ratio = Omega_PSC / Omega_holo
# Closed form: 14 * ln(2000/3) / (9 * pi^2)
ratio_formula = 2 * Z7 * math.log(D**2 * N_fam**3 / N_gen) / (N_gen**2 * math.pi**2)

print(f"Omega_PSC  = {Omega_PSC:.6f}")    # 0.689914
print(f"Omega_holo = {Omega_holo:.6f}")   # 0.673198
print(f"Ratio      = {ratio:.6f}")        # 1.024831
print(f"Formula    = {ratio_formula:.6f}") # 1.024831 (should match)
print(f"2000/3     = D^2 * N_fam^3 / N_gen = {D**2 * N_fam**3} / {N_gen}")  # 2000/3
```

**N_gen=3 uniqueness:** For all integers N ≠ 3, at least one route deviates from
Planck 2018 (Ω_Λ = 0.6889 ± 0.0056) by more than 5σ. At N=3 the PSC route gives
+0.18σ and the holographic route gives −2.80σ. The continuous minimum of the route
spread function lies at N=3.034; the nearest integer is N=3 (PSC-selected independently
by the Two-Layer PSC Theorem).

```python
# Verify N_gen=3 uniqueness
Planck, sigma = 0.6889, 0.0056
for N in range(1, 8):
    op = (math.log(2) / (N * math.pi)) * math.log2(D**2 * N_fam**3 / N)
    oh = (N / Z7) * (math.pi / 2)
    both_ok = abs(op - Planck) < 5*sigma and abs(oh - Planck) < 5*sigma
    print(f"N={N}: PSC={op:.4f} ({(op-Planck)/sigma:+.1f}s) "
          f"holo={oh:.4f} ({(oh-Planck)/sigma:+.1f}s) both<5s: {both_ok}")
# Only N=3 prints True
```

---

## Lean build

The central derivations are certified in `ugp-lean`. Relevant modules:

- `UgpLean/Gravity/PSCEpochSelection.lean` — Ω_Λ = 0.6899 (D_res route)
- `UgpLean/Gravity/TemporalVoxelCC.lean` — Ω_Λ = 3π/14, holographic mode count, NRT
- `UgpLean/Gravity/EtherProperTimeRate.lean` — τ = 3/7 from Rule-110 ether
- `UgpLean/Gravity/CMBSpectralTilt.lean` — n_s = 1 − ln2/(2π²) (14 theorems)
- `UgpLean/ContinuumLimit/GorardRationalFormula.lean` — κ_SD = 10/13, Gorard chain
- `UgpLean/Gravity/GorardRicciFlatVacuum.lean` — C_Gorard = 3/32, superselection
- `UgpLean/Gravity/PMDLGravityTheorems.lean` — kink mass, Hawking emission, V_max
- `UgpLean/Gravity/NRTVacuumEnergy.lean` — Z₇ vacuum energy mass independence
- `UgpLean/MassRelations/CKMCPPhase.lean` — δ_CP, Jarlskog, A parameter

New in this version (2026-06-01):
- `UgpLean/Gravity/Z7AnomalyFree.lean` — Z₇ global scalar symmetry anomaly-free (4 theorems, zero sorry): `z7_global_scalar_anomaly_free`, `z7_shift_measure_preserving`, `z7_jacobian_eq_one`, `z7_vacuum_sectors_equiprobable`
- `UgpLean/ContinuumLimit/GorardVacuumW1Bridge.lean` — W₁=1 for vacuum measures, κ=0 ∀ adjacent edges (zero sorry): `gorard_vacuum_oric_zero_scoped`, `vacuum_w1_eq_one`, `W1_ge_of_lipschitz`
- `UgpLean/ContinuumLimit/WassersteinDistance.lean` — W₁ Wasserstein distance (fully proved, zero sorry): `W1_nonneg`, `W1_triangle`, `W1_eq_zero_iff`, `W1_attained`, `couplingCostSet_isCompact`

Build with `lake build` from the `ugp-lean` repository root; a clean build exits 0
with zero `sorry` on the cited theorems.

## Additional Lean certificates

| Theorem | Module | Commit | Statement |
|---|---|---|---|
| `incompleteness_implies_nonzero_omega_lambda` | `UgpLean/Gravity/PSCEpochSelection.lean` | `63c015b` | PSC incompleteness → D_res>0 → Ω_Λ>0 |
| `psc_enumeration_forces_ngen_3` | `UgpLean/TE22/ScanCertificate.lean` | `63c015b` | All 34,560 PSC survivors have N_gen=3 |
