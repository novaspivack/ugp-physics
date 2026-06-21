# Paper Outline — The Information Profit Principle

**Full title:** The Information Profit Principle: Derivation and Computational Validation of a Threshold Condition for Self-Maintaining Reflexive Systems

---

## Abstract

Derivation of IPT = 1 + Lambda/2 from PSC + Reflexive Landauer Bound.
Three simulation-only validations (TE1.H, TE2.1, E4).
Biological/economic connections explicitly labeled conjectural.

---

## 1. Introduction

- Motivating problem: informational viability of reflexive self-maintaining systems
- The MFRR framework: PSC requirement and Reflexive Landauer Bound as structural inputs
- Statement of main result: IPT = 1 + ln(phi) / (2 ln(2*pi)) ≈ 1.1309
- Scope and claims paragraph (model-internal derivation; no experimental validation; interpretive connections are conjectural)
- Paper organization

---

## 2. Theoretical Framework

### 2.1 Reflexive Systems and PSC

- Definition: reflexive system = state space + self-model field Psi + PT adjudication mechanism
- PSC requirement: iterative closure of self-model update operator F
- Definition 2.1: Information Generation G and Drain D
- Definition 2.2: Profit ratio rho = G/D

### 2.2 The Reflexive Landauer Bound

- Classical Landauer bound (Landauer 1961)
- MFRR extension: coherence field Psi incurs additional energy E_Psi
- Theorem 2.1 (Reflexive Landauer Bound): Delta E_PT >= k_B T ln(n) + lambda_Psi E_Psi
- Role of the coherence coupling constant lambda_Psi

---

## 3. Derivation of the Information Profit Threshold

### 3.1 Setting Up the Energy Balance

- Drain rate: D_dot = nu * Delta E_PT >= nu (k_B T ln(n) + lambda_Psi E_Psi)
- Viability condition: rho >= 1

### 3.2 PSC Convergence Overhead

- Lemma 3.1 (PSC convergence surplus): delta_PSC = ln(phi) / (2 ln(2*pi))
- Golden-ratio factor: optimal contraction kappa* = 1/phi for two-step predict-correct PSC update
- 2*pi normalization: PT phase space has natural 2*pi-periodic structure; ln(2*pi) is angular information normalization
- The 1/2 prefactor: forward vs. backward pass attribution

### 3.3 The Information Profit Threshold

- Theorem 3.1 (IPT): rho > IPT iff system has energy budget for coherent self-referential processing within MFRR model
- Equation: IPT = 1 + Lambda/2, Lambda = ln(phi)/ln(2*pi)
- Remark 3.1: Why phi and 2*pi — structural necessity, not numerology
- Remark 3.2: Necessary and sufficient only within stated model assumptions

### 3.4 Algebraic Verification

- Numerical values to 6 decimal places: phi, ln(phi), ln(2*pi), Lambda, Lambda/2, IPT
- Compact approximation IPT ≈ 1.13 accurate to three significant figures

---

## 4. Computational Validation

*Preamble: all experiments are simulation-only, internal consistency tests within the MFRR framework. No biological or economic data.*

### 4.1 TE1.H: 2D Toy Field Simulator

- Setup: 64x64 2D field, sinusoidal generation, exponential drain, Levin-style noise
- Coherence measure: C = 1 - r_zlib (gzip compression ratio proxy)
- Three scenarios: Unprofitable (rho ≈ 0.80), Profitable (rho ≈ 1.40), High Noise (rho < 1.00)
- Results table: C_0, C_T, Delta-C/step for each scenario
- Supercritical scenario only one with positive coherence slope
- Limitations: three scenarios, single run per scenario, compressed-size proxy

### 4.2 TE2.1: Evolutionary Neural-Agent Genesis

- Setup: neural agents in 2D resource grid, selection for positive profit
- 124 genesis runs; profit ratio accumulated over agent lifetime
- Results table: total runs, supercritical count, range, mean (supercritical and overall)
- Sweep: 72 runs over metabolic cost x decay rate grid; 14/72 above threshold
- Limitations: simplified neural controllers, heuristic mapping to MFRR constructs

### 4.3 E4: Reflexive Landauer Inequality Verification

- Setup: 50 randomized configurations, smooth 32x32 coherence field, random PT parameters
- PT cost modeled with difficulty factor epsilon >= 0
- Results table: pass rate, min/max/mean margin
- Interpretation: internal consistency check on energy model, not Gen/Drain threshold test
- Limitations: 100% pass rate is structurally expected; informative quantity is margin distribution

---

## 5. Discussion

### 5.1 Relation to Prigogine Dissipative Structures

- Complementary but not identical: IPT specifies informational minimum excess for reflexive systems; Prigogine characterizes broader macroscopic self-organization

### 5.2 Relation to Classical Landauer Erasure

- Classical case lambda_Psi = 0 collapses IPT to 1 (bare viability); reflexive overhead generates the gap Lambda/2 ≈ 0.1309

### 5.3 Conjectural Connections to Biology and Economics

- **Explicitly speculative:** no data collected or analyzed
- Metabolic cells and ATP ratios as possible analogue
- Economic investment/depreciation as possible analogue
- Three reasons these remain conjectural: mapping gap, PSC applicability, lack of empirical data
- Offered as motivation for future work only

---

## 6. Falsification and Open Questions

- Falsification criterion F1 (theoretical): proof that PSC surplus coefficient is not ln(phi)/(2 ln(2*pi))
- Falsification criterion F2 (computational): MFRR-compliant simulation with coherence growth at rho ≤ IPT or collapse at rho > IPT
- Open questions:
  - Derivation of lambda_Psi from MFRR axioms
  - Finite-time corrections to IPT
  - Multi-agent network generalizations
  - Stochastic fluctuation regime

---

## 7. Conclusion

- IPT = 1 + ln(phi)/(2 ln(2*pi)) ≈ 1.1309 derived from PSC + Reflexive Landauer Bound
- phi from golden-ratio optimality of two-step fixed-point recursion; 2*pi from phase-space periodicity
- Three simulation validations: TE1.H coherence growth, TE2.1 survivor population, E4 non-degeneracy
- All results are simulation-internal; physical/biological experiments remain future work
- Concrete falsification criterion and open quantitative research program

---

## Appendix A: Derivation Details

### A.1 Notation and Setup

- Reflexive system S, self-model field Psi, domain U, temperature T, coupling lambda_Psi
- E_Psi definition; Reflexive Landauer Bound restatement

### A.2 Derivation of Lemma 3.1 (PSC Convergence Surplus)

- Step 1: PSC as fixed-point iteration; optimal contraction kappa* = 1/phi
- Step 2: Energy overhead from convergence at rate ln(phi) per step
- Step 3: Phase-space normalization; ln(2*pi) as natural unit
- Step 4: 1/2 prefactor from forward/backward pass split
- Step 5: Threshold follows

---

## Appendix B: Simulation Methodology

### B.1 TE1.H Parameters and Implementation

- Grid: 64x64, 400 steps, single seed per scenario
- Generation: sinusoidal injection; Drain: exponential decay; Noise: uniform per-cell
- Exact parameter values for each of the three scenarios

### B.2 TE2.1 Evolutionary Experiment

- Neural agent architecture; 2D discrete resource grid; fitness definition
- Genesis experiment: 124 runs, parameter ranges
- Sweep experiment: 4x6 metabolic cost x decay rate grid, 3 seeds per point, 40 generations, 600 frames

### B.3 E4 Energy Model Consistency Check

- 50 independent configurations; smooth field generation (Gaussian filter sigma=2.0)
- Parameter distributions: n in {2,...,8}, T in [0.5,1.0], lambda_Psi in [0.5,2.0], alpha in [0.5,1.5]
- PT cost formula; margin definition; informative output is margin distribution
