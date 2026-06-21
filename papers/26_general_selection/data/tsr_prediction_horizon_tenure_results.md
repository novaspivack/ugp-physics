# SPEC_574b — Multi-Horizon + Tenure Stratification Results

**Run date:** 2026-05-10  
**IPT constant:** 1.13091513  
**Universe:** S&P 500 walk-forward (W5 parquet)  
**Tickers:** 25  

---

## Part A — AUC by Forward TSR Horizon

| Horizon | N obs | AUC | Youden threshold | Plateau [low, high] | IPT in plateau? |
|---|---|---|---|---|---|
| 1yr | 152 | **0.4791** | 2.0984 | [2.0984, 2.0984] | NO ✗ |
| 2yr | 152 | **0.4993** | 5.3562 | [5.3562, 5.3562] | NO ✗ |
| 3yr | 136 | **0.5595** | 3.0074 | [3.0074, 3.0074] | NO ✗ |
| 4yr | 120 | **0.5244** | 3.0074 | [3.0074, 3.0074] | NO ✗ |
| 5yr | 104 | **0.5288** | 2.4632 | [2.4227, 2.4632] | NO ✗ |

---

## Part B — Tenure Stratification (3yr horizon)

| Tenure Group | N obs | AUC | Youden threshold | IPT in plateau? |
|---|---|---|---|---|
| A_tenure_0 | 61 | **0.5452** | 0.2660 | NO ✗ |
| B_tenure_1_2 | 35 | **0.5784** | 2.1087 | NO ✗ |
| C_tenure_3plus | 40 | **0.6650** | 4.7116 | NO ✗ |

---

## Part C — Persistence (3yr)

- Overall persistence rate: **0.810** (100 → 81 companies)

---

## Outputs

```
results/ipt_oef/v2_auc_by_horizon.png
results/ipt_oef/v2_roc_3yr.png
results/ipt_oef/v2_roc_5yr.png
results/ipt_oef/v2_tenure_auc.png
results/ipt_oef/v2_gd_by_tercile_3yr.png
results/ipt_oef/v2_horizon_tenure_results.json
```
