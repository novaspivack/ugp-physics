# SPEC_583_CSA — Conditional Survival Analysis Results

**Run date:** 2026-05-12
**Spec:** SPEC_583_CSA
**IPT:** 1.13091513
**DB mode:** prod

---

## Summary

| Metric | Value |
|--------|-------|
| Panel: bankrupt company-years | 1321 |
| Panel: survivor ticker-years | 55257 |
| Panel: total rows | 56578 |
| Conditional AUC G/D∈[0,2] | 0.314596 |
| ΔBIC(M4 vs M1) | -92.1866 |
| Three-regime structure confirmed | True |
| Regime 2→3 transition significant | True |
| **GXT Grade** | **[C+] (PARTIAL)** |

---

## Analysis A: Fine-grained Survival Curve

Failure rate per 0.1-width G/D bin (key bins shown):

| G/D Bin | N | Failed | Failure Rate | 95% CI | Notes |
|---------|---|--------|-------------|--------|-------|
| [-1.0, -0.9) | 129 | 12 | 9.30% | [5.40%, 15.56%] |  |
| [-0.9, -0.8) | 160 | 22 | 13.75% | [9.26%, 19.94%] |  |
| [-0.8, -0.7) | 185 | 21 | 11.35% | [7.55%, 16.73%] |  |
| [-0.7, -0.6) | 186 | 27 | 14.52% | [10.17%, 20.30%] |  |
| [-0.6, -0.5) | 226 | 21 | 9.29% | [6.16%, 13.79%] |  |
| [-0.5, -0.4) | 231 | 33 | 14.29% | [10.36%, 19.38%] |  |
| [-0.4, -0.3) | 287 | 31 | 10.80% | [7.71%, 14.92%] |  |
| [-0.3, -0.2) | 416 | 31 | 7.45% | [5.30%, 10.38%] |  |
| [-0.2, -0.1) | 786 | 61 | 7.76% | [6.09%, 9.84%] |  |
| [-0.1, 0.0) | 7641 | 103 | 1.35% | [1.11%, 1.63%] | ← G/D=0 |
| [0.0, 0.1) | 23877 | 100 | 0.42% | [0.34%, 0.51%] |  |
| [0.1, 0.2) | 749 | 61 | 8.14% | [6.39%, 10.32%] |  |
| [0.2, 0.3) | 558 | 46 | 8.24% | [6.24%, 10.82%] |  |
| [0.3, 0.4) | 622 | 36 | 5.79% | [4.21%, 7.91%] |  |
| [0.4, 0.5) | 634 | 18 | 2.84% | [1.80%, 4.44%] |  |
| [0.5, 0.6) | 604 | 16 | 2.65% | [1.64%, 4.26%] |  |
| [0.6, 0.7) | 632 | 21 | 3.32% | [2.18%, 5.03%] |  |
| [0.7, 0.8) | 641 | 13 | 2.03% | [1.19%, 3.44%] |  |
| [0.8, 0.9) | 603 | 8 | 1.33% | [0.67%, 2.60%] |  |
| [0.9, 1.0) | 666 | 7 | 1.05% | [0.51%, 2.15%] | ← G/D=1.0 |
| [1.0, 1.1) | 654 | 8 | 1.22% | [0.62%, 2.40%] |  |
| [1.1, 1.2) | 667 | 6 | 0.90% | [0.41%, 1.95%] | ← IPT=1.1309 |
| [1.2, 1.3) | 646 | 3 | 0.46% | [0.16%, 1.36%] |  |
| [1.3, 1.4) | 551 | 3 | 0.54% | [0.19%, 1.59%] |  |
| [1.4, 1.5) | 609 | 2 | 0.33% | [0.09%, 1.19%] |  |
| [1.5, 1.6) | 584 | 0 | 0.00% | [0.00%, 0.65%] |  |
| [1.6, 1.7) | 558 | 1 | 0.18% | [0.03%, 1.01%] |  |
| [1.7, 1.8) | 563 | 0 | 0.00% | [0.00%, 0.68%] |  |
| [1.8, 1.9) | 549 | 1 | 0.18% | [0.03%, 1.02%] |  |
| [1.9, 2.0) | 476 | 0 | 0.00% | [0.00%, 0.80%] |  |
| [2.0, 2.1) | 450 | 3 | 0.67% | [0.23%, 1.94%] |  |
| [2.1, 2.2) | 431 | 0 | 0.00% | [0.00%, 0.88%] |  |
| [2.2, 2.3) | 402 | 1 | 0.25% | [0.04%, 1.40%] |  |
| [2.3, 2.4) | 383 | 0 | 0.00% | [0.00%, 0.99%] |  |
| [2.4, 2.5) | 345 | 0 | 0.00% | [0.00%, 1.10%] |  |

---

## Analysis B: Three-Regime Comparison

| Regime | N | Failed | Failure Rate | 95% CI |
|--------|---|--------|-------------|--------|
| Regime 1: G/D < 0 (Destruction) | 14074 | 958 | 6.807% | [6.402%, 7.235%] |
| Regime 2: 0 ≤ G/D < IPT (Watch) | 30489 | 337 | 1.105% | [0.994%, 1.229%] |
| Regime 3: G/D ≥ IPT (Safe) | 12015 | 26 | 0.216% | [0.148%, 0.317%] |

**Odds ratio (Regime 2 vs Regime 3):** 5.15×
**Odds ratio (Regime 1 vs Regime 3):** 33.68×

| Test | Statistic | p-value | Significant? |
|------|-----------|---------|-------------|
| Chi-square (3 regimes) | 1672.9251 | 0.000000 | True |
| Fisher's exact (R2 vs R3) | 5.1538 | 0.000000 | True |
| Mann-Whitney (R1 vs R2) | 0 | 0.000000 | True |
| Mann-Whitney (R2 vs R3) | 0 | 0.000000 | True |

**Conclusion:** SIGNIFICANT: The transition from Watch (0≤G/D<IPT) to Safe (G/D≥IPT) is statistically significant (p<0.05). IPT marks a genuine step-change in failure rates.

---

## Analysis C: Piecewise Logistic Regression

| Model | Description | AIC | BIC | ΔBIC vs M1 |
|-------|-------------|-----|-----|-----------|
| M1_threshold_zero | Single threshold at G/D=0 | 11182.80 | 11200.68 | +0.00 |
| M2_threshold_unit | Single threshold at G/D=1.0 | 12089.14 | 12107.02 | +906.34 |
| M3_threshold_ipt | Single threshold at G/D=IPT=1.13092 | 12091.44 | 12109.33 | +908.65 |
| M4_two_thresholds | Two thresholds at G/D=0 AND G/D=IPT (three-regime) | 11081.67 | 11108.50 | -92.19 |
| M5_continuous | Continuous G/D (no discrete breakpoints) | 10308.54 | 10326.43 | -874.26 |

**Best model (BIC):** M5_continuous
**ΔBIC(M4 vs M1):** -92.19
**Three-regime supported (ΔBIC < −6):** True

**Interpretation:** ΔBIC(M4 vs M1) = -92.19. Strong evidence: the two-threshold model (G/D=0 AND G/D=IPT) fits significantly better than the single break-even threshold. IPT adds structural information beyond G/D=0.

---

## Analysis D: Conditional AUC within G/D ∈ [0, 2]

| Metric | Value |
|--------|-------|
| N total | 35474 |
| N bankrupt | 352 |
| N survivor | 35122 |
| AUC | 0.314596 |
| AUC bootstrap mean | 0.314698 |
| AUC 95% CI | [0.299396, 0.330685] |
| Youden G/D threshold | 1.094837 |
| Youden J | 0.103483 |
| IPT in Youden plateau | True |
| Youden near IPT (±0.2) | True |
| AUC > 0.60 (meaningful) | False |
| AUC > 0.65 (strong) | False |

**Conclusion:** NULL: AUC=0.3146 ≤ 0.60 within [0,2]. G/D provides negligible discrimination above break-even. The survival signal is primarily captured by the sign of G/D (positive vs. negative), not the magnitude above zero. IPT does not identify a meaningful second threshold.

---

## GXT Grade Update

| Criterion | Met? |
|-----------|------|
| Three-regime BIC strong (ΔBIC < −6) | True |
| Regime 2→3 Fisher significant | True |
| Conditional AUC > 0.65 | False |
| Conditional AUC > 0.60 | False |

**Prior grade:** [C+]  
**New grade:** [C+] — pathway: PARTIAL
**Upgraded:** False

**Rationale:** Structural break confirmed (ΔBIC=-92.19 < -6) but conditional AUC within [0,2] is below the 0.65 threshold for [B-] upgrade.

---

## Physics Interpretation

The conditional survival analysis addresses the key question raised by SPEC_579_SVT:
is IPT a genuine structural boundary, or merely a point on a monotone gradient?

**Result: THREE-REGIME STRUCTURE NOT CONFIRMED → GXT [C+] MAINTAINED**

The data does not support a distinct second structural break at IPT beyond G/D=0.
The survival signal is primarily captured by whether G/D is positive or negative.
IPT (1.13092) remains a valuable safety plateau with a 13.4× odds ratio
(from SPEC_579), but the physics interpretation should be:

- IPT is a conservative safety margin above the primary failure boundary at G/D=0
- The boundary at G/D=0 (break-even) is the main discriminating threshold
- Above G/D=0, the gradient is monotone (or weakly structured), not regime-structured

This is a valid and important finding: it constrains the physics claim. IPT is
predictively useful but is not a second phase transition in the thermodynamic sense.
