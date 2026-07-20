# LaTeX Integration Guide: TE_2.4 Phase 1 Figures

**Date:** November 20, 2025  
**Purpose:** Guide for integrating Phase 1 figures into MFRR monograph

---

## Generated Figures

All figures are available in both PNG (high-res) and PDF (vector) formats:

### 1. Field Profiles (`field_profiles.[png,pdf]`)
- **Size:** 33 KB (PDF), 414 KB (PNG)
- **Resolution:** 300 DPI
- **Dimensions:** 12" × 10"
- **Content:** 2×2 grid showing φ(x), Ψ(x), g_tt(x), g_xx(x)
- **Purpose:** Visualize background configuration of 1+1D JT gravity + Ψ

### 2. Scaling Laws (`scaling_laws.[png,pdf]`)
- **Size:** 34 KB (PDF), 339 KB (PNG)
- **Resolution:** 300 DPI
- **Dimensions:** 14" × 5"
- **Content:** (a) x_H vs M, (b) T_H vs 1/M with fits
- **Purpose:** Validate black hole thermodynamics (x_H ∝ M, T_H ∝ 1/M)

### 3. Mode Spectrum (`mode_spectrum.[png,pdf]`)
- **Size:** 33 KB (PDF), 385 KB (PNG)
- **Resolution:** 300 DPI
- **Dimensions:** 14" × 5"
- **Content:** (a) ω_n vs n for different masses, (b) universal data collapse
- **Purpose:** Demonstrate harmonic oscillator quantization

### 4. Error Distributions (`error_distributions.[png,pdf]`)
- **Size:** 47 KB (PDF), 396 KB (PNG)
- **Resolution:** 300 DPI
- **Dimensions:** 12" × 10"
- **Content:** Error histograms and parameter dependence
- **Purpose:** Quantify numerical accuracy across parameter space

### 5. Runtime Analysis (`runtime_analysis.[png,pdf]`)
- **Size:** 25 KB (PDF), 185 KB (PNG)
- **Resolution:** 300 DPI
- **Dimensions:** 14" × 5"
- **Content:** Computational cost vs. M and m²
- **Purpose:** Demonstrate computational efficiency

---

## LaTeX Integration Examples

### Basic Figure Inclusion

```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.9\textwidth]{TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/results/figures/field_profiles.pdf}
    \caption{Background configuration for 1+1D JT gravity + coherence field. 
    (a) Dilaton field φ(x) approaches Schwarzschild-like profile. 
    (b) Coherence field Ψ(x) shows Gaussian perturbation near horizon. 
    (c,d) Metric components g_tt and g_xx exhibit expected black hole behavior. 
    Red dashed line marks horizon at x_H = 20.29 Planck lengths.}
    \label{fig:te24_field_profiles}
\end{figure}
```

### Side-by-Side Subfigures

```latex
\begin{figure}[htbp]
    \centering
    \begin{subfigure}[b]{0.48\textwidth}
        \includegraphics[width=\textwidth]{TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/results/figures/scaling_laws.pdf}
        \caption{Scaling law validation}
        \label{fig:te24_scaling}
    \end{subfigure}
    \hfill
    \begin{subfigure}[b]{0.48\textwidth}
        \includegraphics[width=\textwidth]{TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/results/figures/mode_spectrum.pdf}
        \caption{Mode quantization}
        \label{fig:te24_modes}
    \end{subfigure}
    \caption{TE_2.4 Phase 1 validation: (a) Black hole thermodynamics scaling laws 
    show excellent agreement with theory (x_H ∝ M, T_H ∝ 1/M). 
    (b) Near-horizon modes exhibit harmonic oscillator spectrum with universal 
    data collapse ω_n/(πT_H) = n + 1/2.}
    \label{fig:te24_validation}
\end{figure}
```

### Full-Page Figure

```latex
\begin{figure}[p]
    \centering
    \includegraphics[width=\textwidth,height=0.9\textheight,keepaspectratio]{TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/results/figures/error_distributions.pdf}
    \caption{Parameter sweep error analysis. 
    (a) Horizon location error histogram shows mean 2.44\% ± 1.64\%. 
    (b) Error vs. coherence mass reveals expected backreaction for heavier fields. 
    (c) Self-coupling has negligible effect in weak coupling regime. 
    (d) Summary statistics confirm 100\% success rate and production readiness.}
    \label{fig:te24_errors}
\end{figure}
```

---

## Recommended Placement in MFRR Monograph

### Option 1: New Section in Part V (TE_2 Advanced Explorations)

```latex
\section{TE₂.4: Reflexive Quantum Gravity + Black-Hole Unitarity}
\label{sec:te24}

\subsection{Phase 1: 1+1D Toy Model}

We construct a simplified 1+1D Jackiw-Teitelboim (JT) dilaton gravity model 
coupled to the coherence field Ψ from TE₁.C. This analytically tractable 
setting allows explicit computation of horizon dynamics, Hawking temperature, 
and near-horizon mode quantization.

\subsubsection{Background Configuration}

The system is described by the action
\begin{equation}
    S = \int dx\,dt \left[ \phi R + (\nabla\Psi)^2 + V(\Psi) \right],
\end{equation}
where φ is the dilaton field, R is the 2D Ricci scalar, and 
V(Ψ) = \tfrac{1}{2}m^2\Psi^2 + \tfrac{1}{4}\lambda\Psi^4.

Figure~\ref{fig:te24_field_profiles} shows the converged background 
configuration for a black hole of mass M = 10 M_Planck...

\subsubsection{Scaling Law Validation}

Figure~\ref{fig:te24_validation} demonstrates that the numerical 
implementation correctly reproduces black hole thermodynamics...

\subsubsection{Parameter Sweep}

To validate robustness, we tested 10 configurations spanning 
M ∈ [5,50] M_Planck, m² ∈ [0.01,0.5] Planck⁻², and λ ∈ [0.001,0.1]. 
Figure~\ref{fig:te24_errors} shows that all configurations converged 
with mean horizon error 2.44\% and perfect temperature agreement...
```

### Option 2: Appendix (Computational Validation)

```latex
\appendix
\section{TE₂.4 Phase 1: Computational Validation}
\label{app:te24_phase1}

This appendix documents the computational validation of the 1+1D 
JT gravity + coherence field toy model used in TE₂.4...

\subsection{Field Profiles}
See Figure~\ref{fig:te24_field_profiles}...

\subsection{Scaling Laws}
See Figure~\ref{fig:te24_scaling}...

\subsection{Error Analysis}
See Figure~\ref{fig:te24_errors}...
```

---

## Caption Templates

### Field Profiles
```latex
\caption{Background configuration for 1+1D JT gravity + coherence field 
with M = 10 M_Planck, m² = 0.1, λ = 0.01. 
(a) Dilaton field φ(x) crosses 2M threshold at horizon (red dashed line). 
(b) Coherence field Ψ(x) shows localized perturbation. 
(c) Timelike metric component g_tt(x) vanishes at horizon. 
(d) Spacelike metric component g_xx(x) diverges at horizon. 
All quantities in Planck units.}
```

### Scaling Laws
```latex
\caption{Black hole thermodynamics scaling law validation. 
(a) Horizon location scales linearly with mass: x_H = (2.058 ± 0.058)M 
(blue points: numerical; red dashed: fit; green dotted: theory x_H = 2M). 
(b) Hawking temperature scales inversely with mass: 
T_H = (0.039789 ± 0.000001)/M 
(red points: numerical; blue dashed: fit; green dotted: theory T_H = 1/(8πM)). 
Both scaling laws agree with theory to within 3\%.}
```

### Mode Spectrum
```latex
\caption{Near-horizon mode quantization exhibits harmonic oscillator spectrum. 
(a) Mode frequencies ω_n for different black hole masses M ∈ [5,50] M_Planck 
(solid lines: numerical; dashed lines: theory ω_n = (n+½)πT_H). 
(b) Universal data collapse: normalized frequencies ω_n/(πT_H) = n + ½ 
independent of M (colored points: numerical for different masses; 
black dashed: universal curve). 
Perfect agreement validates thermal quantization.}
```

### Error Distributions
```latex
\caption{Parameter sweep error analysis across 10 configurations. 
(a) Horizon location error histogram: mean 2.44\% ± 1.64\%, 
all within 7.07\% (red dashed: mean). 
(b) Error vs. mass and coherence field mass m²: 
heavier fields (m² = 0.5) show larger backreaction as expected. 
(c) Error vs. mass and self-coupling λ: 
weak coupling regime (λ ≤ 0.1) shows no λ dependence. 
(d) Summary statistics: 100\% success rate, all criteria passed, 
model production-ready.}
```

### Runtime Analysis
```latex
\caption{Computational efficiency analysis. 
(a) Runtime vs. black hole mass M: approximately constant ~0.03s 
across M ∈ [5,50] M_Planck (red dashed: mean). 
(b) Runtime vs. coherence field mass m²: weak dependence, 
slight increase for heavier fields due to stiffness (red dashed: mean). 
All configurations complete in < 0.1s on 10-core Mac, 
demonstrating excellent scalability for Phase 2.}
```

---

## File Paths

All figures are located in:
```
TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/results/figures/
```

Relative to MFRR monograph root:
```
./TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/results/figures/
```

---

## LaTeX Preamble Requirements

Ensure your LaTeX document includes:

```latex
\usepackage{graphicx}  % For \includegraphics
\usepackage{subcaption}  % For subfigures (if using)
\usepackage{float}  % For [H] placement (if needed)

% Optional: set graphics path
\graphicspath{{./}{./TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/results/figures/}}
```

---

## Figure Quality Notes

1. **PDF vs PNG:**
   - Use **PDF** for LaTeX (vector graphics, scalable)
   - Use **PNG** for presentations or web (raster, fixed resolution)

2. **Resolution:**
   - All PNG figures: 300 DPI (publication quality)
   - PDF figures: vector (infinite resolution)

3. **File Sizes:**
   - PDF: 25-47 KB (very small, fast compilation)
   - PNG: 185-414 KB (reasonable for high-res)

4. **Colors:**
   - All figures use colorblind-friendly palettes
   - Grayscale-compatible (for B&W printing)

5. **Fonts:**
   - Default serif font (compatible with LaTeX)
   - Font size 10-13pt (readable at various scales)

---

## Cross-References

When referencing figures in text:

```latex
As shown in Figure~\ref{fig:te24_field_profiles}, the dilaton field...

The scaling laws (Figure~\ref{fig:te24_validation}a,b) validate...

Parameter sweep results (Figure~\ref{fig:te24_errors}) demonstrate...
```

---

## Compilation Notes

1. **First compilation:** LaTeX may show warnings about missing figures
2. **Run twice:** Ensures all references resolve correctly
3. **PDF output:** Figures will be embedded as vector graphics
4. **File size:** Expect ~200 KB increase in PDF size (all 5 figures)

---

## Example: Complete Figure Block

```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.95\textwidth]{TE_2_Advanced_Explorations/TE_2_4_BH_Unitarity/results/figures/field_profiles.pdf}
    \caption{%
        \textbf{Background configuration for 1+1D JT gravity + coherence field.}
        Numerical solution for M = 10 M_Planck, m² = 0.1, λ = 0.01 at t = 50 
        (all quantities in Planck units).
        \textbf{(a)} Dilaton field φ(x) approaches Schwarzschild-like profile, 
        crossing 2M threshold (gray dotted) at horizon x_H = 20.29 (red dashed).
        \textbf{(b)} Coherence field Ψ(x) shows Gaussian perturbation localized 
        near horizon, with small amplitude (~0.1) ensuring weak backreaction.
        \textbf{(c)} Timelike metric component g_tt(x) vanishes at horizon, 
        consistent with black hole event horizon.
        \textbf{(d)} Spacelike metric component g_xx(x) diverges at horizon, 
        indicating coordinate singularity.
        Integration converged cleanly with rtol = 10⁻⁸, atol = 10⁻¹⁰ in 0.04s.
    }
    \label{fig:te24_field_profiles}
\end{figure}
```

---

## Summary

✅ **5 figures generated** (PNG + PDF)  
✅ **Publication quality** (300 DPI, vector graphics)  
✅ **LaTeX-ready** (proper sizing, fonts, colors)  
✅ **Documented** (captions, placement, cross-refs)  
✅ **Validated** (all data from successful Phase 1 runs)

**Ready for immediate integration into MFRR monograph!**

---

**Last Updated:** November 20, 2025  
**Status:** ✅ Complete  
**Next Step:** Integrate into Mathematical_Foundations_of_Reflexive_Reality.tex

