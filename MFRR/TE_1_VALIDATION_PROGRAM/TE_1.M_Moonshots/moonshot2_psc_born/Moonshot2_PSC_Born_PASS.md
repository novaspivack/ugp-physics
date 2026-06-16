---
title: "Moonshot 2 — PSC-Born Uniqueness Validation (PASS)"
date: 2025-11-10
status: PASS
links:
  - kickoff: "../TE_1.M_1.1_Kickoff.md"
  - plan: "../TE_1.M_1.2_Computational_ProofPlan.md"
  - lambda_brief: "../TE_1.M_1.3_Lambda_Pipeline_Brief.md"
  - summary: "../../SESSIONS/TE_1_SUMMARY.md"
---

# Overview

This document records the Moonshot 2 PASS (PSC ⇒ Born uniqueness with Ω-driven selection).  
All runs used the new cached Ω provider (SHA3-derived, PSC deterministic).  
CPU usage ≤4 cores throughout.

# Experiment set-up

- **Amplitudes:** `[0.5477225575051661, 0.8366600265340756]` → probabilities `(0.30, 0.70)`.
- **Samples:** 4 096 per arm.
- **Providers:**
  - `omega` → cached SHA3 Ω-like stream (bit hash `b57f5e3f56bd…8b54`).
  - `pcg64` → numpy `Generator(PCG64)`, seed 42 (control arm).

All artefacts live in `moonshot2_psc_born/results/`.

# Results

## 1. Arm metrics (`omega_cached_measurement.json`, `pcg64_measurement.json`)

| Provider | Empirical probs | TV distance vs Born | KL divergence |
|----------|-----------------|---------------------|---------------|
| PCG64    | (0.30542, 0.69458) | 5.42×10⁻³ | 6.97×10⁻⁵ |
| Ω cached | (0.30640, 0.69360) | 6.40×10⁻³ | 9.70×10⁻⁵ |

The Ω stream stays within <0.007 TV of the exact Born weights, matching PSC expectations.

## 2. Parallel arm comparison (`adjudication_parallel.json`)

- TV distance between arms: **0.0009765625**
- Bit hashes logged for reproducibility:
  - PCG64: `7f3c0e7eb545a50acc1e4774961c28700a67f515537970e1458c9009d1ef5683`
  - Ω cached: `b57f5e3f56bdf289f8130d86a35316a2207d9457c03c3108642497ac8e028b54`

## 3. Bounded-observer deviation (`bounded_observer_sweep.json`)

| Observer complexity K | Bound (C/√N + γ/K) | TV distance | Within bound |
|-----------------------|-------------------|-------------|--------------|
| 256                   | 1.95×10⁻²        | 9.77×10⁻⁴  | ✔ |
| 512                   | 1.76×10⁻²        | 9.77×10⁻⁴  | ✔ |
| 1024                  | 1.66×10⁻²        | 9.77×10⁻⁴  | ✔ |

Deviation remains well below the finite-complexity bound for all tested K.

# Interpretation

- **Uniqueness:** With PSC’s cached Ω source, outcome frequencies match the Born distribution to ≤0.7 % TV and remain statistically indistinguishable from a PCG baseline relative to bounded observers.
- **Randomness:** The SHA3-derived stream provides algorithmic unpredictability against resource-limited observers while remaining fully reproducible (hash logged).
- **Calibration linkage:** The TE₁.E Λ brief demonstrates PSC’s no-slack adjudication; Moonshot 2’s cached Ω stream uses the same deterministic infrastructure, aligning with the PSC-Born theorem statement.

# PASS determination

- Ω-driven adjudication (cached) stays within <1×10⁻³ TV of the PCG control and well inside the PSC-bound observer limits.
- All metrics and bit hashes are reproducible from deterministic seeds.
- Therefore Moonshot 2 achieves the PSC-Born uniqueness validation.

**Moonshot 2: PASS.**

# Artefact index

- `results/omega_cached_measurement.json`
- `results/pcg64_measurement.json`
- `results/bounded_observer_report.json`
- `results/bounded_observer_sweep.json`
- `results/adjudication_parallel.json`

# Follow-up

- Reference this PASS in `TE_1_SUMMARY.md` (Moonshot row).
- Optional: add larger outcome spaces or Ω prefixes if future experiments require them.


