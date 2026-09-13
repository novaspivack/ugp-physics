# Paper Outline

**Black Hole Unitarity via Reflexive Unitarity and Stinespring Dilation:
A GKSL Model in a JT-like PSC Universe**

---

## Abstract

Brief statement of the problem, approach, main results (F_th = 0.9999192951,
F_Stinespring ≥ 1−10⁻⁸, dim(H_E) = 7), and explicit caveats on scope.

---

## 1. Introduction

- The black hole information paradox: Hawking radiation and apparent unitarity
  violation
- Page curve and modern approaches (island formula, ER=EPR, firewall)
- Overview of the MFRR framework and its application to this problem
- Central observation: GKSL dynamics + Stinespring theorem + PT⁻¹ interpretation
- Summary of TE2.4 computational results
- Clear statement of what this paper does and does not claim
- Paper organisation

---

## 2. The PSC Framework and Reflexive Unitarity

### 2.1 The Persistent Self-Consistency Condition
- Definition of the PSC condition
- The adjudication operator PT and its role

### 2.2 The Canonical Reverse PT⁻¹
- PT⁻¹ as the physical recovery channel
- Relation to environment access and unitarity restoration

### 2.3 Reflexive Unitarity
- Definition of reflexive unitarity
- Why it follows from Stinespring + PSC (no additional postulate)

---

## 3. GKSL Dynamics and Stinespring Dilation

### 3.1 GKSL Master Equation
- General form: dρ/dt = −i[H,ρ] + Σ_k γ_k(L_k ρ L†_k − ½{L†_k L_k, ρ})
- CPTP property of e^{tL}
- Detailed balance condition: γ_emission/γ_absorption = exp(−ω/T_H)

### 3.2 Stinespring Dilation Theorem
- Statement of the theorem
- Kraus operator representation
- Construction of the isometry V: H → H ⊗ H_E
- Extension to full unitary on H ⊗ H_E
- dim(H_E) = 1 + (number of Lindblad operators)

### 3.3 The JT-like PSC Model
- JT gravity in 1+1D as motivation
- Finite-dimensional Fock space truncation
- Model parameters: n=3 modes, d=2 levels, T_H=0.003979, coupling=0.01
- Mode frequencies: ω_n = (n+½)πT_H
- Lindblad operators: emission and absorption for each mode

---

## 4. TE2.4 Computational Results

### 4.1 Model Construction and Validation
- Hilbert space construction (dim=8)
- GKSL Lindblad operator construction
- Detailed balance verification (0.00% error)
- CPTP verification via Choi matrix (trace preservation to 10⁻¹⁰)

### 4.2 Stinespring Dilation Results
- Environment dimension: dim(H_E) = 7
- Isometry construction
- Fidelity verification on vacuum, Fock, and thermal states: F ≥ 1−10⁻⁸

### 4.3 Steady-State and Thermalization
- Steady-state fidelity with thermal state: F = 0.9999192951
- Occupation numbers: [0.1640, 0.0077, 0.0003]
- Purity = 0.7142, entropy = 0.4945
- Entropy ratio vs. ideal thermal: 97.2%

### 4.4 Page-like Entropy Curve
- Von Neumann entropy S(t) over time interval [0, 200]
- Monotone approach to thermal equilibrium
- Relation to Page curve phenomenology

---

## 5. Comparison with Existing Approaches

- Island formula / quantum extremal surfaces
- ER=EPR proposal
- Firewall paradox
- How the MFRR/PT⁻¹ picture relates to and differs from each
- Honest assessment of what each approach achieves

---

## 6. Scope, Limitations, and Open Fronts

- This is a toy model: JT-like, not full JT gravity; not 3+1D
- PT⁻¹ is interpretive in the current work, not directly measured or
  derived from a Hilbert-space definition
- Finite-dimensional Fock space truncation
- Open front 1: Extension to 3+1 quantum gravity
- Open front 2: Firewall tension
- Open front 3: Hilbert-space realization of PT⁻¹

---

## 7. Conclusion

- Summary of contributions
- Reflexive unitarity as a conceptual bridge between MFRR and BH information
- Stinespring dilation provides the formal guarantee; PT⁻¹ provides the
  interpretation
- Outlook for future work

---

## Appendices

### Appendix A: Model Parameters
Full parameter table: n_modes, n_levels, T_H, coupling, total_dim, dim(H_E),
mode frequencies.

### Appendix B: Stinespring Construction Details
Explicit Kraus operators K_0 and K_k; isometry construction; QR extension
to full unitary.

### Appendix C: Reproducibility
Data provenance, SHA-256 of primary results file, pointers to source code
and reproduction instructions.
