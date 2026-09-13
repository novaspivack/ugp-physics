# REPRODUCE — The UGP Interaction Skeleton Theorem (Paper 22)

**Paper:** `ugp_dynamics_paper.tex`  
**Last verified:** 2026-04-25

---

## Requirements

- **Lean 4** with `elan` toolchain manager (installs automatically via `lean-toolchain`)
- **Mathlib 4** (fetched by `lake update`)
- **Python 3.9+** (for vertex audit and EW predictions)
- **pdflatex** or `latexmk` (for paper compilation)

---

## 1. Verify all Lean theorems (primary result)

**Repository:** https://github.com/novaspivack/ugp-physics-lean

```bash
git clone https://github.com/novaspivack/ugp-physics-lean
cd ugp-physics-lean

# Download Mathlib precompiled cache (avoid full build from source)
lake exe cache get

# Build all 17 modules
lake build

# Expected output:
# Build completed successfully (8313+ jobs).
# 0 errors. 0 sorry (theorem-grade).
```

**What this verifies:** All 40+ theorem-grade [T] results in the paper, including:
- `ugp_gauge_fermion_equals_sm` (Silver closure — §7)
- `ugp_yukawa_implies_sm` (Gold closure, one-directional — §7)
- `ugp_yukawa_allowed_eq_canonical_set` (Gold closure, exact equality on the canonical SM Yukawa set — §7)
- `dark_sector_gap_all_isolated` (dark sector — §8)
- `proton_decay_dim4_forbidden` (proton stability — §8)
- `all_four_sm_anomalies_cancel` (anomaly cancellation — §3)
- ... (see Appendix A of paper for full list)

**One structural placeholder sorry** exists in `UGPYukawaWeight` (CategoryEnrichment.lean).
This is a bridge item [B], not a theorem-grade claim. All results in Appendix A are unaffected.

---

## 2. Reproduce the vertex audit (MISMATCH COUNT = 0)

```bash
cd papers/22_ugp_dynamics

python3 vertex_truth_table.py
```

Expected output:
```
EW vertex audit: 64 schemas, SM=12, UGP=12, MISMATCH=0
Dark sector gap: 12 transitions checked, all isolated = True
MISMATCH_COUNT: 0
SHA-256: c927758a9b7801db863102f4c2c4a08c7bea60a513d9a6d0c0538a64e46e0468
```

The JSON artifact `vertex_audit_017035.json` contains the full table.

---

## 3. Reproduce EW predictions (m_W and α_s)

```bash
cd papers/01_SM/canonical_run

python3 comp_p01_EW_full_matching.py
```

Expected predictions:
- `m_W = 80.3637 GeV` (−1.28σ from PDG)
- `α_s(MZ) = 0.11790` (0.00σ from PDG)
- `sin²θ_W = 0.2316` (0.16% physical deviation; tree-level)
- `α_EM⁻¹ = 127.76` (0.15% physical deviation; tree-level)

**Protocol:** g₂ injected at M₂* = 34.66 GeV; g₃ injected at M₃* = 89.50 GeV; g₁ used directly as g_Y at MZ.

---

## 4. Verify upstream Lean prerequisites (ugp-lean)

The `ugp-lean` repository provides the foundation modules used in this paper:

```bash
git clone https://github.com/novaspivack/ugp-lean
cd ugp-lean

lake build UgpLean.BraidAtlas.ChargeTheorem
# Expected: Build completed successfully. 0 errors. 0 sorry.
# Proves: Q = W/Nc for all SM fermion types.

lake build UgpLean.GTE.FiberBundle
# Expected: Build completed successfully.
# Proves: canonical_lepton_winding, fiber uniqueness.
```

---

## 5. Compile the paper

```bash
cd papers/22_ugp_dynamics

pdflatex ugp_dynamics_paper.tex
pdflatex ugp_dynamics_paper.tex   # second pass for cross-references

# Expected: Output written on ugp_dynamics_paper.pdf (24 pages).
```

---

## 6. Inspect PR-1 SESSION_31 corroboration data (optional)

The 87.38% / C=0 result cited in §12 is documented in:

```
papers/22_ugp_dynamics/pr1_session31_corroboration/
  action1_corrected_results.json    ← full numerical data (self-contained)
  action1_z4_winding_bijection_corrected.py  ← experiment script (reference only)
  REPORT_TO_UGP_PHYSICS_TEAM.md    ← full experimental report
```

**The JSON is self-contained** — open it directly to inspect the 87.38%
consistency rate, C=0 result, and all 24 bijection rankings across 8 seeds
(1,024,000 events). No code needs to run to verify the reported numbers.

**The script will NOT run standalone** — it requires the full PR-1/Logos CA
codebase (separate private research repository). See the `README.md` in that
folder. The full experiment is available on request.

This corroboration is NOT part of the central proof. The Lean theorems
(`ugp-physics-lean`) are the proof; PR-1 is independent foreshadowing.

## Notes

- The PR-1 SESSION_31 bridge experiment code is in the Particle Derivations repository (separate from ugp-physics). The quantitative results (87.38%, C=0) are documented in the paper and in SESSION_31_UGP_DYNAMICS_BRIDGE/REPORT_TO_UGP_PHYSICS_TEAM.md.
- The PR-0 force-emergence results are in `ugp-physics/pr0_system/`. The D-Φ correlation (r=−0.91) is documented there.
- All Lean module names use the Lean 4 dot-path convention (`UgpPhysicsLean.VertexTheorem` etc.).
