# PROVENANCE — P30 Cook Theorem Formalization

**Paper:** P30 — Machine-Certified Formalization of Cook's Rule 110 Universality Theorem in Lean 4  
**Status:** Draft (partial certification documented in `cook_theorem_paper.tex`, 2026-05-20)

## Origin

This paper documents the Lean 4 formalization in **`rule110-lean`**, undertaken to discharge the Rule 110 universality bridge used conditionally in UGP Paper P28 (`SpivackCompUniversality`).

Cook's mathematical sources: Cook (2004) *Complex Systems*; Cook (2009) EPTCS/arXiv:0906.3248; collision checklist per Neary--Woods (ICALP 2006).

## Key source files (Lean)

| Path | Role |
|------|------|
| `rule110-lean/Rule110/CTStoRule110.lean` | Encodings, bridge axioms, `cook_cts_step_sim_ax` |
| `rule110-lean/Rule110/InfTape.lean` | Infinite tape, Icc locality |
| `rule110-lean/Rule110/CookC2InfTapeBridge.lean` | Partial C1, L ≤ 7 |
| `rule110-lean/Rule110/CookC2SupportBareEquiv.lean` | Ossifier bare equivalence |
| `rule110-lean/Rule110/CookUniversalityChain.lean` | `CookUniversalityDischarged` bundle |
| `rule110-lean/Rule110/CookTM2Bridge.lean` | Stage 4 scaffolds |
| `rule110-lean/Rule110/CookLen6TailEvolution.lean` | L=6 list evolution / compose certificates |
| `rule110-lean/Rule110/CookLen6FastInfCert.lean` | Fast list-only compose cert alias + extraction |
| `rule110-lean/Rule110/CookLen6InfTapeBridge.lean` | List↔InfTape bridges; one remaining evolved-side axiom |
| `papers/30_cook_theorem/scripts/len6_evolved_origin_cert.py` | Python cross-check of compose certificate |
| `papers/30_cook_theorem/data/len6_evolved_origin_cert.json` | Certificate artifact (SHA-256 of init tape + slot results) |

**Commit pin (partial snapshot):** `dc17feb` on local `main` (see agent handoff for latest; update at graduation).

## Change log

| Date | Change | Reason |
|------|--------|--------|
| 2026-05-19 | Directory created | P30 planned as Cook certification paper |
| 2026-05-20 | L=6 fast list cert + Python cross-check | `CookLen6FastInfCert`, `len6_evolved_origin_cert.py`, REPRODUCE update |
| 2026-05-19 | `cook_theorem_paper.tex`, `OUTLINE.md`, refs, README | Draft aligned with partial Lean status |
