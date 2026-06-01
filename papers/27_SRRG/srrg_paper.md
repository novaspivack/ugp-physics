# The Self-Referential Renormalization Group

**Author:** Nova Spivack  
**Status:** WORKING PAPER — FIRST DRAFT  
**Date:** 2026-05-11  
**Classification:** PUBLIC (working paper; not yet submitted)

---

## Abstract

I introduce the *Self-Referential Renormalization Group* (SRRG): a gradient-flow
theory on the space of self-referential physical theories. The SRRG flow maximizes
a net viability functional $F[S] = R[S] - C_\Lambda[S]$, where $R[S]$ measures
the self-representation capacity of theory $S$ and $C_\Lambda[S]$ encodes three
independent stability constraints derived from the NEMS/PSC framework (closure cost,
self-computation-principle cost, and selector cost). The SRRG fixed-point equation
$\delta F[S]/\delta S = 0$ is satisfied at a theory $S^*$ where the universe
"knows itself" with maximal stability, and I show that the fixed-point conditions
force:

1. The **Information Profit Threshold** IPT ≈ 1.1309 as the information-efficiency
   ratio $R[S^*]/C_\Lambda[S^*]$ at the fixed point.
2. The **minimal gauge group U(1)** as the unique group minimizing the SCP cost
   $C_{\text{SCP}}[S^*] = 0$.
3. The **$1/\varphi$ contraction eigenvalue** of the linearized flow near $S^*$,
   where $\varphi$ is the golden ratio.

Fixed-point existence is established via the Master Fixed-Point Theorem.
The F-theorem (monotonicity of $F[S]$ along flow) is the SRRG analogue of
Zamolodchikov's $c$-theorem. All core theorems are machine-certified in
`srrg-lean` at zero sorry.

---

## Structure

| Section | Topic |
|---------|-------|
| §1 | Introduction: physical constants as fixed points |
| §2 | The SRRG framework: theory space, $R[S]$, $C_\Lambda[S]$, $F[S]$, flow |
| §3 | Fixed-point theorems: existence, F-theorem, stability, uniqueness |
| §4 | NEMS/PSC as SRRG axiom system |
| §5 | IPT as the SRRG information-efficiency fixed point |
| §6 | Gauge symmetry at the SRRG fixed point |
| §7 | CFT universality classes and the $\varepsilon_{3s} = \text{IPT}$ prediction |
| §8 | Discussion: fine-tuning, anthropic reasoning, open problems |
| §9 | Lean 4 machine certification table |
| App. A | Complete Lean theorem table |

---

## Lean Certification

All core theorems formalized in `srrg-lean` (zero sorry for all owned modules):

| Theorem | Location | Status |
|---------|----------|--------|
| SRRG fixed-point existence (finite) | `FixedPoints/Existence` | zero sorry |
| MFP-1 flow fixed point | `FixedPoints/Existence` | zero sorry |
| $\|\psi\| = 1/\varphi$ stability | `FixedPoints/Stability` | zero sorry |
| Uniqueness (conditional) | `FixedPoints/Uniqueness` | zero sorry |
| $C_\Lambda = 0$ iff all components zero | `Core/ConstraintFunctional` | zero sorry |
| IPT = SRRG viability ratio | `Connection/IPTBridge` | zero sorry |
| H9 Landauer identity | `Connection/H9Bridge` | zero sorry |
| NEMS → SRRG typing | `Bridges/FromNEMS` | zero sorry |
| IPT closed-form | `Bridges/ToIPT` | zero sorry |

Pre-existing upstream warnings (not from this paper's work):
`UgpPhysicsLean.GXT.{LieExpSurjective, U1DirectProof}`.

---

## Dependencies

- `nems-lean` — NEMS/PSC framework (MFP-1, barriers, closure audit)
- `ugp-lean` — UGP gauge structure, GTE, golden-ratio eigenvalue
- `ugp-physics-lean` — IPT theorem, GXT, H9, U1DirectProof
- `srrg-lean` — main SRRG Lean library (this paper's Lean contribution)
- `Mathlib` — standard math library
