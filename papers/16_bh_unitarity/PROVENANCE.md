# Data Provenance

**Paper:** Black Hole Unitarity via Reflexive Unitarity and Stinespring Dilation:
A GKSL Model in a JT-like PSC Universe

---

## Primary Data File

```
MFRR/TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/results/phase2_3_final/final_results.json
```

SHA-256: `bf2b079c9f3d2850434430356e9f4b1d49b448e6154c1cf808d348a730159b36`

Verify integrity:

```bash
shasum -a 256 MFRR/TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/results/phase2_3_final/final_results.json
```

---

## Model Parameters

| Parameter | Value |
|---|---|
| `n_modes` | 3 |
| `n_levels_per_mode` | 2 |
| `T_H` (Hawking temperature) | 0.003979 |
| `coupling` (γ₀) | 0.01 |
| `total_dim` (dim H) | 8 |
| `dim(H_E)` (environment) | 7 |
| Mode frequencies ω_n | (n + ½) π T_H, n = 0, 1, 2 |

The environment dimension satisfies dim(H_E) = 1 + N_Lindblad = 1 + 2×3 = 7,
where the factor of 2 counts one emission and one absorption operator per mode.

---

## Verified Claims

| Claim | Value | Source |
|---|---|---|
| Steady-state fidelity with thermal state (F_th) | 0.9999192951 | `final_results.json` → `steady_state.fidelity_with_thermal` |
| Stinespring fidelity (minimum over test states) | F ≥ 1 − 10⁻⁸ | `final_results.json` → `stinespring.F_min` = 1.0; TE2.4 final report |
| dim(H_E) | 7 | Analytic (1 + 6 Lindblad operators) |
| Choi trace preservation error | ≤ 10⁻¹⁰ | GKSL CPTP check in `te2_4_gksl_constructor.py` |
| Detailed balance error | 0.00% | `te2_4_gksl_constructor.py` detailed balance check |
| Steady-state von Neumann entropy | 0.4945 | `final_results.json` → `steady_state.entropy` |
| Entropy ratio vs. ideal thermal | 97.2% | `final_results.json` → `page_curve.ratio` |
| Steady-state purity | 0.7142 | `final_results.json` → `steady_state.purity` |
| Occupation numbers ⟨n₀, n₁, n₂⟩ | [0.1640, 0.0077, 0.0003] | `final_results.json` → `steady_state.occupation_numbers` |

---

## Source Code

```
MFRR/TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/src/
  te2_4_hilbert_space.py       — Hilbert space and density matrix utilities
  te2_4_gksl_constructor.py    — GKSL master equation; Lindblad operators; CPTP check
  te2_4_stinespring.py         — Stinespring dilation; Kraus operators; fidelity check
  te2_4_jt_toy_model.py        — Top-level driver; produces final_results.json
```

A thin wrapper for reproducing the Stinespring analysis is provided at:

```
bh_unitarity/run_stinespring_analysis.py
```

See `bh_unitarity/REPRODUCE.md` for step-by-step instructions.

---

## Caveats

1. **Toy model only.** The Hilbert space is a finite-dimensional truncated Fock space
   (d = 2 levels per mode). Results are rigorous within this truncation but do not
   constitute a proof in the full infinite-dimensional setting.

2. **JT-like, not full JT gravity.** The mode structure and Hamiltonian are inspired
   by 1+1D JT gravity, but the model is not a first-principles derivation from the
   JT path integral. The Schwarzian mode and exact bulk-boundary correspondence of
   JT gravity are not implemented.

3. **Not real 3+1D gravity.** The results apply to the 1+1D toy model; extension to
   four-dimensional quantum gravity is an explicit open problem.

4. **PT⁻¹ is interpretive, not directly measured.** The canonical reverse operator
   PT⁻¹ is proposed as the physical mechanism implementing information recovery.
   It is not derived from a first-principles Hilbert-space construction in this work,
   and it is not directly observed or measured in the computation. Its role is
   conceptual and interpretive.

5. **Stinespring fidelity is a numerical check, not a formal proof.** The fidelity
   F ≥ 1 − 10⁻⁸ is a numerical verification on three test states (vacuum, thermal,
   Fock |1,0,0⟩) at a single time step dt = 0.01. The Stinespring theorem itself is
   a mathematical theorem that holds exactly; the numerical value confirms the
   implementation is correct to that precision.

---

## Canonical Computational Results

### PT⁻¹ Circuit — Open-System (GKSL) Model

| Artifact | Script | SHA-256 |
|----------|--------|---------|
| `results/pt_inverse_circuit/final_results.json` | `te2_4_pt_inverse_circuit.py` | `882cd67a272ea5339f9de83c5f42a89f2d5d69b257aa13b64c90be5eb11f6dd4` |

**Configuration:** n_modes=3, d_levels=2, T_H=0.003979, coupling=0.01, 50,000 thermalization steps, dt=0.01  
**Key results:** F(PT⁻¹(ρ_partial), |vacuum⟩) = 0.9967; purity_recovered=0.993; entropy_recovered=0.022 nats (ideal: 0)

### Full Page Curve — Closed Unitary Model (CANONICAL RESULT)

| Artifact | Script | SHA-256 |
|----------|--------|---------|
| `results/page_curve_unitary/results_4modes_full.json` | `te2_4_page_curve_unitary.py` | `7f132bb18bf09a8955003931804d2627aff1984fd0c75f9f17a94ce334d23ba9` |
| `results/page_curve_unitary/results_4modes_hi_res.json` | same | `d28a9fbfe9420465940f2da2ae5586265bf11215be85319304e755df0408c970` |

**Configuration:** n=4 qubit BH (|+⟩^4, pure), n=4 qubit radiation (|0⟩^4), partial-SWAP unitaries, 20 steps/mode  
**Key results:**
- S_BH peak = 0.2458 nats; S_BH final = 0.000000 nats (full Page curve turnover)
- Purity_total = 1.000000 throughout (exact unitary conservation)
- S_BH = S_rad at all times (pure total state)
- F(PT⁻¹(ρ_evap), |+⟩^4) = 1.000000 (exact recovery)

**Reproduce:**
```bash
cd MFRR/TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/src
python3 te2_4_page_curve_unitary.py
# Canonical result: results_4modes_full.json, SHA-256 7f132bb1...
```

### Purified Thermal BH Page Curve — Closed Unitary Model (CANONICAL RESULT)

| Artifact | Script | SHA-256 |
|----------|--------|---------|
| `results/page_curve_thermal/results_3modes_thermal.json` | `te2_4_page_curve_thermal.py` | `e9ac80b01b46c7423bba8dd21ee77c950774314388f29b25bf7f49bcc9203dc5` |
| `results/page_curve_thermal/results_4modes_thermal.json` | `te2_4_page_curve_thermal.py` | `3cbd71f277e39fb4306e9fc58f99f8165b625aaf6afe6c7af558a945b5d196a5` |

**Configuration (nq=3):** n=3 qubits BH, n=3 qubit reference R (|Φ+⟩_BH,R purifying thermal BH), n=3 qubit radiation (|0⟩^3), partial-SWAP unitaries, 20 steps/mode  
**Configuration (nq=4):** Same with n=4; total dim = 4096 (reference, ~9 min)  
**Key results (both nq):**
- S_BH starts at ln(2^nq) nats (thermal), falls monotonically to 0 after full evaporation
- S_R = ln(2^nq) throughout (reference system untouched); S_rad → ln(2^nq) (all thermal entropy in radiation)
- Page crossing at n/2 modes as predicted by Page (1993); purity = 1.000000 throughout (total state exactly pure)
- F(PT⁻¹ restores |Φ+⟩_BH,R) = 1.000000 (exact recovery of BH–reference entanglement)

**Physical interpretation:** The reference system R = BH interior reference, matching island formula setup. PT⁻¹ = U†_evap restores the thermal BH–interior entanglement exactly.

**Reproduce:**
```bash
cd MFRR/TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/src
python3 te2_4_page_curve_thermal.py
# Canonical result: results/page_curve_thermal/results_3modes_thermal.json
```

---

### Lean Formalization Sources (Paper §Appendix D)

| Theorem | Library | Zenodo | Lean name |
|---------|---------|--------|-----------|
| BH record consistency | nems-lean | 10.5281/zenodo.19429792 | `BlackHoles.record_consistency_abstract` |
| No hypercomputing from BH | nems-lean | 10.5281/zenodo.19429792 | `BlackHoles.no_hypercomputing_from_bh` |

### Exploratory Runs (not canonical)

Prefixed `explore_*` in results directories; not cited in paper. See run log for details.
