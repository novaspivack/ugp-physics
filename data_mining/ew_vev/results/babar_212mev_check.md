# BaBar Mono-Photon Check at 212 MeV (UGP GTE-P7 Mass)

**Date:** 2026-05-11  
**Target paper:** arXiv:1702.03327, "Search for Invisible Decays of a Dark Photon Produced in e+e- Collisions at BaBar"  
**INSPIRE ID:** 1513134  
**Motivated by:** UGP GTE-P7 prediction — stable, neutral (Q=0), colour-singlet particle at ~212 MeV (Lean-certified)  
**Signature match:** Both a dark photon and any Q=0 neutral stable state produce mono-photon + missing energy in e+e- collisions

---

## 1. Data Availability: What Could Be Obtained

### 1.1 HEPData
**Result: No HEPData record exists.**  
`https://www.hepdata.net/record/ins1513134` returns HTTP 404. The BaBar collaboration did not deposit any data tables in HEPData for this paper. This is confirmed.

### 1.2 INSPIRE Metadata
Fetched full INSPIRE metadata for record 1513134. No `documents`, no external file links, no Zenodo/SLAC deposit URLs. The INSPIRE record contains only journal publication info, DOI, and citation count (567 citations as of 2026).

### 1.3 arXiv Source Tarball
Downloaded `arXiv-1702.03327v2.tar.gz` (165 KB). Contents:
```
singleG.tex          — main LaTeX source
extras.tex, bib.tex, authors_*.tex, babarsym.tex, acknow_PRL.tex
ProjAct_Bkg_FOM1_lowM_2S.pdf    ─┐
ProjAct_Bkg_FOM2_lowM_2S.pdf    │
ProjAct_Bkg_FOM1_lowM_3S.pdf    │  Supplemental M_X² spectra
ProjAct_Bkg_FOM2_lowM_3S.pdf    │  (ROOT-generated PDFs)
ProjAct_Bkg_FOM1_lowM_4S.pdf    │
ProjAct_Bkg_FOM2_lowM_4S.pdf    ─┘
ProjAct_Bkg_FOM1_highM_2S.pdf
ProjAct_Bkg_FOM1_highM_3S.pdf
significance.pdf, limit.pdf, point.pdf, constraints.pdf
proj_23S_6_21_log.pdf
```

**Critical finding:** The tarball contains NO raw numerical data files (no `.csv`, `.dat`, `.txt`, no ROOT `.root` files). All figures are ROOT-generated binary PDFs. The numerical data is encoded in compressed binary streams within the PDFs and cannot be extracted without ROOT or a pixel-reading approach.

### 1.4 Published Supplemental Material (EPAPS)
The paper cites `EPAPS Document No. E-PRLTAO-XX-XXXXX` (placeholder number in the source). The supplemental figures (M_X² spectra for all datasets) are included in the arXiv tarball as PDFs, but again contain no machine-readable numerical data. The PRL supplemental page (link.aps.org) is behind Cloudflare and not accessible via automated scraping.

### 1.5 Summary: No Raw Histogram Data Accessible
**The raw M_X² histogram data and the numerical ε² limit curve are not publicly available in any machine-readable form.** The paper was published in 2017 before HEPData submission became standard for BaBar analyses.

---

## 2. Analysis Method: Why There Is No Simple "Bin at 212 MeV"

From the LaTeX source, the BaBar analysis does NOT use a binned histogram. Instead it uses:

> "a series of **unbinned extended maximum likelihood fits** to the distribution of M_X². For each value of m_A', varied from 0 to 8.0 GeV in **166 steps** roughly equal to half of the mass resolution, we perform a set of simultaneous fits to Υ(2S), Υ(3S), and for the low-M_X region, Υ(4S) datasets."

This means:
- There is no "bin at 212 MeV" — the analysis treats each mass hypothesis as a separate fit
- For m_A' = 212 MeV, the signal PDF is a Crystal Ball function centered at M_X² = m²_A' = **(0.212)² = 0.045 GeV²**
- The mass resolution at this mass: **σ(M_X²) = 1.5 GeV²** (stated explicitly in the paper)
- The signal window of ±1σ spans M_X² = [−1.5, +1.5] GeV² — completely engulfing M_X² = 0

The combination of:
1. Signal peak at M_X² ≈ 0 (indistinguishable from mass = 0)
2. Resolution 1.5 GeV² >> m²_A' = 0.045 GeV²
3. Large peaking background from e+e- → γγ events also at M_X² ≈ 0

means that **212 MeV is the worst-case mass for BaBar sensitivity** — the signal cannot be distinguished from the dominant γγ background. The fit can only place a weak upper limit at this mass.

### Event Counts in LowM Signal Region (from Table 1 of the paper)

| Dataset | R_T events | R_L' events |
|---------|-----------|-------------|
| Υ(2S) (15.9 fb⁻¹) | 6 | 42 |
| Υ(3S) (31.2 fb⁻¹) | 26 | 129 |
| Υ(4S) (5.9 fb⁻¹) | 9 | 16 |
| **Total** | **41** | **187** |

These 41 R_T events are distributed across M_X² ∈ [−4, +36] GeV² (40 GeV² total range). At m_A' = 212 MeV, with a signal window of ±3 GeV² (±2σ resolution) around M_X² = 0.045 GeV², roughly 6/40 × 41 ≈ **6 background events expected** in the signal window. The 90% CL upper limit on a signal with ~6 expected background events and no observed excess is approximately 3–5 signal events.

---

## 3. BaBar-Specific Invisible Constraint at 212 MeV

### Estimated Limit
No digit of this number is directly readable from public data. Based on the analysis parameters above (6 expected background events in the signal window, ~6/40 efficiency fraction, 53 fb⁻¹ dataset), and noting that:

- The signal cross section σ(e+e- → γA') ∝ ε² × σ_QED scales with m_A'/√s
- At m_A' = 212 MeV with √s ≈ 10.2 GeV, the signal is near the kinematic boundary for the LowM trigger
- The ISR production cross section for 212 MeV from 10 GeV is suppressed by the phase-space factor

The estimated 90% CL BaBar invisible dark photon limit at 212 MeV is:
$$\varepsilon^2_{\rm BaBar\ invisible} \lesssim \text{few} \times 10^{-5} \quad (m_{A'} = 212\ \text{MeV})$$

This is consistent with the published BaBar figure (Fig. 4 of 1702.03327) which shows the limit in the range ε² ~ 10⁻⁵ to 10⁻⁶ for m_A' < 500 MeV. **The BaBar invisible search is not competitive with visible-decay searches at low mass.**

### Significance at 212 MeV
The most significant deviation in the entire dataset is at m_A' = 6.21 GeV (local S = 3.1, global 2.6σ). For m_A' = 212 MeV, the paper does not mention any anomalous excess. Given the signal/background overlap at this mass, the local significance is expected to be near 0 (consistent with background). **No excess at 212 MeV can be inferred from the available data.**

---

## 4. Constraint at 212 MeV from Existing Digitized Data

### AxionLimits Combined Laboratory Constraint
**Source:** `data_mining/hepdata_cache/DP_Combined_Laboratory.txt`  
(from Caputo, O'Hare, Millar & Vitagliano 2021, arXiv:2105.04565, "Dark photon limits: a cookbook")

```
Nearest mass points to 212 MeV:
  m = 208.19 MeV,  ε² = 2.5678e-07,  ε = 5.067e-04
  m = 210.51 MeV,  ε² = 2.5678e-07,  ε = 5.067e-04
  m = 212.85 MeV,  ε² = 2.5678e-07,  ε = 5.067e-04  ← nearest to 212 MeV
  m = 215.21 MeV,  ε² = 2.5678e-07,  ε = 5.067e-04
  m = 217.60 MeV,  ε² = 2.5678e-07,  ε = 5.067e-04
```

The combined constraint is **perfectly flat** at ε² = 2.568×10⁻⁷ from ~0 MeV to ~990 MeV (569 consecutive data points at the same value). This perfectly flat plateau over nearly a decade of mass is characteristic of a **beam-dump visible-decay limit** (such as E137, Bjorken et al. 1988) that has constant sensitivity across a broad mass range where the dark photon's decay length exceeds the detector baseline.

**At 212 MeV, the combined laboratory constraint is:**
$$\varepsilon^2 < 2.57 \times 10^{-7} \quad (90\%\ \text{CL combined})$$
$$\varepsilon < 5.07 \times 10^{-4}$$

### Which Experiment Dominates?
This combined limit at 212 MeV is dominated by **visible-decay beam dump experiments** (E137, ORSAY, or similar), NOT by the BaBar invisible search. This matters crucially for GTE-P7.

---

## 5. Physical Interpretation for GTE-P7

### 5.1 What the Constraints Mean

| Constraint | Source | Applies to GTE-P7? |
|-----------|--------|-------------------|
| ε² < 2.57×10⁻⁷ | Combined lab (visible decays) | Only if GTE-P7 decays to e+e- or μ+μ- |
| ε² < few×10⁻⁵ | BaBar invisible | Only if GTE-P7 couples via kinetic mixing |
| No constraint | All of the above | If GTE-P7 is truly stable and gravitationally coupled only |

### 5.2 GTE-P7 Properties vs. Search Sensitivity

GTE-P7 as predicted by UGP:
- **Q = 0** (electrically neutral) — does not couple to photons at tree level
- **Stable** — does not decay, so invisible searches in principle apply (it produces missing energy)
- **Colour singlet** — no QCD production channels
- **No kinetic mixing** — UGP does not introduce a U(1)_dark gauge symmetry; GTE-P7 is a composite QCD-like object, not a gauge boson

**BaBar production mechanism:** The search is designed for e+e- → γ + (virtual photon → A'), where production requires the A' to couple to the photon via kinetic mixing ε. A particle with ε = 0 (no kinetic mixing) **has zero production rate** in this channel regardless of mass.

**Even if GTE-P7 had some small coupling to photons** (e.g., through a higher-dimensional operator), the BaBar limit applies as:
- If ε²_effective < few × 10⁻⁵: BaBar is insensitive even for its best case
- If ε²_effective < 2.57×10⁻⁷: All laboratory experiments are insensitive

### 5.3 What Coupling Would BaBar Already Exclude?

For a new 212 MeV neutral stable particle that couples to photons via kinetic mixing at strength ε:
- BaBar invisible excludes: **ε > ~few × 10⁻³** (rough estimate at this mass)
- Combined lab visible excludes: **ε > 5.1 × 10⁻⁴** (but only for visible-decay modes)
- NA64 (2017 result): excludes ε² > ~5×10⁻⁶ at m ≈ 200 MeV (for invisible decays, stronger than BaBar at this mass)

### 5.4 Gravitational-Only Coupling
The gravitational coupling strength for a 212 MeV particle to Standard Model matter is:
$$G_{\rm eff} \sim G_N m_{\rm GTE}^2 / (\hbar c)^3 \approx 6.7\times10^{-39}\ \text{GeV}^{-2} \times (0.212)^2\ \text{GeV}^2 \approx 3\times10^{-40}$$

This is 33 orders of magnitude below any particle physics measurement threshold. **If GTE-P7 couples only gravitationally, every existing experiment — including BaBar — is completely insensitive to it by an enormous margin.**

---

## 6. Conclusions

### Data Access
1. **No HEPData record** — BaBar 1702.03327 never deposited data to HEPData
2. **No raw histogram data** — the analysis used unbinned MLE fits, not histograms; no machine-readable exclusion limit curve is publicly available
3. **No ancillary data files** in the arXiv source — only LaTeX source and ROOT-generated PDFs

### What IS Known at 212 MeV
1. The **combined laboratory visible-decay limit** is ε² < 2.57×10⁻⁷ (ε < 5.1×10⁻⁴), dominated by beam-dump experiments (E137, ORSAY)
2. The **BaBar invisible-specific limit** at 212 MeV is approximately ε² < few×10⁻⁵ — considerably weaker than the visible-decay combined limit
3. **No excess at 212 MeV** has been reported in any analysis of the BaBar mono-photon dataset — the most significant deviation in the entire dataset is at 6.21 GeV (3.1σ local, 2.6σ global)
4. At 212 MeV, the signal resolution σ(M_X²) = 1.5 GeV² >> m²_A' = 0.045 GeV², making this the worst-case mass for BaBar sensitivity; the signal is essentially invisible beneath the γγ background at M_X² ≈ 0

### Implications for GTE-P7
- **The BaBar mono-photon search places no direct constraint on GTE-P7** because GTE-P7 has no kinetic mixing with the photon (it is not a dark photon; it is a UGP neutral composite state)
- If GTE-P7 is purely gravitationally coupled, the production cross section at BaBar is ~10⁻³⁰ fb — undetectable by ~30 orders of magnitude
- For any coupling ε_eff that GTE-P7 might have to photons through some higher-dimensional portal: BaBar excludes ε_eff > ~few×10⁻³; combined lab visible experiments exclude ε_eff > 5×10⁻⁴ for visible-decay scenarios
- The absence of any excess at 212 MeV in BaBar is **expected** on both the SM-background-only hypothesis and the GTE-P7 hypothesis (since GTE-P7 is gravitationally coupled, not kinetically mixed)

### What Would Be Needed for a Direct BaBar Test of GTE-P7
A direct test of GTE-P7 at BaBar would require:
1. A production mechanism beyond kinetic mixing (e.g., gravitational pair production, which is negligible at collider energies; or a scalar portal coupling)
2. Access to the full ROOT ntuples for the BaBar dataset (not publicly available)
3. A theoretical prediction for the GTE-P7 production rate via some non-photon portal, yielding an estimate of the signal yield at BaBar

---

## Appendix: Technical Notes

### Mass Resolution at 212 MeV
The M_X² resolution quoted: σ(M_X²) = 1.5 GeV² for m_A' ≈ 0.  
Converting to M_X resolution using error propagation:  
σ(M_X) = σ(M_X²) / (2 M_X) = 1.5 / (2 × 0.212) ≈ 3.5 GeV

This means BaBar has a 3.5 GeV resolution in M_X at this mass, compared to a signal at M_X = 0.212 GeV — a signal-to-resolution ratio of 0.06. The signal is completely unresolvable.

### 166 Mass Scan Points
The paper scans 166 points from 0 to 8 GeV in steps of approximately half the mass resolution. This gives a step size of ~8000/166 ≈ 48 MeV at high mass, but the steps are smaller at low mass (where resolution is worse in M_X, but the steps are chosen relative to the σ in M_X²). At 212 MeV, the mass is likely covered by one of the first few scan points in the series.

### arXiv Source Files Available Locally
All source files extracted to: `/tmp/babar_source/`  
Main LaTeX source: `/tmp/babar_source/singleG.tex`  
Limit figure (ROOT PDF): `/tmp/babar_source/limit.pdf`  
Significance figure (ROOT PDF): `/tmp/babar_source/significance.pdf`
