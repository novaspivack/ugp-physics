# SPEC_576_ACT — G/D as Activist Targeting Signal

**Run date:** 2026-05-11  
**IPT:** 1.130915  
**Source:** `scripts/run_spec576_activist_signal.py`  

---

## Summary

| Test | Result |
|---|---|
| Test 1: AUC (G/D → 13D filing) | 0.6977 (best window) |
| Test 2: Max |Spearman ρ| (G/D vs screener) | 0.2600 |
| Test 3: CEO change directional check | insufficient_data |
| Test 4: Outcome analysis | ok |
| Decision gate | **PROCEED_CORRELATED** |

**G/D predicts activist filings (AUC=0.6977 > 0.55) AND correlates with screener scores (|ρ|=0.2600 > 0.20). G/D captures related variance — propose SPEC_577 to add gd_ratio as a component (multiplier or factor) in catalyst_probability.**

---

## Test 1: G/D as Leading Indicator of SC 13D Filings

### Lookback window: 1yr
- N total: 2017 (filed=113, control=1904)
- AUC: **0.6787** [0.6154–0.7420] (95% CI, bootstrap N=2000)
- Mann-Whitney p (filed < control G/D): 0.0000
- Median G/D: filed=0.026, control=0.841

### Lookback window: 2yr
- N total: 2006 (filed=102, control=1904)
- AUC: **0.6977** [0.6311–0.7634] (95% CI, bootstrap N=2000)
- Mann-Whitney p (filed < control G/D): 0.0000
- Median G/D: filed=0.027, control=0.841

### Lookback window: 3yr
- N total: 1991 (filed=87, control=1904)
- AUC: **0.6294** [0.5569–0.7015] (95% CI, bootstrap N=2000)
- Mann-Whitney p (filed < control G/D): 0.0000
- Median G/D: filed=0.055, control=0.841

### Filing rates by G/D zone

| Zone | N tickers | Filed | Rate | 95% CI |
|---|---|---|---|---|
| destruction | 1361 | 80 | 5.9% | 4.8%–7.3% |
| zipf | 69 | 4 | 5.8% | 2.3%–14.0% |
| above_ipt | 614 | 55 | 9.0% | 7.0%–11.5% |

Chi-squared test: χ²=6.445, p=0.0399

---

## Test 2: G/D vs Vyra Activist Screener Scores

N tickers joined: 2021

| Screener dimension | Spearman ρ | p-value | N |
|---|---|---|---|
| Catalyst probability | +0.0140 | 0.532090 | 1989 |
| Governance receptivity | +0.2072 | 0.000000 | 2021 |
| Execution intent (low = management not executing) | +nan | nan | 2021 |
| Total value gap (TSR pp) | -0.2600 | 0.000000 | 2021 |
| Economic activatability | +0.0529 | 0.018276 | 1989 |
| Credible opportunity score | -0.0246 | 0.268361 | 2019 |

Max |ρ|: 0.2600

---

## Test 3: G/D vs CEO/Leadership Changes

**Status:** insufficient_data

> executive_tenure has only 45 tickers; results are descriptive only


---

## Test 4: G/D vs Strategic Events / Campaign Outcomes

### Campaign outcomes (resolved campaigns only)

Outcome counts: {'positive': 102}

| Outcome | N | Median G/D | % below 1.0 | % Zipf | % Above IPT |
|---|---|---|---|---|---|
| positive | 101 | 0.031 | 75% | 2% | 23% |

### Quasi-delisted tickers (last trade < 2026-01-01)

| Ticker | Last trading date | Last G/D | Zone |
|---|---|---|---|
| PDLI | 2020-12-29 | 0.136 | destruction |
| SBT | 2025-03-30 | no G/D data | N/A |

---

## Decision Gate

| Gate | Value | Threshold | Pass? |
|---|---|---|---|
| Test 1 best AUC | 0.6977 | > 0.55 | ✅ YES |
| Test 2 max |ρ| | 0.2600 | > 0.20 | ✅ YES |

**Outcome: PROCEED_CORRELATED**

G/D predicts activist filings (AUC=0.6977 > 0.55) AND correlates with screener scores (|ρ|=0.2600 > 0.20). G/D captures related variance — propose SPEC_577 to add gd_ratio as a component (multiplier or factor) in catalyst_probability.
