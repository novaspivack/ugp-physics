# P44 — Numerical Verification Scripts

Scripts in this directory verify the numerical results in P44:
"Quantum Gravity in the GTE/Φ_MDL Framework: Functional Completeness"

All scripts are graduated from `research-sandbox/epic_078/` after paper completion.

## Script inventory

| Script | What it verifies | Key output |
|---|---|---|
| `hawking_radiation_phimdl.py` | T_H = M_Pl²/(8πM_BH) unchanged by m_φ; M_crit = M_Pl²/(8πm_τ) | M_crit = 3.34×10³⁹ MeV |
| `greybody_factor_phimdl.py` | Greybody suppression for massive Φ_MDL; thermal vs exponential regimes | Greybody table vs M_BH/M_crit |
| `uv_finiteness_curved_background.py` | DeWitt-Schwinger Type 1-4 classification; R² magnitudes at ξ=0 | C_i ≈ 41.76 |
| `rt_wald_extension_proof.py` | RT formula proof steps: T₂→T₃ normalization; log7 cancellation verification | a² = 4l_Pl² log(7) |
| `flrw_gte_bounce.py` | GTE Friedmann correction f_C(x); bounce at ρ_Pl; reheating temperature | T_reh = 6.49×10⁸ GeV |
| `mdl_initial_state_scoring.py` | MDL K-score comparison for all PSC-admissible FLRW configs | K_min = log₂(3) at k=0, Φ₀=0, Φ̇₀=M_Pl |
| `cyclotomic_z7_analysis.py` | Galois group Gal(Q(ζ₇)/Q) ≅ Z₂×Z₃; CPT = σ₆; generation orbits | Galois structure tables |
| `norfleet_tools_test.py` | Bakry-Émery κ_SD=10/13; Ihara-Bass ρ(B)=2.29; D_CF=4.018 with χ=5λ | Norfleet tool inventory |
| `bianchi_extended_test.py` | Extended Bianchi identity k=3..10 in Rule 110 CA; max|∑κ|<10⁻¹⁴ | Mean=0 to machine precision |
| `bakry_emery_saturation_check.py` | κ_SD=10/13 (exact by construction); W=8.80×10⁻⁵; Bakry-Émery floor saturation | κ_SD=0.7692, W=8.80×10⁻⁵ |

## Graduation status

All scripts graduated from `research-sandbox/epic_078/` on 2026-05-29.
Output artifacts write to `papers/44_quantum_gravity/data/`.

## Quick verification of Ω_Λ formula

```python
import numpy as np
L_model = np.log2(2000/3)          # gauge-orbit information content
omega = np.log(2) / (3 * np.pi) * L_model
print(f"Omega_Lambda = {omega:.4f}")  # Expected: 0.6899
print(f"Planck 2018:   0.6850 +/- 0.0070")
print(f"Deviation:     {abs(omega - 0.685)/0.007:.2f} sigma")  # Expected: 0.70
```
