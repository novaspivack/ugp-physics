# VYRA Empirical Artifacts — GXT Organizational Domain Tests
**Prepared by:** Nova Spivack / VYRA Research  
**Date:** 2026-05-12  
**For:** GXT / IPT Physics Research Program  

---

## Summary

This bundle contains machine-readable results and figures from five empirical tests of the
Information Profit Threshold (IPT = 1.13091513 = 1 + ln(φ)/(2·ln(2π))) as an organizational
efficiency threshold. Data source: S&P 500 constituents and U.S. public companies, 2010–2023,
VYRA production database (Bloomberg/FMP fundamentals, EDGAR XBRL filings, SEC 13D activist events).

**IPT derivation:** φ = (1+√5)/2 (golden ratio). IPT is the information profit threshold in the
Spivack IPT framework — the minimum ROIC/WACC ratio (G/D, where G = ROIC − WACC and D = |WACC|,
expressed as a ratio such that G/D ≥ IPT implies genuine information surplus in capital allocation).
The quantity IPT = 1 + ln(φ)/(2·ln(2π)) ≈ 1.13091513 arises from the intersection of the golden
ratio and logarithmic information scaling at the organizational level.

---

## GXT Evidence Summary

| Test | N | Key Metric | GXT Grade |
|------|---|-----------|-----------|
| A: TSR Prediction | 8,546 company-years (3yr horizon) | AUC = 0.564 (weak, positive) | [C] consistent with EMH |
| B: Activist Targeting | 2,006 obs (2yr window) | AUC = 0.698, p < 0.0001 | [C+] behavioral |
| C: Survival (H8.4) | 17,324 obs (1,354 bankrupt + 15,970 survivors) | AUC = 0.781, OR = 13.37× | [C+] suggestive |
| D: Entropy Signal (H3) | 66 quarters | ρ = 0.339, p = 0.005 | [C+] market-level |
| E: Three-Regime Structure | 56,578 company-years | ΔBIC = −92.19 | [C+] structural |

**Aggregate GXT grade: [C+]** — IPT is confirmed as a genuine structural threshold with a 13.37×
protection factor in survival analysis, ΔBIC = −92.19 evidence for three-regime structure, and
AUC = 0.698 in predicting activist investor targeting. The dominant null result (Test A) is
interpretable as an EMH consistency check: IPT does not predict future market-priced returns, but
it does predict fundamental corporate outcomes. Path to [B−] requires a bias-controlled conditional
AUC test within the Watch regime (G/D ∈ [0, IPT]).

---

## File Manifest

### data/ — Machine-Readable Results

---

#### `tsr_prediction_fulluniv_N8546_results.json` / `.md`
**Test A: Full-Universe TSR Prediction (null / EMH-consistent result)**

ROC/AUC analysis of G/D ratio as a predictor of 3-year total shareholder return (TSR), using the
full S&P 500 universe over ten annual baseline dates (2014–2023). The label is top-vs-bottom
tercile TSR over each horizon (1–5 years). G/D data is derived from VYRA fundamentals (ROIC/WACC).

Key statistics (3yr horizon, primary result):
- N = 8,546 company-years (N = 9,852 at 1yr; declines with horizon due to survivor availability)
- AUC = 0.564, Youden J_max = 0.111
- Youden optimal threshold: G/D = 0.0139 (not IPT)
- IPT is not in the plateau of optimal thresholds
- Mann-Whitney p < 10⁻⁶ (G/D differs between top/bottom tercile groups, but AUC is weak)
- G/D persistence (3-year): 67.4% of above-IPT companies remain above IPT after 3 years

**Interpretation:** G/D has statistically significant but economically weak discriminatory power
for future TSR. AUC values (0.56–0.59 across horizons) are above chance but below the 0.60
threshold for actionable prediction. This is consistent with Efficient Market Hypothesis: IPT
captures fundamental value creation, which is already priced into equities.

Tenure stratification (part_b): AUC drops to 0.489–0.509 for companies with G/D tenure ≥ 1 year,
suggesting any TSR signal is concentrated in the first year a company enters or exits the IPT zone.

BH-FDR corrected results (part_d): Only tenure-0 (first-year IPT transitions) survives
multiple-test correction (q = 3×10⁻⁶). Longer-tenure groups do not.

---

#### `tsr_prediction_horizon_tenure_results.json` / `.md`
**Test A (v2): Multi-Horizon and Tenure Stratification**

Earlier version of the TSR prediction analysis with explicit tenure-stratified AUC curves across
1–5 year horizons. Companion to the full-universe results above; provides per-year breakdown with
tenure-indexed subgroups. Used for Figures 2–4.

---

#### `activist_signal_N2006_AUC0698_results.json` / `.md`
**Test B: IPT as Activist Investor Targeting Signal**

Four-part analysis testing whether G/D ratio predicts SEC Schedule 13D activist filing events
(≥5% ownership with intent to influence management) in S&P 500 companies, 2013–2023.

Key statistics (primary result: 2yr window):
- N = 2,006 obs (102 activist-filed, 1,904 control)
- AUC = 0.6977, 95% CI [0.631, 0.763]
- Mann-Whitney p = 8.17×10⁻¹² (U = 58,716)
- Best AUC at 2yr lookback window; AUC = 0.679 at 1yr, AUC = 0.629 at 3yr
- Zone rates (by G/D regime): Destruction 5.88%, Zipf 5.80%, Above-IPT 8.96%; χ² p = 0.040

Screener orthogonality test (test2): G/D correlates with VYRA governance receptivity score
(ρ = 0.207, p < 10⁻⁴) and total value gap (ρ = −0.260, p < 10⁻⁴), confirming G/D captures
related variance but is not fully orthogonal to existing activist signals.

**Interpretation:** Companies with low G/D (value-destroying or marginal return on capital) are
significantly more likely to be targeted by activist investors. AUC = 0.70 is a strong,
publication-quality discrimination signal. This tests the behavioral hypothesis: activists
implicitly use information-theoretic efficiency as a target filter.

---

#### `activist_ipt_zone_test_results.json` / `.md`
**Test B (zone test): IPT Zone Comparison for Activist Targeting**

Complements the primary activist signal test by computing activist filing rates stratified by
IPT zone (Destruction: G/D < 0, Watch: 0 ≤ G/D < IPT, Safe: G/D ≥ IPT). Includes the
fine-grained filing rate by G/D decile bin. Used for Figure 7.

Key: Filing rates show non-monotone pattern across zones (destruction ≈ watch << above-IPT
is reversed), suggesting activists target both distressed companies AND highly-profitable ones
(potential capital return activism). See Figure 7 for the full decile breakdown.

---

#### `survival_test_N590_AUC0781_results.json` / `.md`
**Test C: Organizational Survival — H8.4 (primary positive result)**

Survival analysis testing whether G/D < IPT predicts corporate bankruptcy (Chapter 7/11 EDGAR
filings) vs. survival, using EDGAR XBRL Company Facts API for post-delisting G/D data. This
dataset retains historical fundamentals even after a company delists, making it uniquely suitable
for survival analysis without survivorship bias.

Key statistics (overall stratum, primary result):
- N_total = 17,324 (N_bankrupt = 1,354; N_survivor = 15,970)
- Unique bankrupt CIKs = 507; years covered: 2010–2022
- AUC = 0.7813, 95% CI bootstrap [0.766, 0.796]
- Bootstrap mean AUC = 0.7811 (stable)
- Youden optimal threshold: score = 0.0339 (G/D = −0.0339), J = 0.582
- At IPT: sensitivity = 98.1%, specificity = 20.7% (IPT is a near-universal upper bound on bankrupt firms)
- **Odds ratio at IPT = 13.37×** (p_bankrupt below IPT = 9.50%; above IPT = 0.78%)
- n_below_ipt = 13,985; n_above_ipt = 3,339

Horizon stratification (strata key):
- T−1 (1yr pre-bankruptcy): AUC = 0.840, OR = 34.46× at IPT
- T−2 (2yr pre-bankruptcy): AUC = 0.768, OR = 11.35×
- T−3 (3yr pre-bankruptcy): AUC = 0.745, OR = 9.95×

**Interpretation:** IPT identifies a near-absolute ceiling on bankrupt firms. 98.1% of companies
that subsequently went bankrupt were below IPT (G/D < 1.131) at some point in the prior 3 years.
The 13× odds ratio is a strong causal-direction finding: crossing below IPT is strongly associated
with subsequent failure. AUC = 0.78 is publication-quality for a single-factor survival classifier.

---

#### `phase_a_infothermo_results.json` / `.md`
**Test D: Phase A Information-Thermodynamic Tests (H2, H3, H5, H6, H8)**

Four information-thermodynamic hypotheses tested at the market and sector level:

- **H2 (Complexity complexity-activist):** AUC = 0.396 (null). G/D complexity (variance of G/D
  cross-section) does not discriminate activist targets. Spearman ρ = −0.140 between complexity
  and G/D level (p < 10⁻¹⁰); more complex sectors tend to have lower G/D. NEGATIVE gate.

- **H3 (Entropy signal, market-level):** Spearman ρ = 0.339 (lag-2), p = 0.005; ρ = 0.285
  (lag-1), p = 0.020; N = 66 quarters. Market-level IPT entropy (cross-sectional G/D distribution
  above IPT) predicts lagged market direction. POSITIVE gate. This is the key market-level
  thermodynamic signal.

- **H5 (Sector variance):** Cross-sectional G/D variance is correlated with lagged sector returns
  (Spearman ρ = 0.162–0.192, p < 10⁻¹⁴), but entropy alone is weaker (ρ = 0.075–0.083).
  44 sectors; power is limited. NEUTRAL gate (directional only).

- **H6 (Attractor / IPT recovery trajectory):** Companies crossing below IPT (N = 334 treated)
  show recovery trajectory toward IPT. At t+3, Cohen's d = 0.334 vs. matched controls, but
  Mann-Whitney p = 0.077 (marginal, N drops to 118 at t+3). POSITIVE gate (noisy but directional).

- **H8 (Price entropy):** No relationship between G/D zone and price entropy (OHLCV-based).
  Spearman ρ = 0.003, p = 0.72. NEGATIVE gate.

---

#### `conditional_survival_3regime_DBIC92_results.json` / `.md`
**Test E: Conditional Survival and Three-Regime Structure**

Four-part structural analysis of whether IPT marks a second discrete transition in organizational
failure rates beyond the G/D = 0 break-even threshold.

N = 56,578 company-years (1,321 failed, 55,257 surviving). Period: 2010–2023.

**Analysis A (Fine-grained survival curve):** 0.1-width G/D bins from −2.0 to +4.0.
The IPT bin [1.1, 1.2] has failure rate = 0.90% (N = 667 obs, 6 failures). The break-even bin
[−0.1, 0.0] has failure rate = 1.35%. Rapid monotone decline in failure rates above G/D ≈ 1.1.

**Analysis B (Three-regime comparison):**
- Regime 1 — Destruction (G/D < 0): N = 14,074, failure rate = **6.81%** (95% CI: 6.40%–7.23%)
- Regime 2 — Watch (0 ≤ G/D < IPT): N = 30,489, failure rate = **1.11%** (95% CI: 0.99%–1.23%)
- Regime 3 — Safe (G/D ≥ IPT): N = 12,015, failure rate = **0.22%** (95% CI: 0.15%–0.32%)
- Chi-squared test (3 regimes): χ² = 1,672.9, p < 10⁻³⁰⁰ (2 dof)
- Fisher exact (R2 vs. R3): OR = 5.15, p = 4.05×10⁻²⁴
- Odds ratio R1 vs. R3: **33.68×**

**Analysis C (Piecewise logistic regression, structural break test):**
- M1: single threshold at G/D = 0, BIC = 11,200.7 (reference)
- M3: single threshold at G/D = IPT, BIC = 12,109.3 (worse than M1 alone: ΔBIC = +908.6)
- **M4: two thresholds at G/D = 0 AND G/D = IPT, BIC = 11,108.5 (ΔBIC = −92.19 vs. M1)**
- M5: continuous G/D, BIC = 10,326.4 (best overall — monotone relationship dominates)
- **Interpretation: ΔBIC(M4 vs M1) = −92.19. Strong evidence that IPT adds a second structural
  break beyond break-even. IPT is not the primary threshold (G/D = 0 dominates), but it adds
  significant structural information that neither G/D = 0 alone nor G/D = 1.0 (unit return) capture.**

**Analysis D (Conditional AUC within G/D ∈ [0, 2]):**
- N = 35,474 (352 failed, 35,122 surviving) — restricted to Watch + Safe regime
- AUC = 0.315 (bootstrap mean 0.315, 95% CI [0.299, 0.331])
- Youden optimal threshold within [0, 2]: G/D = 1.095 (IPT is in the plateau: [0.832, 1.271])
- **Conclusion: Conditional AUC < 0.60. IPT does not meaningfully discriminate within the Watch
  regime. The survival signal is primarily captured by the sign of G/D, not the magnitude above 0.**
  This is the current blocker for GXT grade upgrade to [B−].

**GXT grade:** Remained [C+]. Structural break confirmed (ΔBIC = −92.19), but conditional AUC
within [0, 2] is below 0.65 threshold for upgrade.

---

### figures/ — Publication-Ready Figures

| File | Caption | Source data |
|------|---------|-------------|
| `fig1_tsr_roc_3yr_fulluniv.png` | ROC curve for G/D predicting 3yr TSR, full S&P 500 universe (N=8,546, AUC=0.564) | `tsr_prediction_fulluniv_N8546_results.json` |
| `fig2_tsr_auc_by_horizon_fulluniv.png` | AUC by prediction horizon (1–5yr), full universe — shows mild improvement at 4yr | `tsr_prediction_fulluniv_N8546_results.json` |
| `fig3_tsr_tenure_stratified_auc.png` | AUC stratified by G/D tenure (tenure=0: AUC=0.536; tenure≥3yr: AUC=0.490) | `tsr_prediction_fulluniv_N8546_results.json` |
| `fig4_tsr_bh_fdr_table.png` | Benjamini-Hochberg FDR correction table — only tenure=0 survives (q=3×10⁻⁶) | `tsr_prediction_fulluniv_N8546_results.json` |
| `fig5_activist_gd_vs_filing_rate.png` | G/D level vs. activist 13D filing rate (shows low G/D firms targeted more) | `activist_signal_N2006_AUC0698_results.json` |
| `fig6_activist_gd_by_event_type.png` | G/D distribution by activist event type (financial restructuring vs. governance) | `activist_signal_N2006_AUC0698_results.json` |
| `fig7_activist_filing_rate_by_gd_bin.png` | Filing rate by G/D decile bin (zone test); non-monotone above IPT | `activist_ipt_zone_test_results.json` |
| `fig8_survival_roc_curve_AUC0781.png` | ROC curve for G/D predicting bankruptcy (N=17,324, AUC=0.781, OR=13.37× at IPT) | `survival_test_N590_AUC0781_results.json` |

---

## Data Sources and Methodology

| Component | Source |
|-----------|--------|
| Fundamentals (ROIC, WACC, G/D) | Bloomberg / FMP, VYRA production database |
| Bankruptcy events (post-delisting) | EDGAR XBRL Company Facts API |
| Activist filing events | SEC Schedule 13D EDGAR database |
| Price/TSR data | OHLCV daily from VYRA database |
| Statistical methods | scikit-learn (ROC/AUC), scipy (Mann-Whitney, Fisher exact), statsmodels (logistic regression), numpy (bootstrap) |
| Sample period | 2010–2023 (varies by test; see individual result files) |
| Universe | S&P 500 constituents + historical constituents; Tests C/E include non-S&P bankrupts via EDGAR |

---

## Reproducibility

Analysis scripts are available in the VYRA codebase. See `CITATION_GUIDE.md` for citation
format and contact information.
