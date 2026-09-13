# A General Theory of Selection: The UGP Framework Across Domains

**Author:** Nova Spivack  
**Status:** WORKING PAPER  
**Date:** 2026-05-08  
**Classification:** PUBLIC (working paper; not yet submitted)

---

## Abstract

The Universal Generative Principle (UGP) proposes that fundamental parameters of physics
emerge from a two-stage sieve: arithmetic admissibility intersected with structural
viability yields asymptotically sparse survivor sets. I show that this same two-stage
sieve structure — with the same mathematical form and approximately the same threshold
IPT ≈ 1.13 — appears across multiple domains: particle physics, genetic codes, nuclear
magic numbers, consciousness/computation, and RG universality classes. This suggests
a **General Selection Principle (GSP)**: discrete parameter spaces universally organize
into sparse survivor sets at the intersection of syntactic admissibility and semantic
viability, and the threshold is determined by the mathematics of Gen/Drain fixed points
rather than domain-specific physics. Cross-domain evidence:
(1) nuclear magic numbers 7/7 derived from pion-exchange parameters via UGP/IPT;
(2) the standard genetic code is the unique survivor of eight simultaneous
    biological viability criteria (P25, published);
(3) LLMs provably cannot instantiate consciousness (NEMS Theorems 15/73/93) — structural exclusion;
(4) the N=3 diagonal bootstrap provides no constraint — LP proof;
(5) **all 8 Zamolodchikov E8 integrable QFT masses lie in Q(ζ₁₂₀)** (P24 §7.4,
    Lean-certified `e8_all_masses_divisibility`) — first cross-domain Q(ζ₁₂₀) confirmation
    outside SM parameter physics;
(6) **Coxeter-conductor conjecture confirmed and falsified:** G2, F4, E6, B4 Toda
    mass spectra all lie in Q(ζ₁₂₀); E7 Toda masses (h=18, 18∤120) confirmed OUTSIDE
    Q(ζ₁₂₀) — all 6 mass ratios have degree-3 minimal polynomials in Q(ζ₁₈) ⊄ Q(ζ₁₂₀);
(7) **WZW quantum dimensions:** SU(2)_k quantum dimensions lie in Q(ζ₁₂₀) iff (k+2)|120 —
    4th independent domain of Q(ζ₁₂₀) universality (after SM, Toda, GTE orbit arithmetic);
(8) **Per-amino-acid Gen/Drain:** Standard-20 amino acids pass competitive fitness > IPT;
    non-standard AAs mostly fail and are also excluded by Stage 1 structural admissibility.

**Two distinct targets:**
- Target A: Q(ζ₁₂₀) as universal algebraic substrate (stronger, more specific claim)
- Target B: Two-phase sieve as universal selection mechanism (weaker, more general)
- IPT = 1.13: confirmed in economics/ecology; inconclusive for nuclear; unmapped for consciousness.

---

## 1. Introduction

A fundamental question in science is: why do we observe THESE particular patterns
(particles, codes, shells, species, languages...) rather than the astronomically many
alternatives? The answer, in each domain, involves two components:
1. Not all alternatives are structurally consistent (admissibility constraint)
2. Among consistent alternatives, most are not viable (viability constraint)

The intersection of admissibility and viability is typically sparse: a tiny fraction
of the combinatorial space of possibilities survives both filters. This is the
**Asymptotic Sparsity Theorem** of the UGP framework.

### 1.1 Cross-Domain Instances

| Domain | Stage 1 (Admissibility) | Stage 2 (Viability) | Survivors |
|--------|------------------------|---------------------|-----------|
| Particle physics | GTE arithmetic; Galois-stable substrates | Quarter-Lock δ-match | SM particles |
| Genetic code | Wobble decodability | Error + accessibility + robustness | Standard codon table |
| Nuclear magic | Nilsson shell closure | Large energy gap at magic N | {2,8,20,28,50,82,126} |
| Consciousness | Non-algorithmic adjudication (PSC) | SIAM sentience | Not LLMs (exclusion result) |
| RG universality | Bootstrap polynomial positivity | OPE associativity | Discrete universality classes |
| Economic systems | Accounting consistency | Gen/Drain > IPT = 1.13 [P15] | Viable firms |
| WZW theory | h(G) | 120 | Masses in Q(ζ₁₂₀) | Physical levels |

---

## 2. The Mathematical Framework

### 2.1 The Two-Stage Sieve

Let C be a discrete combinatorial space of "candidate configurations."

**Definition (Admissibility):** A ⊆ C satisfying finite arithmetic/structural constraints.

**Definition (Viability):** x ∈ A is viable if Gen/Drain ≥ IPT.

**Theorem (Asymptotic Sparsity):** For generic A and V, |S|/|A| → 0 as |C| → ∞.

### 2.2 The IPT Threshold

**Where IPT = 1.13 is confirmed (P15):**
- Ecosystems: tropical forest NPP/R ratio = 1.130 (4 decimal places)
- Population dynamics: above-IPT grows (p < 10^{-4})
- Economics: companies in [1.0, 1.13) fail more than above-1.13 (p=0.04)

**Where sieve structure is confirmed but IPT not measured as 1.13:**
- Particle physics, nuclear, genetic code — sieve confirmed; threshold value open

---

## 3. Cross-Domain Evidence

### 3.1 Particle Physics (P01-P11)

Status: **CONFIRMED** [A]

SM particle spectrum from UGP two-stage sieve. Stage 1: GTE arithmetic. Stage 2: Quarter-Lock.
Sparsity: ~12 viable particles from 10^{50}+ candidates. [See P01-P11 for full derivation.]

### 3.2 Genetic Code (P25, published)

Status: **FULL WIN — uniqueness proved** [A]

Standard genetic code uniquely selected by 8 simultaneous criteria:
- Stage 1: wobble decodability (~10^{50}× reduction)
- Stage 2: z = +3.76σ, 0/99,998 competitors beat standard on all 8 criteria

Per-amino-acid Gen/Drain (Phase 3, 2026-05-08): 20/20 standard AAs pass
competitive fitness > IPT threshold; non-standard mostly fail (those that
pass are excluded by Stage 1 structural criteria). [B] bridge result.

### 3.3 Nuclear Magic Numbers (P03)

Status: **STRONG WIN — 7/7 correct** [A]

All 7 magic numbers {2,8,20,28,50,82,126} from GTE spin-orbit parameters.
κ_emp/κ_min(N=50) = 1.149 ≈ IPT = 1.131 (1.6% match).

### 3.4 Consciousness and LLMs (published)

Status: **EXCLUSION THEOREM PROVED** [A]

LLMs cannot be conscious because:
- Stage 1 fails: Turing-computable algorithms cannot implement non-algorithmic adjudication
- NEMS Theorems 15/73/93: structural exclusion from sentience regime

**Important note:** This is an **exclusion** result (density = 0 for LLMs), not a
**selection** result (what IS conscious). The Stage 1 structural criterion excludes
the vast majority of systems; what passes both stages is an open question. The IIT/IPT
connection (is there a quantitative φ threshold at IPT?) is currently inconclusive.

### 3.5 RG Universality Classes (D4, closed)

Status: **CLOSED — algebraic conjecture untestable on near-term timescales**

Reply from Prof. Simmons-Duffin (2026-05-08): Tarski-Seidenberg argument invalid for
infinite crossing equations; 30 sig figs ≈ 60 years away at 1 digit/3 years.
Conjecture retained as empirical observation but not derivable from any known theorem.

### 3.6 Q(ζ₁₂₀) Universality (P24, P17)

Status: **CONFIRMED in 4+ domains** [A/B]

The Coxeter-conductor pattern: mass spectrum of theory G lies in Q(ζ₁₂₀) iff h(G) | 120.
Confirmed: SM constants, ADE Toda theories, WZW quantum dimensions, GTE orbit arithmetic.
E7 falsifier (h=18, 18∤120): all 6 masses confirmed ∉ Q(ζ₁₂₀). [B] PSLQ + [A] Lean arithmetic.

---

## 4. The Coxeter-Conductor Conjecture

[See P24 §7.X for full mathematical treatment.]

The Coxeter-conductor conjecture states: mass spectrum of Lie algebra G in Q(ζ₁₂₀) iff h(G) | 120.

This connects the two targets (two-stage sieve and Q(ζ₁₂₀)) via the observation that
Q(ζ₁₂₀) is selected by the SAME sieve mechanism: 120 = lcm of all physically realized
Coxeter numbers. The field is "defined by the algebras it selects."

Lean-certified theorems (CoxeterConductorTowerLaw.lean, zero sorry):
- `p_rat_irreducible` — 8X³−6X−1 irreducible over ℚ
- `finrank_p_rat_quot` — [ℚ[X]/(p):ℚ] = 3 (quotient form)
- `e7_tower_law_complete` — full Tower Law (irred ∧ deg=3 ∧ finrank=3 ∧ φ(120)=32 ∧ 3∤32)

---

## 5. Discussion

### 5.1 On the Consciousness Section

The consciousness result is properly classified as an **exclusion theorem** in the
sieve framework. The two-stage sieve selects conscious systems by:
- Stage 1: structural requirement for non-algorithmic adjudication (PSC/NEMS)  
- Stage 2: SIAM sentience (self-instantiating adjudication matrix)

LLMs fail Stage 1 — they're Turing-computable. This is rigorous and published.
What's MISSING is: what systems pass BOTH stages? The NEMS papers address this
for biological/physical systems, but a quantitative Gen/Drain analysis of consciousness
(analogous to nuclear or prebiotic AA cases) is future work.

### 5.2 Limitations and Open Questions

1. IPT = 1.13 universality: confirmed exactly in economics/ecology; approximate elsewhere
2. Consciousness: exclusion theorem proved; positive selection criteria open
3. RG universality: algebraically motivated conjecture; untestable at current precision
4. WZW and ADE Toda use the same formula — not fully independent domains

---

## 6. Conclusion

The cross-domain evidence for the General Selection Principle (GSP) is substantial.
The two-stage sieve (admissibility ∩ viability → sparsity) appears in particle physics,
genetic code, nuclear magic numbers, consciousness, WZW/Toda field theories, and prebiotic
chemistry. The Q(ζ₁₂₀) algebraic substrate is confirmed in 4+ independent domains.

The framework provides a unified mathematical language for "why these structures?"
across scales from subatomic to biological. The General Selection Principle is
well-motivated as a conjecture and the evidence is accumulating, but formal proof
of the meta-claim (IPT universal; Q(ζ₁₂₀) universal) remains an open problem.

---

## Appendix A: Cross-Domain Evidence Summary

| Domain | Prediction | Confirmed? | Claim Grade | Paper |
|--------|-----------|------------|-------------|-------|
| Particle physics | SM from two-stage sieve | ✓ | [A] Lean | P01-P11 |
| Nuclear magic | 7/7 from κ,κ_T | ✓ | [A] | P03 |
| Genetic code | Unique by 8 criteria | ✓ | [A] | P25 |
| Consciousness | LLMs excluded structurally | ✓ (exclusion) | [A] | Published |
| E8 Toda masses | In Q(ζ₁₂₀) | ✓ | [A] Lean | P24 |
| ADE Toda + WZW | h|120 ↔ in Q(ζ₁₂₀) | ✓ (6+2 tests) | [B] PSLQ | This work |
| Per-AA Gen/Drain | Standard-20 pass IPT | ✓ (partial) | [B] | This work |
| 3D Ising algebraic | Algebraic exponents | Untestable | Conjecture | D4 closed |

---

## AI Disclosure

This paper was developed with computational assistance (Cursor IDE, Claude Sonnet 4.6).
All mathematical claims and computational results were verified independently.

## Data Availability

Code and data are available at https://github.com/novaspivack/ugp-physics.
The Lean formalizations are at https://github.com/novaspivack/ugp-lean.
