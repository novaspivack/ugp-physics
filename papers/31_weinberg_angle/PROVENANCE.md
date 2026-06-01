# PROVENANCE — P31: Arithmetic Derivation of the Electroweak Mixing Angle

**Paper:** `papers/31_weinberg_angle/weinberg_angle_paper.tex`  
**Status:** Draft — pre-submission

---

## Lean certification

| Module | Repo (current) | Graduation target |
|--------|----------------|-------------------|
| `GUTStructure.lean` §§10,12,13,24,45,49,50,63,78 | `ugp-lean` | `ugp-lean` |
| `EWChiralBridge.lean` | `ugp-lean` | `ugp-lean` |
| `EWBosonStructure.lean` | `ugp-lean` | `ugp-lean` |

Key commits referenced in appendix (partial list): `596b190` (§12 closure), `9e4844f` (§24 orbit-average), `2010aee0` (B126.1 orbit absorption). Re-pin all SHAs when modules graduate to canonical `ugp-lean`.

---

## Computational artifacts (graduated 2026-05-20)

| Script | Location |
|--------|----------|
| `double_mersenne_endpoint.py` | `scripts/` ✅ |
| `palindrome_identification.py` | `scripts/` ✅ |
| `weinberg_angle_arithmetic.py` | `scripts/` ✅ |

Scripts produce stdout only (no JSON artifacts). JSON artifact generation deferred to pre-Zenodo pass.

---

## Paper integration passes (internal tracking)

| Pass | Content |
|------|---------|
| B74.1–B74.2 | Orbit-average + cross-sector bridge (2026-05-20) |
| R223.P31 | Charge neutrality remark + §63 Lean table |
| B126.1 | CA orbit absorption §7 |
| R197.1 | Proton decay open-problem framing |

Full reproducibility checklist: `REPRODUCE.md` § Graduation checklist; Handoff 8 § P31.

---

*PROVENANCE.md — P31 — 2026-05-20*
