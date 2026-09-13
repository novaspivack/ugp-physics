# Reproduce — Paper 24: The Arithmetic Uniqueness of the Standard Model

All paper-internal computational results reproduce from scratch in < 1 second:

```bash
cd papers/24_deeper_theory
python3 run_all.py
```

Requirements: Python 3.8+, `sympy`, `numpy`

```bash
pip install sympy numpy
```

## Individual scripts (paper-internal)

```bash
python3 01_asymptotic_sieve.py      # Asymptotic Sparsity: n=4..60 + analytic bound
python3 02_diophantine_analysis.py  # Near-integer solutions at n=10
python3 03_t6_root_hypothesis.py    # Positive Root Theorem: |Φ⁺| = SU(N)₁ factor count
python3 04_galois_orbits.py         # Galois stability of UGP layers in Q(ζ₁₂₀)
python3 05_wzw_structure.py         # WZW structure + T4 falsification
python3 06_synthesis.py             # The deeper law
python3 toda_masses.py              # ADE Toda mass spectra: Q(ζ₁₂₀) containment / E7 falsifier
python3 pslq_e8_exact.py            # E8 mass ratios: minimal polynomials + precision table
python3 wzw_dimensions.py           # WZW quantum dims: Q(ζ₁₂₀) iff (k+2)|120
python3 pslq_known_models.py        # PSLQ pipeline validation on 2D Ising / tricritical (pipeline sanity check)
```

> **Note (2026-05-12):** `toda_masses.py`, `pslq_e8_exact.py`, `wzw_dimensions.py`,
> and `pslq_known_models.py` are the canonical versions used to produce results cited in
> §Coxeter–Conductor theorem and the Q(ζ₁₂₀) algebraic filter evidence.

## Cross-referenced artefacts (in `papers/01_SM/canonical_run/`)

### Precision derivation programme (§9.8)

```bash
cd ../01_SM/canonical_run

# §9.5 / §9.6 (Charge derivation, extended RCC):
python3 comp_p23_SP1_rcc_extended_scan.py    # Extended RCC scan (11 new gauge groups)

# §9.7 (boundary of derivability):
python3 comp_p24_SP3_Nc_independence_audit.py  # N_c=3 independence audit

# Precision Derivation Programme (§9.8) — run in order:
python3 comp_p25_alpha_precision_floor.py             # 60-digit C_alg / delta_target / b1_req
python3 comp_p25_residual_structural_search.py        # null-disciplined search (NO_MATCH at depth ≤ 1)
python3 comp_p25_galois_protection_probe.py           # O4a Galois census (GALOIS_PROTECTION_SUPPORTED)
python3 comp_p25_o4b_sensitivity_probe.py             # O4b sensitivity (583 ppm one-loop = 244× R_real)
python3 comp_p25_o3_scale_probe.py                   # O3: matching scale Q ≈ m_e
python3 comp_p25_o4b_analytic_proof.py               # O4b 6-step analytic proof (ANALYTIC_PROOF_COMPLETE)
python3 comp_p25_o3_two_loop_coefficient.py          # O3 closure: (8/9)×α²/(2π²) (MATCH_WITHIN_PRECISION)
```

Each script writes a SHA-256-verified JSON certificate.

## Lean verification

```bash
cd ugp-lean
lake build UgpLean.Phase4.AsymptoticSparsity
lake build UgpLean.Phase4.PositiveRootTheorem
lake build UgpLean.BraidAtlas.ChiralitySquaring
lake build UgpLean.BraidAtlas.ChargeDerivation
lake build UgpLean.GaloisStructure.CyclotomicLayers
lake build UgpLean.GaloisStructure.MinimalCyclotomic
lake build UgpLean.MassRelations.VVMechanism
lake build UgpLean.MassRelations.VVAllCoefficientsFromNc
lake build UgpLean.PSC.RCCInfiniteFamilies
lake build UgpLean.MassRelations.NeutrinoFroggattNielsen
# All pass: zero errors, zero sorry, zero custom axioms
```

Or, equivalently, build the whole library:

```bash
cd ugp-lean
lake build
# Expected: zero sorry, zero custom axioms
```

## Expected output

All six paper-internal scripts match the pre-computed results in `results/`.
The sieve (`01`) uses an analytic cutoff at n≥13 and completes in < 0.2s.

The companion artefacts in `01_SM/canonical_run/` each write a JSON certificate
whose SHA-256 is recorded in their console output and in
`papers/01_SM/PROVENANCE.md`.
