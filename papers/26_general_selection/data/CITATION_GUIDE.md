# Citation Guide — VYRA GXT Empirical Results

## How to Cite

These results are from unpublished empirical work by Nova Spivack using the VYRA
proprietary financial intelligence platform. Suggested citation format:

> Spivack, N. (2026). Empirical tests of the Information Profit Threshold as an
> organizational efficiency boundary: Evidence from S&P 500 survival analysis and
> activist investor targeting signals. VYRA Research Working Paper.
> Mindcorp Inc. Available from: nova@mindcorp.ai

For specific tests, append the test name and primary statistic, e.g.:

> Spivack, N. (2026). *op. cit.* Test C (Organizational Survival, H8.4):
> AUC = 0.781, OR = 13.37×, N = 17,324 company-years, 2010–2022.

---

## Key Numbers for Inline Citation

| Test | Label | N | Primary Statistic | Sample Period |
|------|-------|---|------------------|--------------|
| A | TSR Prediction (3yr horizon) | 8,546 company-years | AUC = 0.564 (weak; EMH-consistent) | 2014–2023 |
| A | TSR Prediction (4yr horizon) | 7,284 company-years | AUC = 0.585 (best horizon) | 2014–2022 |
| A | G/D persistence (3yr) | 2,454 above-IPT companies | 67.4% remain above IPT after 3yr | 2014–2020 |
| B | Activist targeting (2yr) | 2,006 obs (102 filed) | AUC = 0.698, MW p = 8.2×10⁻¹² | 2013–2023 |
| B | Activist targeting (1yr) | 2,017 obs (113 filed) | AUC = 0.679, MW p = 8.3×10⁻¹¹ | 2013–2023 |
| C | Survival, overall | 17,324 (1,354 bankrupt) | AUC = 0.781, OR = 13.37× at IPT | 2010–2022 |
| C | Survival, T−1 | 16,368 (398 bankrupt) | AUC = 0.840, OR = 34.46× at IPT | 2010–2022 |
| D | H3 (entropy, lag-2) | 66 quarters | Spearman ρ = 0.339, p = 0.005 | 2010–2023 |
| D | H6 (attractor, t+3) | 118 treated | Cohen's d = 0.334, p = 0.077 | 2015–2023 |
| E | Three-regime BIC test | 56,578 company-years | ΔBIC = −92.19 (M4 vs M1) | 2010–2023 |
| E | Failure cascade | 56,578 company-years | 6.81% → 1.11% → 0.22% across regimes | 2010–2023 |
| E | Conditional AUC | 35,474 (Watch/Safe only) | AUC = 0.315 within G/D ∈ [0, 2] | 2010–2023 |

**IPT constant:** 1.13091513 = 1 + ln(φ)/(2·ln(2π)), where φ = (1+√5)/2

---

## Figure Reference Numbers

| Figure | Caption (short) | Test |
|--------|----------------|------|
| Figure 1 | ROC curve, G/D vs. 3yr TSR (N=8,546, AUC=0.564) | A |
| Figure 2 | AUC by prediction horizon (1–5yr), full universe | A |
| Figure 3 | AUC by G/D tenure stratum (tenure=0 vs 1–2 vs ≥3yr) | A |
| Figure 4 | BH-FDR correction table — multiple testing adjustment | A |
| Figure 5 | G/D level vs. activist 13D filing rate | B |
| Figure 6 | G/D distribution by activist event type | B |
| Figure 7 | Filing rate by G/D decile bin (zone test) | B |
| Figure 8 | ROC curve, G/D vs. bankruptcy (N=17,324, AUC=0.781) | C |

---

## Reproducibility Note

All analyses use:
- **Data:** VYRA production database (Bloomberg/FMP fundamentals, EDGAR XBRL filings, SEC 13D activist events, OHLCV daily price history)
- **Bankrupt company fundamentals:** EDGAR XBRL Company Facts API (retains historical ROIC/WACC data post-delisting, enabling survivorship-bias-free survival analysis)
- **Statistical software:** scikit-learn (ROC/AUC, BH-FDR), scipy (Mann-Whitney, Fisher exact, Spearman), statsmodels (logistic regression BIC), numpy (bootstrap CI)
- **Analysis scripts:** VYRA codebase, `scripts/run_spec574c_fulluniv_youden.py` (Test A), `scripts/run_spec576_activist_signal.py` (Test B), `scripts/run_spec579_survival_test.py` (Test C), `scripts/run_spec578_phase_a_infothermo.py` (Test D), `scripts/run_spec583_conditional_survival.py` (Test E)
- **G/D ratio definition:** G/D = (ROIC − WACC) / |WACC| when WACC ≠ 0; G/D > 0 iff ROIC > WACC (value creation); G/D ≥ IPT iff information surplus is achieved
- **IPT:** 1.13091513 (six significant figures used throughout; full precision = 1.1309151286162316)

---

## Contact

Nova Spivack  
nova@mindcorp.ai  
VYRA / Mindcorp Inc.  

For access to underlying data or methodology details, contact directly.
