# SPEC_574c — Full-Universe G/D Youden Test Results

**Run date:** 2026-05-11  
**IPT:** 1.13091513  
**Universe:** 1972 tickers (signal_features), 10 annual periods  
**Prior (SPEC_574b):** 25 tickers, AUC@3yr=0.5595, tenure≥3 AUC=0.665 (N=40)  

---

## Part A — Multi-Horizon AUC (Full Universe)

| Horizon | N obs | AUC | Youden threshold | IPT in plateau? |
|---|---|---|---|---|
| 1yr | 9852 | **0.5582** | 0.0132 | NO ✗ |
| 2yr | 9850 | **0.5559** | 0.0202 | NO ✗ |
| 3yr | 8546 | **0.5641** | 0.0139 | NO ✗ |
| 4yr | 7284 | **0.5850** | 0.0129 | NO ✗ |
| 5yr | 6126 | **0.5726** | 0.0127 | NO ✗ |

---

## Part B — Tenure Stratification (3yr horizon)

| Tenure Group | N obs | AUC | IPT in plateau? |
|---|---|---|---|
| A_tenure_0 | 6254 | **0.5361** | NO ✗ |
| B_tenure_1_2 | 1095 | **0.5095** | NO ✗ |
| C_tenure_3plus | 1197 | **0.4899** | NO ✗ |

---

## Part D — BH-FDR Correction

Method: Benjamini-Hochberg, α=0.05, n_tests=3

| Group | N obs | AUC | p (raw) | p (BH) | Reject H₀? |
|---|---|---|---|---|---|
| Tenure = 0 | 6254 | 0.5361 | 0.0000 | 0.0000 | **✓ YES** |
| Tenure = 1–2 | 1095 | 0.5095 | 0.5884 | 0.5884 | NO |
| Tenure ≥ 3 | 1197 | 0.4899 | 0.5585 | 0.5884 | NO |

---

## Part C — Persistence (3yr)

- Overall persistence rate: **0.674** (1655 / 2454 companies)

---

## Part E — Non-W5 Sub-Analysis

- AUC @3yr (non-W5): **0.5623** (N=8410)
- Tenure≥3 AUC (non-W5): **0.4779** (N=1158)

---

## Decision Gate

**Grade: WEAK_NEGATIVE**

AUC=0.4899 ≤ 0.60 → G/D tenure does not discriminate

---

## Outputs

```
results/ipt_oef/v3_fulluniv_youden_results.json
results/ipt_oef/v3_fulluniv_youden_results.md
results/ipt_oef/v3_auc_by_horizon_fulluniv.png
results/ipt_oef/v3_roc_3yr_fulluniv.png
results/ipt_oef/v3_tenure_auc_fulluniv.png
results/ipt_oef/v3_bh_fdr_table.png
```
