# Paper 27: The Self-Referential Renormalization Group

**Title:** The Self-Referential Renormalization Group: A Universal Framework for Physical Constants

**Author:** Nova Spivack  
**Status:** Pre-draft (outline complete)  
**Year:** 2026

## Abstract (draft)

The Self-Referential Renormalization Group (SRRG) is a gradient-flow theory on the space of self-referential physical theories. Its fixed points simultaneously determine the Information Profit Threshold (IPT ≈ 1.1309), the Standard Model gauge group, and the NEMS observational barriers — as necessary corollaries of a single fixed-point theorem δF[S]/δS = 0. This paper presents the SRRG framework, proves fixed-point existence and stability, and derives IPT, U(1) symmetry, and the golden ratio contraction eigenvalue as SRRG outputs. **Lean status (2026-05-11):** the companion [`srrg-lean`](https://github.com/novaspivack/srrg-lean) library certifies the **H9 / Landauer** fixed-point identity (**[H3]**), **A1** (golden contraction), and **circle exp** (A2 limb) at **zero `sorry`**; the lemma packaging **efficiency at the SRRG fixed-point → IPT** remains the outstanding formalisation target tracked in `srrg-lean` (hypotheses [H1], [H2], [H4] in module `Connection/IPTBridge`), with one transitional `sorry` pending that bridge.

## Paper Dependencies

- P10 (Reflexive Reality / NEMS)
- P15 (Information Profit Threshold)
- P01 (Standard Model from UGP)
- P23 (Foundational Finality)
- P25 (Unified Rigidity)
- P26 (General Selection Theory)

## Lean Certification

Companion library: [`srrg-lean`](https://github.com/novaspivack/srrg-lean) — local checkout path `~/srrg-lean/` conventionally sits as a sibling of canonical `ugp-lean`-family checkouts used for PSC / GXT bridges. Detailed theorem tables and reproducible numerics referenced in `srrg_paper.tex`, `PROVENANCE.md`, and `REPRODUCE.md` in this directory.
