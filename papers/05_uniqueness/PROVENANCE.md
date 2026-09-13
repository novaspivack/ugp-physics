# PROVENANCE — The Uniqueness of the UGP

**Paper:** `The Uniqueness of the Universal Generative Principle.tex`  
**Primary code root:** `ugp_discovery_lab/` (in the ugp-physics clone root)  
**Last replication:** 2026-04-13

---

## Canonical code and artifacts (Task A inventory)

All scripts and data live in `UGP_discovery_lab/` root.

### Stage 1: Arithmetic Sieve

| Item | Path | Role | Runs? |
|------|------|------|-------|
| `ugp_uniqueness_sieve.py` | `UGP_discovery_lab/` | Full n=4–30 two-stage sieve | ✅ ~42s |
| `uniqueness_sieve_results.json` | `UGP_discovery_lab/` | Frozen output: `total_survivors: 1` | ✅ |
| `uniqueness_sieve_summary.md` | `ugp_discovery_lab/lab_notebooks/` (gitignored; author-local) | Narrative summary | ✅ |

### Stage 2: Final Physical Sieve

| Item | Path | Role | Runs? |
|------|------|------|-------|
| `ugp_final_sieve.py` | `UGP_discovery_lab/` | Applies δ_UGP constraint to 6 survivors | ✅ <1s |
| `survivors.csv` | `UGP_discovery_lab/` | Input: 6 rows (n=10,13,16,20,22,28) | ✅ |
| `final_sieve_results.json` | `UGP_discovery_lab/` | Frozen output: 1/6 passes | ✅ |
| `final_sieve_summary.md` | `ugp_discovery_lab/lab_notebooks/` (gitignored; author-local) | Narrative summary | ✅ |

### Cleanroom independence tests

| Item | Path | Role | Runs? |
|------|------|------|-------|
| `test_ugp_t_02_first_principles.py` | `UGP_discovery_lab/` | Independent first-principles derivation of δ | ✅ |
| `test_ugp_t_03_universal_instantiation.py` | `UGP_discovery_lab/` | Universal δ for all 3 gauge couplings | ✅ |

### Supplementary (not cited for core uniqueness claim)

| Item | Path | Role | Runs? |
|------|------|------|-------|
| `protocol_victory_lap_final.py` | `UGP_discovery_lab/` | RG running of cleanroom δ to physical couplings | ⚠️ Fails at Step 3: `float - str` type error in `ugp_renormalization_finalizer_enhanced`. Not needed for uniqueness theorem. |

---

## Key results verified (2026-04-13)

| Paper claim | Value | Verified |
|-------------|-------|----------|
| Exactly 6 arithmetic survivors (n=4–30) | n=10,13,16,20,22,28 | ✅ |
| Only n=10/b₁=73 passes Stage 2 | relative error 2.70×10⁻⁵⁹ | ✅ |
| δ_UGP = 0.016599156624… (60 s.f.) | Matches formula exactly | ✅ |
| T-02 cleanroom pass | error −0.00508% vs 0.0166 | ✅ |
| T-03 universal δ | g₁²=0.1301, g₂²=0.4385, g₃²=1.5103 | ✅ |

---

## Dependency notes

- All sieve scripts are **stdlib only** (`json`, `math`, `decimal`, `csv`)
- High-precision arithmetic: `getcontext().prec = 80`
- No external pip packages required
- `test_ugp_t_02` and `test_ugp_t_03` require `ugp_discovery_lab` package: `pip install -e .` from lab root

## Wave 2 Revision Artifacts (2026-04-17)

| Artifact | Script | SHA-256 | Notes |
|----------|--------|---------|-------|
| `uniqueness/canonical_run/delta_noncircular.json` | `uniqueness/derivation_non_circular.py` | `884b04d1ca58898dfdc8053f268fca8956872d8c284a376b0fd3f85e3eb947f9` | COMP-P05-A: Non-circular δ_UGP from CODATA + Lean constants |
| `uniqueness/survivors_ugplean.csv` | Generated via sympy sieve | — | COMP-P05-B: Correct b₁ values for n∈[4,30]; replaces buggy survivors.csv |

## Caveats Added (Wave 2)

1. **survivors.csv was buggy for n>10**: b₁ values for n=13,16,20,22,28 were wrong. Correct values from independent sieve: n=13→209, n=16→529, n=20→10389, n=22→4153, n=28→33393. Stage 2 conclusion unaffected (all non-n=10 seeds fail Stage 2 with both correct and incorrect b₁).

2. **Non-circularity of Stage 2**: δ_target = formula(73) is consistent with CODATA-derived δ_CODATA to 2.39 ppm (the TE1.P residual). CODATA independently selects b₁=73 (b₁_required = C/δ_CODATA = 73.0002). Documented in canonical_run/delta_noncircular.json.

3. **n-scope**: Uniqueness certified for n∈[4,30]. All-n extension is the open Asymptotic Sparsity Conjecture (formally stated in ugp-lean).
