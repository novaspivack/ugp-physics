# PROVENANCE — The UGP Interaction Skeleton Theorem (Paper 23)

**Paper:** `ugp_dynamics_paper.tex`  
**Version:** April 2026 draft  
**Last verified:** 2026-04-25

---

## Paper history and scope

This paper presents the first machine-verified proof that the UGP (Universal
Generative Principle) framework determines the Standard Model's complete finite
renormalizable interaction skeleton, without any additional gauge-theoretic input.

It builds directly on:
- **Paper 01** (SM from UGP): GTE triples, orbit arithmetic, mass ratios
- **Paper 17** (Canonical Braid Atlas v2.0): charge formula Q=W/Nc, fiber bundle
- **ugp-lean** (Lean 4 formalization): ChargeTheorem, FiberBundle, ScaleTransport, IPT

The new formalization (`ugp-physics-lean`, Lean 4) was developed in April 2026
covering 17 modules across the following research blocks:
- Block A: PSC orbit uniqueness, winding table derivation, Ψ_Braid functor
- Block B: EW/RG hardening (hypercharge normalization, matching scales)
- Block C: UGP discrete action, MFRR action hardening
- Block D: Category enrichment (17 specs)
- Block E: Pre-paper audits (vertex audit, forbidden processes, claim audit)

---

## Lean code provenance

| Repository | Role | Language |
|-----------|------|----------|
| `ugp-lean` | ChargeTheorem, FiberBundle, ScaleTransport, IPT | Lean 4 / Mathlib 4 |
| `ugp-physics-lean` | Dynamics-paper Lean modules (17 modules) | Lean 4 / Mathlib 4 |

**ugp-physics-lean GitHub:** https://github.com/novaspivack/ugp-physics-lean  
**Clean initial commit:** `a24f235` (single root commit, 2026-04-25)  
**Zenodo DOI:** pending — deposit when Paper 23 is submitted to journal

**Mathlib version:** `v4.29.0-rc6`  
**Lean version:** determined by `lean-toolchain` file in each repo

**Key theorem provenance (selected):**

| Theorem | Module | Proved |
|---------|--------|--------|
| `ugp_gauge_fermion_equals_sm` (Silver) | VertexTheorem | April 2026 |
| `ugp_yukawa_implies_sm` (Gold, one-directional) | HiggsYukawa | April 2026 |
| `ugp_yukawa_allowed_eq_canonical_set` (Gold, exact on canonical set) | HiggsYukawa | April 2026 |
| `dark_sector_gap_all_isolated` | ForbiddenProcesses | April 2026 |
| `proton_decay_dim4_forbidden` | ForbiddenProcesses | April 2026 |
| `winding_quartet_forced_by_two_inputs` | WindingFromDoublet | April 2026 |
| `all_four_sm_anomalies_cancel` | EWStructure | April 2026 |
| `charge_from_winding_Nc3` | ugp-lean/ChargeTheorem | 2025 |
| `IPT_theorem` | ugp-lean/IPT | 2025 |

---

## Computational artifacts provenance

### PR-1 SESSION_31 corroboration

**Location:** `papers/23_ugp_dynamics/pr1_session31_corroboration/`

| File | Role |
|------|------|
| `action1_z4_winding_bijection_corrected.py` | Script that ran the bijection experiment |
| `action1_corrected_results.json` | Full data: 1,024,000 events, 8 seeds, 24 bijections |
| `REPORT_TO_UGP_PHYSICS_TEAM.md` | Full experimental report with methodology and caveats |

**⚠️ Dependency:** The script requires the full PR-1/Logos CA codebase (separate private
research repository, Particle Derivations). It will NOT run standalone.
The JSON data file is self-contained and can be inspected directly.

**Role in paper:** Computational corroboration of Theorem C4 in Paper 23 §12 (Related Work).
Not a proof — the Lean theorems are the proof. Independent prior computational foreshadowing.

**Full experiment available on request** from the Particle Derivations repository.

### Vertex audit

**File:** `vertex_audit_017035.json`  
**Generated:** 2026-04-25 by `papers/23_ugp_dynamics/vertex_truth_table.py`  
**SHA-256:** `c927758a9b7801db863102f4c2c4a08c7bea60a513d9a6d0c0538a64e46e0468`  
**Contents:** 64 EW vertex schemas (MISMATCH=0), 12 dark-sector transitions (all isolated), winding table uniqueness, forbidden-process certificates.

### EW predictions

**Primary artifact:** `papers/01_SM/canonical_run/comp_p01_EW_full_matching.json`  
**SHA-256 of prediction block:** `b8f9ac7cdb89851d8c589b4b23323764289b376d1e134cb7de47c53c21a5a707`  
**Protocol:** 2-loop Machacek–Vaughn β-functions; m_t threshold; SC-ZZ self-consistent matching.

### PR-1 SESSION_31 bridge experiment

**Location:** Particle Derivations repository (separate codebase)  
**Session:** `SESSION_31_UGP_DYNAMICS_BRIDGE` (2026-04-25)  
**Report:** `SESSIONS/SESSION_31_UGP_DYNAMICS_BRIDGE/REPORT_TO_UGP_PHYSICS_TEAM.md`  
**Scripts:** `action1_z4_winding_bijection_corrected.py`, `action4_better_rule_comparison.py`  
**Key finding:** 87.38% C4 consistency, C=0 exactly, across 1,024,000 events.

---

## Epistemic status of all claims

All claims in the paper are classified in three tiers:
- **[T]** = Zero-sorry Lean theorem (machine-verified)
- **[C]** = Computationally verified (Python/CA, reproducible)
- **[B]** = Bridge/research (structurally grounded, not yet [T])

**Known gap:** The UGPYukawaWeight function (connecting Yukawa vertices to the UGP mass orbit arithmetic) uses one structural placeholder `sorry`. This is a bridge item [B], clearly labeled in the paper (Remark after Theorem 7.2). It does not affect any theorem-grade claim.

**Known open items (honest disclosure):**
1. sin²θ_W and α_EM require loop corrections to close the remaining 0.1% gap in g₁
2. W(e) = -Nc from GTE orbit braid writhe (deepest open question)
3. Dark sector gap experimental confirmation via full CA TopologicalSpectrometer
4. The Z_UGP functor conjecture (amplitude-level formalization)

---

## Related papers in the UGP series

| Paper | Title | Status |
|-------|-------|--------|
| 01 | A Derivation of the SM from UGP | Published |
| 17 | Canonical Braid Atlas v2.0 | Published |
| 23 | UGP Interaction Skeleton Theorem (this paper) | April 2026 draft |

---

## Note on independence of definitions

The non-circularity of the main theorem (UGPVertex ≠ SMVertex by definition)
is documented in the `017B_DEFINITION_AUDIT.md` internal working note.
Key facts:
- `UGPVertex(f1,f2,B)` uses: winding conservation, sameSector (strand count), chirality from GTE T/T† history
- `SMVertex(f1,f2,B)` uses: conventional SM representation-theoretic vertex table
- These are proved equivalent; neither definition presupposes the other

---

## Change Log

### 2026-05-11 — m_W sigma updated throughout (PDG 2024 world average)


**Changes:**
- Abstract (line 94): −1.28σ → −0.42σ (PDG 2024 world avg 80.3692 ± 0.0133)
- EW predictions table (line 982): PDG value updated from 80.369 ± 0.020 to 80.3692 ± 0.0133; residual updated to −0.42σ; table caption updated.
- Body text (line 995): −1.28σ → −0.42σ (PDG 2024 world avg).
- Results table (line 1313): −1.28σ → −0.42σ (PDG 2024).
