# PR-1 session 31 Corroboration — Reference Artifacts

**Source:** session 31_UGP_DYNAMICS_BRIDGE (April 2026)  
**Role in Paper 23:** Computational corroboration of Theorem C4  
(`sm_allowed_iff_standard_winding_transfer [T]`). NOT a proof — the Lean
theorems are the proof. This is independent prior computational foreshadowing.

## What these files contain

| File | Contents |
|------|----------|
| `action1_z4_winding_bijection_corrected.py` | Script that ran the bijection experiment (87.38%, C=0) |
| `action1_corrected_results.json` | Full results: 1,024,000 events, 8 seeds, 24 bijections ranked |
| `REPORT_TO_UGP_PHYSICS_TEAM.md` | Full experimental report with methodology, results, caveats |

## The PR-1 system specification

**PR-1 (Primordial Reversible, Radius-1)** is a 1D reversible cellular automaton on a
loop of N cells. Each cell carries four state fields:

| Field | Type | Role |
|-------|------|------|
| `g` | Z₄ = {0,1,2,3} | Phase / particle-identity field |
| `l` | Z₈ = {0,...,7} | Slope proxy / momentum-like field |
| `μ` | {−1, 0, +1} | Slope-change parity |
| `m` | {0, 1} | Parity bit |

The dynamics is a Margolus-neighbourhood alternating rule with three guarded
involutions acting on adjacent cell pairs: **R** (Rotor), **X** (Mixer),
**S** (Shear/slope updater).

## The Logos Alpha rule

The specific rule used in session 31 is the **Logos Alpha rule**, which was
identified as the optimal rule by the Logos Search (September–October 2025,
SESSION_9.21) by exhaustive sweep over rule space.

**Rule specification:** `p3:p3, identity, q1, g0≠g1`

| Component | Value | Meaning |
|-----------|-------|---------|
| R-transform | `p3` | Cyclic permutation of Z₄ |
| R-forbidden mask | `p3` | R always fires (unconditional) |
| X-transform | `identity` | X is identity (m field frozen) |
| S-shear | `q1` | 90° shear: l → l+1 per cell |
| S-condition | `g0 ≠ g1` | S fires only at phase domain boundaries |

**Key structural property of the Logos Alpha rule:**

The R-clause fires unconditionally and maps every pre-R Δg=2 pair (which
under the natural bijection has |ΔW|=2, a forbidden cross-family transition)
to post-R Δg=0 (no S-firing). This suppression is **exact**: C=0 across all
seeds (zero false suppressions of SM-allowed events). The 87.38% figure is
the rate of correct selection for the remaining event types; the 12.62%
residual is an irreducible single-field ambiguity (Δg∈{1,3} pairs that mix
doublet and forbidden transitions indistinguishably in the g-field alone).

## Initialization protocol (canonical)

All session 31 results used **canonical two-cluster initialization**:
- 60% cell density concentrated in two spatial clusters
- Zero background density
- This is the same initialization used in the historical PR-1 experiments
  (September–October 2025) that discovered the Logos condition

**Non-canonical initialization** (e.g., simple random) gives ~25% (noise level)
and must NOT be used to reproduce the cited result.

## Bijection convention

The **natural P23 bijection** φ maps Z₄ phase values to SM winding numbers:

| g ∈ Z₄ | W (winding) | SM particle |
|--------|-------------|-------------|
| 0 | 0 | neutrino ν |
| 1 | −1 | down quark d |
| 2 | +2 | up quark u |
| 3 | −3 | charged lepton e |

All results in `action1_corrected_results.json` use **pre-R g-values** (the
particle-identity g field before the R-clause fires). Using post-R values gives
~25% (noise). This distinction is specific to the Logos Alpha rule.

## ⚠️ These scripts will NOT run standalone

`action1_z4_winding_bijection_corrected.py` depends on the full
PR-1/Logos CA codebase (PR-1_UGP_Loop_CA engine, Logos search infrastructure,
canonical initialization routines). The full codebase is in a separate private
research repository (Particle Derivations) and is not included here.

These files are provided as **reference documentation** for the experiment
methodology and results cited in Paper 23 §12 (Related Work). The
`action1_corrected_results.json` data file contains the complete
numerical results and is self-contained for inspection.

## Key cited result

- **87.38% consistency** with the C4 condition over 1,024,000 events (8 seeds:
  42, 0, 7, 13, 99, 123, 256, 777; N=256, 500 steps per seed)
- **C = 0 exactly** across all seeds (no false suppressions of SM-allowed events)
- Natural bijection φ: {0,1,2,3} → {0,−1,+2,−3} is co-optimal among all 24

## Full request

If you need to reproduce the full experiment, the complete PR-1 codebase
and session 31 directory (including all four action scripts and their data)
are available on request.
