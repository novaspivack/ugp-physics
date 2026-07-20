# SPEC_580_PHA — Information-Thermodynamic Phase A Results

**Run date:** 2026-05-12  
**IPT constant:** 1.13091513

---

## H2: G/D Time-Series Complexity as Activist Signal

| Predictor | N | AUC | 95% CI | p-value (MW) |
|-----------|---|-----|--------|--------------|
| G/D level (baseline) | 2170 | 0.3960 | [0.3528–0.4458] | 1.00e+00 |
| G/D complexity | 2170 | 0.3232 | [0.2820–0.3648] | 1.00e+00 |
| G/D level + complexity | 2170 | 0.3204 | [0.2720–0.3684] | 1.00e+00 |

**ΔAUC (combined vs level):** -0.0756  
**Spearman(complexity, G/D):** ρ=-0.140  p=0.000

| Group | N | Mean complexity | Median complexity |
|-------|---|----------------|------------------|
| Activist targets | 149 | 0.3990 | 0.3601 |
| Controls | 2021 | 0.4686 | 0.4479 |

**Gate: NEGATIVE**  
> Gate criteria: POSITIVE if ΔAUC ≥ +0.02 AND complexity AUC > 0.55

## H3: Cross-Sectional G/D Entropy → Forward 13D Filing Frequency

| Lag | N quarters | Spearman ρ | p-value |
|-----|-----------|------------|---------|
| 1Q | 66 | 0.285 | 0.020 |
| 2Q | 66 | 0.339 | 0.005 |
| Both lags | 132 | 0.312 | 0.000 |

**Gate: POSITIVE**  
> Gate criteria: POSITIVE if |ρ| ≥ 0.30 AND p < 0.10

## H5: Sector-Level G/D Entropy → Sector Activist Filing Rates

| Lag | N obs | Variance ρ | p | Entropy ρ | p |
|-----|-------|-----------|---|-----------|---|
| 1Q | 2355 | 0.162 | 0.000 | 0.075 | 0.000 |
| 2Q | 2355 | 0.192 | 0.000 | 0.083 | 0.000 |

N sectors: 44  
**Power note:** CAUTION: 44 sectors; statistical power is limited. Results are directional only.

**Gate: NEUTRAL**  
> Gate criteria: POSITIVE if |ρ| ≥ 0.20 AND p < 0.15 (low-power test)

## H6: Post-Activist-Campaign G/D Recovery (Event Study)

N treated companies (G/D < IPT at 13D filing): **334**

| Horizon | N treated | N controls | ΔG/D treated | ΔG/D controls | Cohen's d | MW p |
|---------|-----------|------------|-------------|--------------|-----------|------|
| t+1 | 332 | 285 | 0.266 | 0.207 | 0.038 | 3.08e-01 |
| t+2 | 258 | 222 | 0.440 | 0.258 | 0.100 | 1.42e-01 |
| t+3 | 118 | 101 | 0.549 | 0.005 | 0.334 | 7.73e-02 |

**G/D trajectory for treated companies:**

| Horizon | N | Median G/D | % Above IPT |
|---------|---|-----------|------------|
| t0 | 334 | 0.008 | 0.0% |
| t+1 | 332 | 0.009 | 11.4% |
| t+2 | 258 | 0.024 | 19.0% |
| t+3 | 118 | 0.024 | 18.6% |

**Coverage note:** Coverage degrades for early filings (G/D data dense from 2015+). N drops significantly at t+3. Interpret with caution.

**Gate: POSITIVE**  
> Gate criteria: POSITIVE if Cohen's d ≥ 0.20 AND MW p < 0.10 at any horizon

## H8: Permutation Entropy of Price Returns by G/D Zone

N ticker-year records: **18695**

| Zone | N | Mean PE | Std PE | Median PE |
|------|---|---------|--------|-----------|
| destruction | 14306 | 0.9955 | 0.0100 | 0.9968 |
| zipf | 287 | 0.9960 | 0.0032 | 0.9969 |
| above_ipt | 4102 | 0.9958 | 0.0040 | 0.9969 |

**Mann-Whitney (destruction > above_ipt):** p=9.33e-01  Cohen's d=-0.026

**Partial Spearman (controlling volatility):** ρ=0.003  p=7.24e-01  N=18695

**Gate: NEGATIVE**  
> Gate criteria: POSITIVE if Cohen's d ≥ 0.15 AND MW p < 0.05

---

## Phase A Gate Summary

| Hypothesis | Gate | Key metric |
|------------|------|-----------|
| H2: G/D Complexity → Activist AUC | NEGATIVE | ΔAUC=-0.0756 |
| H3: Cross-sectional entropy → Filings | POSITIVE | Spearman ρ (best lag) |
| H5: Sector entropy → Sector filing rate | NEUTRAL | Limited power (N sectors) |
| H6: Post-campaign G/D recovery | POSITIVE | Event study Cohen's d |
| H8: Permutation entropy by G/D zone | NEGATIVE | Cohen's d, MW p |

*SPEC_580_PHA — Executed automatically by `scripts/run_spec580_phase_a_tests.py`*  
*Epic: EPIC_090_OEF | Physics: EPIC_043_GXT*