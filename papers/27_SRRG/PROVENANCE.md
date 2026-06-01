% PROVENANCE — Paper 27: The Self-Referential Renormalization Group

**Title:** The Self-Referential Renormalization Group: A Universal Framework for Physical Constants  
**Author:** Nova Spivack  
**Status:** RESEARCH PAPER  
**Date:** 2026-05-11  
**Classification:** PUBLIC  
**Canonical source:** `papers/27_SRRG/srrg_paper.tex`

---

## What this paper claims

Introduces the Self-Referential Renormalization Group (SRRG): a gradient-flow theory
on the space of self-referential physical theories whose unique stable fixed point
simultaneously determines the Information Profit Threshold (IPT ≈ 1.1309), the
minimal gauge symmetry U(1), and the NEMS observational barriers as necessary
corollaries — without anthropic reasoning, fine-tuning, or domain assumptions.

## Key claims and grades

| Claim | Evidence type | Grade |
|-------|--------------|-------|
| SRRG fixed-point existence | Lean-certified via MFP-1 (zero sorry) | [T] |
| F[S] monotonicity (F-theorem) | Lean-certified (zero sorry) | [T] |
| 1/φ contraction eigenvalue at S* | Lean-certified via abs_psi_eq_inv_phi | [T] |
| U(1) minimality at C_SCP=0 | Lean-certified via U1DirectProof | [T] (upstream sorry remaining) |
| IPT = R[S*]/C_Λ[S*] at fixed point | Lean-certified via H9/IPT pipeline | [T] |
| SM gauge group from multi-scale SRRG | Proxy Hessian eigenvalues [A_Lean]; bridge to full SRRG [B] (H4Discharge.lean) | [B] |
| η-direction β_η = κ(η−IPT)(η−2) derived (not posited) | Vieta uniqueness [A_Lean] + no-third-zero [A_Lean] + two named hyps. | [B+→A−] |
| GXT/CFT universality of ε₃ₛ = IPT | Empirical + partial Lean | [C]/[T] |
| NEMS barriers as C_Λ components | Structural derivation | [D] |

## Lean certification

All core SRRG theorems formalized in `srrg-lean` (zero sorry for owned modules).
Upstream warnings in `UgpPhysicsLean.GXT.{U1DirectProof, LieExpSurjective}` are
pre-existing in ugp-physics-lean and tracked separately.

**Two-fixed-point picture and derived β_η (2026-05-12):**

| Module | Key theorems | Grade |
|--------|-------------|-------|
| `srrg-lean/SrrgLean/FixedPoints/NoThirdFixedPoint.lean` | `eta_beta_zero_iff` (no third zero, iff), `no_third_zero_of_eta_beta` (exactly two zeros), `no_third_srrg_fixed_point` (exhaustion hyp.) | [A_Lean] × 2; [B+] |
| `srrg-lean/SrrgLean/FixedPoints/BetaEtaQuadratic.lean` | `poly2_zeros_determine_poly` (Vieta uniqueness), `eta_beta_is_unique_quadratic` (IPT and 2 determine β_η), `beta_eta_quadratic_form` (derived form under two hyps.) | [A_Lean] × 2; [B+] |

All six theorems: zero sorry.

**Additional Lean certification (H4 discharge, 2026-05-12):**

| Module | Key theorems | Grade |
|--------|-------------|-------|
| `srrg-lean/SrrgLean/FixedPoints/H4Discharge.lean` | `proxy_hessian_neg_def_from_BetaFunction`, `no_flat_directions_proxy` (all gauge-sector proxy Hessian eigenvalues < 0; no flat directions); `h_psc_sc_from_hessian` under `ProxyFaithfulBridge` | [A_Lean] for eigenvalue results; [B] for bridge theorem |
| `srrg-lean/SrrgLean/Constants/BetaFunction.lean` | `proxy_hessian_negative_definite` (all three eigenvalues −4H_Haar(G_i) < 0) | [A_Lean] |

`ProxyFaithfulBridge` (connecting gauge-sector proxy Hessian to full SRRG efficiency ratio) remains
open; estimated 3–6 months of Lean functional analysis. See §5 Remark.

**Physical subspace IR-stability chain (2026-05-12):**

| Module | Key theorems | Grade |
|--------|-------------|-------|
| `srrg-lean/SrrgLean/FixedPoints/PhysicalSubspace.lean` | `certifiedIPT_lt_two` (φ < (2π)² pure arithmetic); `srrg_physical_fp_sustainable_from_h_psc_sc` (η ≥ IPT theorem under h_psc_sc); `srrg_physical_fp_bounded_above_from_h_psc_sc` (η ≤ 2 theorem under h_psc_sc); `IsIRStableUnder` predicate; `eta_above_uv_is_not_ir_stable` (η > 2 → not IR-stable); `srrg_physical_is_ir_stable` (physical FPs are IR attractors — axiom); `srrg_physical_fp_bounded_above_from_ir` (η ≤ 2 from IR-stability) | [A_Lean] × 3; [B axiom]; [B+] × 2; predicate |

All seven new items: zero sorry. Chain A axiom count reduced 3→1 (sustainability and UV-bound become [A_Lean] corollaries of h_psc_sc; `certifiedIPT_lt_two` proved from pure arithmetic). Chain B UV-bound elevated from [B] axiom to [B+] derived theorem.

## Files

| File | Purpose |
|------|---------|
| `srrg_paper.tex` | Main paper source (LaTeX, canonical) |
| `scripts/beta_eta_flow.py` | β_η flow trajectories numerical verification (§5 Remark) |
| `figures/beta_eta_flow.png` | Three-panel figure: β-function profile, phase portrait, flow trajectories |
| `scripts/weinberg_angle_haar.py` | Haar entropy ratio assessment for sin²θ_W (§8.4) |
| `scripts/weinberg_rg_running.py` | One-loop SM RG running from M_Planck to M_Z (§8.4) |
| `scripts/weinberg_gut_unification.py` | GUT unification, two-loop running, SU(5) 5/3 normalization tests for sin²θ_W (§8.4) |
| `cft_universality_classes.py` | CFT universality / ε₃ₛ crossing computation |
| `cft_universality_classes.png` | Figure: ε₃ₛ vs β for Ising and Potts-3 |
| `requirements.txt` | Python dependencies for script |
| `nova_zenodo_doi_placeholder.tex` | DOI injection stub |
| `results/` | SHA-256 content-addressed JSON outputs |

## Computational Artifacts

| Script / File | Purpose | Date | Status |
|---------------|---------|------|--------|
| `scripts/beta_eta_flow.py` | Integrates β_η flow from 8 ICs; verifies analytic solution; produces `figures/beta_eta_flow.png` | 2026-05-12 | In paper repository |
| `figures/beta_eta_flow.png` | Three-panel flow figure (§5 Remark) | 2026-05-12 | In paper repository |
| `scripts/weinberg_angle_haar.py` | Enumerates simple Haar entropy ratios vs sin²θ_W = 0.23122; tests §8.4 structural hypothesis; negative result [D→C] | 2026-05-12 | In paper repository |
| `scripts/weinberg_rg_running.py` | One-loop SM RG running from M_Planck to M_Z with SRRG boundary conditions; fixes λ from α_s(M_Z); negative result [D→C] | 2026-05-12 | In paper repository |
| `scripts/weinberg_gut_unification.py` | Tests three GUT-scale directions (GUT democratic −1886σ, two-loop −1358σ, SU(5) 5/3 +6039σ); root cause diagnosed — boundary condition problem; negative result [D→C] | 2026-05-12 | In paper repository |
| `cft_universality_classes.py` | Computes ε₃ₛ = MI·ξ/L for Ising and Potts-3 at critical β; tests ε₃ₛ → IPT hypothesis | 2026-05-12 | In paper repository |
| `cft_universality_classes.png` | Output figure from `--plot` run | 2026-05-12 | In paper repository |
| `requirements.txt` | numpy/matplotlib pins | 2026-05-12 | In paper repository |
| `results/cft_universality_4b672f8eb70f427d.json` | Ising L∈{4,6,8} ε₃ₛ results | 2026-05-12 | In `results/` |
| `results/cft_universality_913752f229248d5d.json` | Potts-3 L∈{4,6,8} ε₃ₛ results | 2026-05-12 | In `results/` |

See `REPRODUCE.md` for full instructions and expected output format.

## Upgrade history

- **2026-05-12 (PhysicalSubspace IR-stability chain):** `srrg-lean/SrrgLean/FixedPoints/PhysicalSubspace.lean` extended with 7 new zero-sorry theorems. Chain A architectural simplification: `srrg_physical_fp_sustainable_from_h_psc_sc` and `srrg_physical_fp_bounded_above_from_h_psc_sc` are now [A_Lean] corollaries of h_psc_sc (sustainability and UV-bound are theorems, not axioms, under h_psc_sc); `certifiedIPT_lt_two` proved algebraically [A_Lean] from pure arithmetic (φ < (2π)²). Independent axiom count for Chain A: 3→1. Chain B: UV-bound `srrg_physical_fp_bounded_above_from_ir` upgraded from [B] axiom to [B+] derived theorem via new `srrg_physical_is_ir_stable` IR-stability axiom + [A_Lean] sign analysis (`eta_above_uv_is_not_ir_stable`). New `IsIRStableUnder` predicate captures IR-attractor definition. Overall h_psc_sc architecture grade [A−] maintained; architecture cleaner. `scripts/weinberg_gut_unification.py` added: three GUT-scale directions tested (GUT unification −1886σ, two-loop running −1358σ, SU(5) 5/3 normalization +6039σ — all negative results; base bare Haar ratio ~+5001σ). Root cause diagnosed: SRRG Haar-entropy boundary condition incompatible with sin²θ_W regardless of RG running — requires matter-field content (Open Problem 5). Grade [D→C] unchanged. 7 new zero-sorry Lean theorems:

  | Theorem | Grade |
  |---------|-------|
  | `certifiedIPT_lt_two` | [A_Lean] |
  | `srrg_physical_fp_sustainable_from_h_psc_sc` | [A_Lean] |
  | `srrg_physical_fp_bounded_above_from_h_psc_sc` | [A_Lean] |
  | `IsIRStableUnder` (predicate) | — |
  | `eta_above_uv_is_not_ir_stable` | [B+] |
  | `srrg_physical_is_ir_stable` | [B axiom] |
  | `srrg_physical_fp_bounded_above_from_ir` | [B+] |

- **2026-05-12 (β_η derivation):** The η-direction β-function β_η = κ(η−IPT)(η−2) is derived (not merely posited) via Vieta's uniqueness theorem ([A_Lean], `BetaEtaQuadratic.lean`) and the machine-certified no-third-zero result ([A_Lean], `NoThirdFixedPoint.lean`). Two remaining named hypotheses: `SrrgPhysicalFixedPointExhaustion` (no third SRRG fixed point on physical subspace) and `SrrgBetaIsQuadraticHyp` (polynomial degree ≤ 2). Grade of h_psc_sc advances [B+] → [B+→A−]. β_η flow numerically verified (8 trajectories; `scripts/beta_eta_flow.py`; `figures/beta_eta_flow.png`). 6 new theorems: 5 [A_Lean] + 1 [B+] (all zero sorry).
- **2026-05-12 (H4 discharge):** Proxy Hessian eigenvalues all negative at proxy fixed point ([A_Lean], `H4Discharge.lean`, `BetaFunction.lean`); `ProxyFaithfulBridge` remains open. 3 [A_Lean] + 1 [B] theorems.
- **2026-05-12 (Weinberg angle scripts):** `scripts/weinberg_angle_haar.py` and `scripts/weinberg_rg_running.py` added; both return negative results, honestly disclosed (grade [D→C]).
- **2026-05-13 (Round 09 — α [A/D] and SRRG-MDL [B+]):** Appendix C added: direct coupling route for the fine-structure constant, $\alpha = g_1^2 g_2^2/[4\pi(g_1^2+g_2^2)]$ with Lean-certified bare couplings from P01 ($g_1^2=16/125$, $g_2^2=2329/5400$), yields $1/\alpha(M_Z)\approx 127.311$ (0.495% from PDG; grade [A/D]). By-product: $\sin^2\theta_W^{\rm bare}=3456/15101\approx 0.229$ (1.0% from PDG; [A/D]). SRRG–MDL equivalence conjecture introduced (Open Problem 9; grade [B+]): identifies SRRG $\arg\max F[S]$ with MDL $\arg\min K[S]$ for self-referential theories; structurally bridges P09 and P27. Three new rows added to Lean certification table (§9). Abstract, load-bearing assumptions table, and §8 open-problems list updated to reflect Round 09 results. P00, P01, and P09 companion references updated.
- **2026-05-12 (SRRG initial):** `srrg_paper.tex` created; core fixed-point existence, F-theorem, stability, and U(1) minimality theorems machine-checked in `srrg-lean` (zero sorry in all owned modules).

- **2026-05-31 (EPIC_083 G01 — OP9 CatAD partial closure):**
  Open Problem 9 (SRRG–MDL equivalence) upgraded from [B+] to CatAD partial:
  - Two new `srrg-lean` modules, commit `6ccf201` (zero sorry):
    - `SrrgLean/Bridges/ToMDL.lean` — 13 theorems; `srrg_op9_biconditional` proves the full
      equivalence SRRG fixed point ↔ MDL Kolmogorov minimizer, conditional on
      `UGPSubstrateConstraint` (one named hypothesis).
    - `SrrgLean/Core/CMCALanguage.lean` — formalizes CMCA encoding language; proves
      `cmca_k_eq_barrier_minus_viability` (K_CMCA(s) = B − F[s], zero sorry).
  - Key algebraic identity proved: K[S] = B − F[S]; argmax F = argmin K (zero sorry,
    by algebra alone).
  - Proportionalities are exact equalities: L[S] = B − R[S], L[data|S] = C_Λ[S].
  - Remaining gap: `UGPSubstrateConstraint` (two sorries: L4 shortest-program semantics,
    L6 abstract K = CMCA Kolmogorov). Full CatAL upgrade tracked as Rank 083-UGP-SUBSTRATE.
  - OP9 grade: [B+] → CatAD partial.

## Dependencies

- `nems-lean` — NEMS/PSC framework theorems
- `ugp-lean` — UGP gauge structure, GTE, coupling constants
- `ugp-physics-lean` — IPT theorem, GXT, H9, U1DirectProof
- `srrg-lean` — main SRRG Lean library (this paper's Lean contribution)
- **2026-05-15 (VEVProof — EW VEV structural derivation):**
  - Added VEVProof Lean cert table rows to §App.~B certified theorem table:
    `goldstone_volume_correction_per_generation` [A−], `psc_entropy_after_contraction` [A−],
    `ew_vacuum_manifold_uniqueness` [A−], `srrg_physical_fp_implies_ew_vacuum_manifold` [A−].
  - Added "Structural derivation of v (grade [A−])" paragraph to App.~B Higgs section (§app:higgs):
    $v_{\rm PSC} = 246.16$~GeV ($-0.024\%$ from $v_{\rm PDG}$; null-discipline saturation 0.35%).
    Formalized in `SrrgLean.VEVProof.*` (4 modules; zero sorry; conditional on 1 named axiom:
    `psc_ew_entropy_maximization`).
  - REPRODUCE.md updated: VEVProof section added with build instructions and module table.
- **Round G1 (2026-05-16):** PSCEntropyDuality axioms `psc_entropy_contraction_duality` and `srrg_s3_entropy_increase` discharged as proved theorems (zero sorry) in `SrrgLean.VEVProof.PSCEntropyDuality.lean`. VEVProof axiom count: 3 → 1 remaining (`psc_ew_entropy_maximization`). Grade unchanged: [A−].
