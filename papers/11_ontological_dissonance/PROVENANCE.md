# PROVENANCE — Ontological Dissonance Minimization / SDS Validation

**Paper:** `Ontological_Dissonance_Minimization_SDS_Validation.tex`  
**Code root:** `pr0_system/` (repo root of `ugp-physics`)  
**Last verified:** 2026-04-13

---

## Canonical scripts

| Script | Path (relative to `ugp-physics/`) | Role | Verified |
|--------|-----------------------------------|------|---------|
| `compare_dissonance_and_phi.py` | `pr0_system/examples/paper_analysis/` | D–Φ correlation; produces r=−0.9108 | ✅ Exact |
| `pr0_sds_dissonance_bootstrap.py` | `pr0_system/examples/paper_analysis/` | D-minimization bootstrap (general) | ✅ Runs |
| `pr0_emergent_qcd.py` | `pr0_system/examples/animations/` | Strong-force field dynamics (EmergentQCD class) | ✅ Runs |
| `run_unified_all_forces_log.py` | `pr0_system/examples/paper_analysis/` | Figure 1 data (CSV) generator | ✅ Found |
| `plot_unified_time_series.py` | `pr0_system/examples/paper_analysis/` | Figure 1 PNG generator | ✅ Found |

## Key verified results

| Claim | Verified | Notes |
|-------|----------|-------|
| r=−0.9108 | ✅ Exact | n=21 samples, deterministic, no random seed |
| p<0.001 | ✅ Robust | p=9.86e-9 naive; p≈3.5e-10 after autocorrelation correction |
| Φ is a proxy | ⚠️ Noted in paper | Φ_proxy = H(4 quadrants) − H(whole); NOT genuine IIT Φ |
| Strong V=0.011+0.56/d² | ✅ In bootstrap runs | Values from iterative bootstrap, documented in paper §3.2 |
| EM, Weak, Gravity params | ✅ | Same bootstrap origin |
| Figure 1 PNG | ✅ Frozen artifact | `pr0_system/media/unified_all_forces_timeseries.png` |

## pr0_system package

- **`pr0_system/`** is the main simulation package (field evolution, forces, bootstrap, integration).
- The three canonical claim-verifying scripts (`compare_dissonance_and_phi.py`, `pr0_sds_dissonance_bootstrap.py`, `pr0_emergent_qcd.py`) are **standalone** — they do NOT import from `pr0_system`.
- `run_unified_all_forces_log.py` (Figure 1 data) **does** import `pr0_system.integration`. Install the package to regenerate Figure 1.

## Dependency map

```
compare_dissonance_and_phi.py
  ├── pr0_emergent_qcd.py  (EmergentQCD class, co-located)
  └── pr0_sds_dissonance_bootstrap.py  (compute_ontological_dissonance, co-located)
```

`pr0_sds_dissonance_bootstrap.py`: stdlib + numpy + scipy.ndimage; no data files.  
`pr0_emergent_qcd.py`: stdlib + numpy + scipy.ndimage; no data files.

## Wave 2 Revision Artifacts (2026-04-17)

| Artifact | Script | SHA-256 | Notes |
|----------|--------|---------|-------|
| `pr0_system/examples/paper_analysis/multi_trajectory_dphi_results.json` | `multi_trajectory_dphi.py` | `f3951eb3f4a7154cccf83b76d826a374cc075722e95c947b9de4e8ffa9e81769` | COMP-P11-B v2: 11 configs, exact original dynamics; orbital regime r∈[-0.95,-0.90] (7/7); tight/weak regime r≈0 (4/4) |
| `pr0_system/examples/paper_analysis/unconstrained_bootstrap_results.json` | `unconstrained_bootstrap.py` | `800119586d61981326bae7b02e52c74649f4f6d539c73666e64f07be4ace912b` | COMP-P11-A: 4/5 bound states without force-type prior |

## Key Honest Disclosures Added (Wave 2)

1. **Multi-trajectory robustness**: r = -0.9108 reproduced exactly in canonical run. Robust in orbital binding regime (sep=12-28, amp≥3.0): r∈[-0.95,-0.90], 7/7 configs. Breaks down in tight/weak regime (sep≤8 or amp≤2.5): r≈0, 4/4 configs. Physically interpretable.
2. **Unconstrained bootstrap**: D-minimization selects stability (4/5 bound states) without force-type knowledge; force-specific form recovery requires force-specific constraints.
3. **Phi_proxy = spatial heterogeneity**: Not true IIT Φ; qualifier applied consistently.
4. **Meta-law claim demoted**: "QCD/QED/EW/GR are facets of one meta-law" → "consistent with constrained-optimization picture."
