# SPEC_051_EWV — Phase 0 + Phase 1 Results

**Date:** 2026-05-11  
**Scripts:** `path0_error_decomposition.py`, `path1_ucl_vev_scan.py`, `path2_coleman_weinberg.py`

---

## Phase 0: Error Decomposition and g₂(M_W) Extraction

### g₂ running (computed from UGP 2-loop RGE)

| Coupling | Value | Source |
|---------|-------|--------|
| g₂_bare | 0.656732 | Lean-certified: √(2329/5400) |
| g₂_UGP(M_W) | 0.652846 | 2-loop SM running from M₂=37.4 GeV |
| g₂_SM(M_Z) | 0.651731 | SM reference |
| Running shift | −0.59% | From bare to EW scale |

SU(2) is IR-free for weak coupling: g₂ runs DOWN toward low energy (M_W < M₂).

### Scenario table: m_H under different v assumptions

| Scenario | v (GeV) | m_H (GeV) | σ from PDG | Notes |
|----------|---------|-----------|-----------|-------|
| PDG v + UGP λ_H | 246.220 | **124.947** | **−2.30σ** | λ_H contribution only |
| UGP v (bare g₂) + UGP λ_H | 244.786 | 124.220 | −8.91σ | P01 direct (same as published) |
| UGP v (running g₂) + PDG m_W | 246.243 | **124.959** | **−2.19σ** | ⚠ Circular — uses m_W_PDG |
| v from m_Z (no G_F, Path 1b) | 245.314 | 124.488 | −6.48σ | m_Z anchor; tree-level sin²θ_W |
| PDG v + SM λ_H | 246.220 | 125.200 | 0.00σ | SM reference |

### Key structural finding

**The 9σ m_H miss decomposes as:**
- **λ_H error:** φ/(4π) vs SM target → −0.40% → −2.30σ at PDG v
- **v error:** UGP v (bare g₂) vs PDG → −0.58% → −6.61σ additional
- **Total: −0.78% → −8.91σ** (matches computed P01 result)

**Critical insight:** If v were at the PDG value, m_H would be **−2.30σ** (not 9σ).  
The gap is almost entirely in v, not λ_H. Solving v closes 75% of the miss automatically.

To get m_H = 125.20 exactly with UGP λ_H: need v = **246.718 GeV** (only +0.202% above PDG).

### Why is v wrong?

UGP v (bare g₂) = 244.79 GeV uses g₂_bare directly. With the running g₂(M_W) = 0.65285 instead:
- v_self = 2·m_W_PDG/g₂(M_W) = **246.24 GeV** — essentially PDG (+0.009%)!
- m_H from this = **124.96 GeV → −2.19σ**

**BUT this is circular:** m_W_PDG was computed using G_F and v=246.22. The result  
v_self = v_PDG is a tautology, not a new derivation.

**Non-circular version (Path 1b, using m_Z instead of G_F):**
- v_from_mZ = 2·m_W_tree(from sin²θ_W_UGP, m_Z)/g₂_UGP(M_W) = 245.31 GeV → m_H = −6.48σ
- Worse than bare g₂ because tree-level m_W_UGP = m_Z·cos θ_W = 80.08 GeV is 0.37% too low

**Conclusion:** No non-circular, G_F-free derivation of v currently achieves the PDG value.  
The PDG-independent improvement path requires Paths 2–4.

---

## Phase 1.1: UCL/Quarter-Lock Scan for v/m_W (Path 3)

Scanned ~200 depth-2 combinations of structural atoms for match to v/m_W = 3.0632.

### Top hits for v/m_W ≈ 3.063

| Expression | Value | Dev from v/m_W |
|-----------|-------|---------------|
| **π/4 + 2/cos(θ_W_UGP)** | 3.06292 | **0.010%** |
| k_gen + 1/g₂_bare | 3.06153 | 0.055% |
| √3 + k_c | 3.06538 | 0.070% |
| (2 + k_L²)/g₂_bare | 3.06620 | **0.097%** — Quarter-Lock motivated |
| φ + 1/ln(2) | 3.06073 | 0.082% |

### Assessment

**π/4 + 2/cos(θ_W_UGP) at 0.010%:** Very close numerically. No obvious structural derivation. With a depth-2 atom library of ~200 items and 2% tolerance giving 15 hits, finding one at 0.010% is suggestive but not conclusive — needs null-discipline test before claiming significance.

**(2 + k_L²)/g₂_bare at 0.097%:** More physically motivated — combines the Quarter-Lock constant k_L² = δ/2^(n-1) = 7/512 (Lean-certified) with the bare coupling. Interpretation: the running correction to 2/g₂_bare is approximately k_L². This is not exact (0.097% off) but has a structural motivation worth pursuing.

**Exact relationship:** The running of g₂ from bare to M_W is a 0.59% shift. If (2 + k_L²)/g₂_bare ≡ 2/g₂(M_W) structurally, then v = m_W × (2 + k_L²)/g₂_bare and the running correction is captured by the Quarter-Lock term k_L²/g₂_bare ≈ 0.021. Need to verify if the SM 2-loop running correction β(g₂)·Δt/g₂ ≈ k_L² at the M₂→M_W range.

**1-loop running factor:** The 1-loop correction is:  
`g₂(M_W)/g₂_bare ≈ 1/(1 - b₂·Δt/(8π²)) ≈ 0.9934` (b₂ = −19/6, Δt = ln(80.4/37.4) = 0.765)

k_L² = 7/512 = 0.01367 ≈ 1 − 0.9934 = 0.0066... The ratio 0.01367/0.0066 ≈ 2.07 — not a clean match.

**v/m_Z scan:** Best hit **1/(φ·sin²θ_W_UGP) = 2.7005** at 0.013%. Combines golden ratio and Koide/UGP sin²θ_W. The formula v = m_Z/(φ·sin²θ_W) is intriguing but not clearly derivable from first principles.

**Verdict on Path 3:** No confirmed structural identity found. Two candidates worth deeper investigation:
1. π/4 + 2/cos θ_W — needs null-discipline test
2. (2 + k_L²)/g₂_bare — Quarter-Lock motivated, needs analytical verification

---

## Phase 1.2: Coleman-Weinberg Correction (Path 2)

**Path 2 is CLOSED NEGATIVE.**

The CW one-loop correction to the Higgs mass is large and negative:  
δm_H² ≈ −2137 GeV² (dominated by the top loop: −4m_t⁴ term)

This means m_H_tree must be ~133 GeV to give physical m_H = 125.2 GeV after CW.  
No simple c-value formula gives 133 GeV:
- c(H)/c(W) × m_W = 95 GeV → m_H_phys = 83 GeV ✗
- φ × m_W = 130 GeV → m_H_phys = 121.6 GeV (closest, but −33σ) ✗
- c(H)/c(Z) × m_Z = 99 GeV → m_H_phys = 87 GeV ✗

**Path 2 cannot close with simple c-value tree-level formula + SM CW correction.**

Note: The leading-log CW formula used here is approximate. The full one-loop SM Higgs self-energy is scheme-dependent. But the magnitude of the top correction (~46 GeV in m_H equivalent) means that any structural m_H_tree must be in the 130–140 GeV range, far from simple c-value results.

---

## Summary of All Paths

| Path | Status | Result |
|------|--------|--------|
| **0 (running g₂ improvement)** | ✓ COMPLETE | m_H = −2.19σ with self-consistent g₂(M_W), but computation is circular — needs v as input |
| **1b (m_Z anchor, no G_F)** | ✓ COMPLETE | m_H = −6.48σ — tree-level sin²θ_W error dominates |
| **2 (CW from c-values)** | ✗ NEGATIVE | Path 2 does not close — CW correction too large |
| **3 (UCL/QL scan)** | ~ PARTIAL | Two candidates (0.010%, 0.097% hits) — neither confirmed as structural identity |
| **4 (PSC energy scale)** | 🔵 DEFERRED | Long-term — requires PSC scalar sector derivation |

### The remaining problem precisely stated

**v needs to be +0.202% higher** than the UGP bare-g₂ prediction (246.72 vs PDG 246.22 GeV).  
**No current UGP structural formula achieves this without using G_F or m_Z as external input.**  
The two closest UCL hits (π/4 + 2/cos θ_W and (2+k_L²)/g₂_bare) need null-discipline testing and are likely numerical coincidences at the current precision.  
**Path 4 (PSC) is the most promising structural path** but requires a new research programme.

---

## Paper Update Recommendation (P01)

**What can be added to P01 now, honestly:**

> "Using the self-consistent two-loop running coupling g₂(M_W) = 0.6528 and the SM-18 Higgs quartic coupling λ_H = φ/(4π) (confirmed at 0.26σ), the Higgs mass prediction decomposes as: (a) the λ_H alone contributes a −2.30σ miss at the PDG VEV (v = 246.22 GeV); (b) the remaining −6.6σ arises from the UGP bare-coupling approximation to the EW VEV. Solving for v from UGP structural principles without G_F input is the remaining open problem (SPEC_051_EWV). If v is treated as known at the PDG value, the Higgs mass prediction improves to m_H ≈ 124.95 GeV (−2.30σ)."

**What NOT to say:** do not claim the 2.3σ improvement as achieved. It is conditional on v, which requires new work.
