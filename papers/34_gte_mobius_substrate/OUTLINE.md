# P34 — The GTE-Möbius Substrate: Computation, Transputation, and Physical Completeness
## Chapter Outline

**Working title:** The GTE-Möbius Substrate: Arithmetic Unification of Computation and
Transputation in the Universal Generative Principle

**Planned venue:** Physical Review D (or monograph chapter in the UGP series)
**Dependencies:** P28 (GTE-CA universality), P30 (Cook's Theorem Lean certification)
**Status:** PLANNED — detailed outline complete; content in progress (EPIC_071)
**Date of outline:** 2026-05-20

---

## Abstract (10–12 lines)

The Universal Generative Principle (UGP) requires that its physical substrate be a single
mathematical object performing two operationally distinct but inseparable modes of action:
*computation* (deterministic evolution under f_MDL) and *transputation* (PSC-forced selection
among undecidable alternatives).  We formalize this substrate as the GTE-Möbius triple
$(A, e, [D])$, where $A$ is the GTE arithmetic carrier (the $\mathbb{Z}_7$ dynamics of P28),
$e$ is the Cook self-encoding map (Turing completeness, P30), and $[D]$ is the
PSC-consistent coherence measure class (the D1–D5 constraints from NEMS Papers 10–11–13).
The Möbius name reflects the single-surface architecture: what appear to be two faces
(computation; transputation) are connected without a sharp boundary — the Gödel-Turing
boundary of $(A, e)$ is the computation/transputation boundary of the physics.
We define the TPC (Turing-PSC) computability class, prove it strictly intermediate between
Turing-decidable and hypercomputation, and show that its three-level depth equals $N_\text{gen} = 3$
(Lean-certified, zero sorry).  Five consistency conjectures (C1–C5) are stated with precise
hypotheses; C3 (TPC Completeness) and C4 (Lawvere-Physical Correspondence) are identified
as highest-priority open problems.

---

## §1  Introduction  (~3 pp)

**Goals:** orient the reader within the UGP series; state what this paper proves vs. conjectures;
motivate the three-component formalism.

- **§1.1  The UGP substrate problem.**
  P22–P29 derive particle quantum numbers, masses, gauge structure, and generation
  hierarchy from GTE arithmetic.  A deeper question remains: what kind of *computational
  object* is the substrate, and how does it generate both the deterministic evolution of
  free particles and the irreversible, non-computable selection events of quantum measurement?
- **§1.2  The two operational modes and why they coexist.**
  Free propagation ($f_\text{MDL}$, Schrödinger) is deterministic and Turing-equivalent.
  Measurement outcome selection, decay timing, and vacuum-reachability adjudication are not.
  The diagonal barrier (NEMS Paper 11, Lean-certified, zero sorry) proves that any
  total-effective adjudicator on diagonal-capable record fragments would decide the
  halting problem — an unconditional contradiction.  The substrate must therefore perform a
  second, non-computable mode of action: transputation.
- **§1.3  Relation to earlier UGP papers.**
  P28 establishes the $\mathbb{Z}_7$ CA dynamics and its fixed-point structure.
  P30 certifies the Cook self-encoding (Rule 110 Turing completeness) in Lean.
  P31–P33 derive electroweak, quantum-mechanical, and gravitational predictions from this
  arithmetic.  P34 synthesizes the underlying operational logic of the substrate that
  grounds all of those derivations.
- **§1.4  Scope: proved, conjectured, and open.**
  Clear demarcation table (mirroring §7 of the Substrate Specification):
  what is Lean-certified, what is analytically derived (CatAD), what remains conjectural (C1–C5).

---

## §2  The Three Aspects: $(A,\, e,\, [D])$  (~5 pp)

**Thesis:** The substrate is a single object seen under three interpretative lenses —
not three interacting components.

### §2.1  Component $A$: The Arithmetic Carrier  (~1.5 pp)

| Property | Value | Certification |
|---|---|---|
| Prime base | $p = 7$ | Lean: Mersenne-GCD ridge |
| Winding alphabet | $\mathbb{Z}_7$ | CatAL (P22) |
| Generation ring | $\mathbb{Z}_5$ | CatAL (P01) |
| Dynamics $f_\text{MDL}$ | $\mathbb{Z}_7^3 \to \mathbb{Z}_7$ (Rule 110 binary projection) | CatAL (P28, CUP-12) |
| MDL description length | 76 bits (minimal over all $\mathbb{Z}_7$ universal CAs) | CatA |
| GoE property | $\text{gen}_1$ has zero $f_\text{MDL}$-predecessors | Lean: `garden_of_eden_gen1` |
| $N_c = 3$ | Mersenne-GCD ridge arithmetic | Lean: P28 §12.3 |

Key structural facts to derive:
- $A$ is fully determined by PSC + the P28 chain: zero free parameters.
- $A$ contains a canonical *decidable fragment* (bounded $\mathbb{Z}_7$ configurations)
  and an implicit *self-referential fragment* through $e$.
- The boundary between these fragments is the Gödel-Turing boundary of $(A, e)$.

### §2.2  Component $e$: The Self-Encoding Map  (~1.5 pp)

Formal statement:
$$e : A \;\longrightarrow\; (A \to_{\mathrm{comp}} A), \qquad
  e(a) = \text{``simulate } f_\text{MDL} \text{ from configuration } a\text{''}$$

- By Rule 110 Turing completeness (CUP-11c, Lean-certified conditional on 1 bridge axiom),
  $e$ is surjective onto all computable functions $A \to A$.
- Lawvere's fixed-point theorem in the cartesian-closed category of computable maps on $A$:
  surjectivity of $e$ guarantees that every computable endofunction of $A$ has a fixed point.
  Physical instances: the vacuum state, the $\text{gen}_1$–$\text{gen}_2$–$\text{gen}_3$ orbit.
- Induced undecidability: ``does the $f_\text{MDL}$ chain from $c$ reach the vacuum?'' is
  undecidable (P28 `fmdl_vacuum_reachability_is_undecidable`, conditional on 6 bridge axioms).
- MDL minimality: $e$ is the minimum-complexity Turing-complete encoding on alphabet
  $\mathbb{Z}_7$ with neighborhood radius 1.  76 bits.
- **Open:** discharging the `rule110_simulates_computable` bridge axiom via Cook's theorem
  (P30, EPIC_070 Spec 08) is the highest-priority outstanding Lean task.

### §2.3  Component $[D]$: The Coherence Measure Class  (~2 pp)

A coherence measure is a map:
$$D : \text{A-realizations} \times \text{A-records} \;\to\; \mathbb{R}_{\geq 0}$$
measuring distance from perfect coherence with a macroscopic record.

**Defining constraints (all five required, none individually sufficient):**

- **D1** (Non-negativity): $D \geq 0$; $D = 0$ iff full coherence.
- **D2** (PSC invariance): $D$ is invariant under $\mathbb{Z}_7$ gauge, $\mathbb{Z}_5$
  cyclic, and orbit relabeling.
- **D3** (Non-computability): $D$ is not a total computable function on diagonal-capable
  record fragments (diagonal barrier, NEMS Paper 11, Lean-certified, zero sorry).
- **D4** (Selection completeness): $D$ achieves a unique minimum over every
  record-equivalence class.
- **D5** (Born-rule consistency): marginals of $D$'s minimizing distribution reproduce
  $P(\text{outcome } n) = |c_n|^2$ (NEMS Paper 13, CatA).

Physical representative in our universe: the PR-0 Ablowitz-Ladik dissonance functional.
This is one specific member of $[D]$; different members correspond to different
PSC-consistent universes sharing $(A, e)$.

**Dependency structure (acyclic):** $A$ is independent; $e$ requires $A$; $[D]$ requires
both $A$ and $e$.  No circular dependency.  The internal self-consistency of $[D]$
is a bounded fixed point guaranteed by the Lawvere theorem in the category of
PSC-consistent coherence measures.

---

## §3  The Computation/Transputation Boundary  (~5 pp)

**Thesis:** The Gödel-Turing boundary of $(A, e)$ is not an abstract mathematical
curiosity — it is the computation/transputation boundary of the physics.

### §3.1  Zone L1 (computable): decidable reachability  (~1 pp)

- All problems answerable by $f_\text{MDL}$ evaluation with a unique next state.
- Formal characterization: configurations in $\Pi^0_1$ (reachability decidable by
  co-semi-decidable check).
- Physical instances: free propagation, wavefunction amplitude evolution, decay rates,
  Born rule probabilities ($|c_n|^2$ as functions of quantum numbers), generation orbit,
  GoE predecessor counts, winding conservation.
- Lean status of each instance (table matching §3 of the Decision Tree document).

### §3.2  Zone L2 (diagonal): transputation domain  (~1 pp)

- Configurations encoding self-referential halting questions.
- Physical instances: measurement outcome selection, decay timing, vacuum-reachability
  adjudication, Born rule outcome selection (which $n$ occurs in THIS event).
- The diagonal barrier: any total-effective adjudicator on diagonal-capable record
  fragments would decide the halting problem — contradiction.  Hence the substrate
  uses $D \in [D]$ for adjudication (non-computable, PSC-forced).

### §3.3  The formal decision taxonomy  (~0.5 pp)

Reproduce (in concise form) the four-question decision tree from the Computation vs.
Transputation taxonomy document:

Q1: Pure quantum-number arithmetic? → **Computable (Arithmetic Layer)**
Q2: Unique next state from deterministic law? → **Computable (Computation Layer)**
Q3: Selection among multiple admissible continuations? → Q4 if yes
Q4: Diagonal-capable record fragment? →
    NO → **Transputable Regime III** (mild selection)
    YES → **Transputable Regime IV** (diagonal barrier applies)

### §3.4  Physical examples across all four regimes  (~1.5 pp)

| Physical process | Regime | Certification |
|---|---|---|
| Particle-type identity ($\mathbb{Z}_7$ winding) | Arithmetic (Q1) | CatAL |
| Generation orbit ($\text{gen}_1 \to \text{gen}_2 \to \text{gen}_3$) | Arithmetic (Q1) | CatAL |
| GoE stability ($\text{pred}(\text{gen}_1) = 0$) | Arithmetic (Q1) | Lean-certified |
| Free propagation, Schrödinger evolution | Computation (Q2) | CatAL |
| Decay rates, Born probabilities | Computation (Q2) | Partially CatAL |
| Photon selection at absorption vertex | Transputable III (Q3, Q4 NO) | Analytical |
| Measurement outcome selection | Transputable IV (Q4 YES) | Lean (conditional) |
| Decay timing | Transputable IV (Q4 YES) | Lean (conditional) |
| Vacuum-reachability decision | Undecidable (outside TPC) | Lean (conditional) |

### §3.5  The Gödel-Turing boundary: semantic, not syntactic  (~1 pp)

The boundary is *content-dependent*, not form-dependent.  There is no clean syntactic
layer interface.  The same formal symbol string can be in Zone L1 (as a pure arithmetic
statement about $\mathbb{Z}_7$ values) or in Zone L2 (as an encoding of a halting question),
depending on what it represents.  This is why the Möbius metaphor is apt: the "two faces"
share a surface.

---

## §4  The TPC Computability Class  (~3 pp)

**Thesis:** The substrate defines a new computability class TPC, strictly between
Turing-decidable and hypercomputation, whose three-level depth equals $N_\text{gen} = 3$.

### §4.1  Definition  (~0.5 pp)

A problem $P$ is in TPC if there exist:
- A Turing machine $M$ that enumerates all admissible continuations $S(P, \text{record})$; and
- A measure $D \in [D]$ such that $D(S(P, \text{record}))$ selects a canonical element;
- and the answer to $P$ is $D(S(P, \text{record}))$.

TPC is *semantically indexed*: answers depend on the physical history record preceding
the problem instance.

### §4.2  Position in the computability hierarchy  (~1 pp)

$$\text{Decidable (Turing)} \;\subsetneq\; \text{TPC} \;\subsetneq\; \text{Hypercomputation}$$

- TPC strictly contains all Turing-decidable problems plus all PSC-forced
  record-indexed selection problems.
- TPC strictly excludes all undecidable decision problems (halting, $\Sigma^0_1 \setminus$
  recursive).
- TPC is *not* an oracle class: it solves semantic selection problems, not
  decision problems of higher arithmetic complexity.  It is incommensurable with the
  arithmetical hierarchy.

Lean certification: 14 items (3 level definitions + 13 theorems) in
`GUTStructure.lean §62` (namespace `TPCPowerClass`), zero sorry, zero custom axioms.
Proof methods: `norm_num`, `rfl`, `decide`, `simp`, `cases`.

### §4.3  The $N_\text{gen} = 3$ hierarchy depth  (~1 pp)

The master structural result:
$$\texttt{level\_hypercomputation} + 1 \;=\; N_\text{gen} \;=\; 3$$

The same arithmetic constant $N_\text{gen} = 3$ that counts SM fermion generations,
SM quark colour charges ($N_c = 3$), and yields the GUT Weinberg angle via $3/8$,
also counts the depth of the TPC computability hierarchy.  A PSC-consistent universe
with $N_\text{gen}$ generations has a computation/adjudication hierarchy of depth
$N_\text{gen}$.

Physical identification label: **CatAD** (analytically derived, pending C3 proof).
Lean numerical identity: **CatAL** (Lean-certified, zero sorry).

### §4.4  TPC vs. oracle computation  (~0.5 pp)

What TPC is NOT:
- Not a Turing machine with a halting oracle ($\emptyset'$): TPC cannot decide the halting
  problem, even with oracle access.
- Not hypercomputation of any standard kind.
- Not "transputation ⊃ computation": computation (decision problems) and transputation
  (selection problems) are different logical types; neither contains the other.

---

## §5  The Five Consistency Conjectures  (~6 pp)

Each conjecture is presented with: precise mathematical statement, motivation,
current evidence, what would be required for a proof, and physical implications.

### §5.1  C1 — Final Coalgebra Conjecture  (~1.2 pp)

**Statement:** $(A, e, [D])$ is the final coalgebra of the functor $F_\text{PSC}$ in
the category of PSC-consistent arithmetic systems with PSC-morphisms.

**Equivalently:** For every PSC-consistent arithmetic system $U$, there exists a unique
PSC-morphism $\varphi : U \to (A, e, [D])$.

**Physical meaning:** GTE is THE unique PSC-consistent universe up to isomorphism.
Every other PSC-consistent universe embeds into ours.

**Current status:** Conjectured.  The Lean proof of `psc_implies_computational_universality`
in `GUTStructure.lean` is currently tautological (identity collapse from Round 02 analysis);
a genuine proof requires abstract PSC category theory not yet formalized.

**What is needed:** Formal definition of the PSC morphism category + proof of universality
of the final coalgebra.

### §5.2  C2 — Coherence Measure Uniqueness  (~1.2 pp)

**Statement:** Under the additional constraints of Lorentz invariance and CPT symmetry
(or controlled CPT violation), the class $[D]$ has a unique minimum-complexity
representative: the PR-0 Ablowitz-Ladik dissonance functional.

**Physical meaning:** PR-0 is the unique physical realization of $[D]$ compatible with
relativistic physics.  Transputation is not merely constrained by PSC — it is forced
to take the specific form of the Ablowitz-Ladik soliton dynamics.

**Current status:** Conjectured.  No formal investigation of Lorentz-invariant
coherence measures on GTE configurations has begun.

**What is needed:** Characterization of all Lorentz-invariant functionals on relativistic
field configurations satisfying D1–D5; proof that AL-dissonance is the unique minimum.

### §5.3  C3 — TPC Completeness  (~1.2 pp)

**Statement:** TPC is complete for the class of problems arising in any PSC-consistent
universe: every physical question in a PSC universe is either Turing-decidable (Zone L1)
or in TPC (Zone L2 selection).  No physical question escapes this dichotomy.

**Physical meaning:** TPC is not an ad hoc class — it is the COMPLETE computability
class of physics.  There is no third category of physical process.

**Current status:** Conjectured.  The arithmetic proxy layer (§62, B-2) certifies
the numerical hierarchy; the physical identification is CatAD.

**What is needed:**
1. Formal definition of "physical questions in a PSC universe" as a problem class.
2. Proof that every such question reduces to a Zone L1 (decidable) or Zone L2 (selection) problem.
3. Lean: build on `pt_non_effectiveness` from transputation-lean (NEMS Paper 11).

**Priority:** HIGH — this is the conjecture with the clearest path to formalization.

### §5.4  C4 — Lawvere-Physical Correspondence  (~1.2 pp)

**Statement:** The three Lawvere-zone types of computable maps on $A$ correspond
exactly to three physical regimes:
- Zone L1 (computable fixed-point approach) $\leftrightarrow$ Stable particles
  ($\text{gen}_1$, free propagation)
- Lawvere periodic orbits $\leftrightarrow$ Metastable particles
  ($\text{gen}_2, \text{gen}_3$ — period-3 orbit)
- Zone L2 (diagonal undecidability) $\leftrightarrow$ Quantum measurement events

**Physical meaning:** The stability ordering of particles is not an independent empirical
fact — it is read off from the Lawvere structure of $(A, e)$.  The most stable particles
are Lawvere fixed points; metastable particles are periodic orbits; measurement events
are the diagonal barrier in action.

**Current status:** Conjectured.  Partially supported by Rounds 1–2 analysis.
Requires formal definition of the three Lawvere-zone types.

**What is needed:** Lean formalization of `LawvereZone.lean` defining the three types;
proof of the physical correspondence using P28's GoE theorem and generation orbit theorem.

### §5.5  C5 — Self-Specification Depth  (~1.2 pp)

**Statement:** The incompleteness depth of $T_\text{GTE}$ (the formal theory of GTE
arithmetic) equals $\varepsilon_0$ — the Goodstein/Gentzen ordinal, the proof-theoretic
ordinal of Peano Arithmetic.  The computation/transputation boundary occurs at ordinal
rank $\varepsilon_0$ in the Gödel numbering of $T_\text{GTE}$.

**Physical meaning:** The Gödel-Turing boundary in GTE has a precise ordinal depth.
The substrate's self-specification limit is not vague — it is quantified by the
proof-theoretic strength of its arithmetic.

**Current status:** Highly speculative.  The plausibility argument: GTE arithmetic
is a fragment of number theory, whose proof-theoretic ordinal is $\varepsilon_0$; if GTE
arithmetic is strong enough to simulate Peano Arithmetic (likely given Turing completeness),
the ordinal depth follows.  Not yet investigated formally.

**What is needed:** Proof that $T_\text{GTE}$ has the same proof-theoretic strength as PA,
or characterization of how it falls short.  This is a deep proof-theory problem.

---

## §6  Open Problems  (~2 pp)

Enumeration of the most important open problems, with precise statements and dependency
relationships.

### Priority 1 (blocks P34 §2.2 / §3 fully)
- **Cook bridge axiom discharge:** Prove `rule110_simulates_computable` without axioms
  (EPIC_070 Spec 08, Cook's Theorem Lean Certification, P30).  Enables certification of
  the $e$ component and conditional results of P28 / P34.

### Priority 2 (enables major theorems)
- **TPC Completeness (C3):** Formal definition of "physical questions in a PSC universe"
  + proof that all fall into Zone L1 or Zone L2.  Currently the most tractable of C1–C5.
- **Lawvere-Physical Correspondence (C4):** Formal `LawvereZone.lean` + physical
  correspondence proof for stable / metastable / measurement regimes.

### Priority 3 (long-range)
- **$[D]$ explicit construction from PR-0:** Prove D1–D5 for the Ablowitz-Ladik
  dissonance functional; show it is the minimum-complexity representative (C2).
- **Final coalgebra / $F_\text{PSC}$ formalization (C1):** Abstract PSC category theory.
- **Ordinal rank $\varepsilon_0$ for Gödel-Turing boundary (C5):** Proof-theoretic
  strength of $T_\text{GTE}$ vs. PA.

### Connection to earlier papers
- P30 (Cook's Theorem): discharges the bridge axiom for $e$.
- P28 §12.x: provides the Lean-certified GoE, orbit, winding, and $N_c = 3$ results
  that anchor $A$.
- NEMS Papers 10–11–13: provide D1–D5 constraints and the diagonal barrier that
  anchor $[D]$.

---

## §7  Summary  (~1 pp)

- Restate the main thesis: the GTE-Möbius substrate is a single object $(A, e, [D])$
  with no sharp separation between computation and transputation.
- The Gödel-Turing boundary of $(A, e)$ IS the computation/transputation boundary of
  the physics.  This is the deepest non-vague statement about the substrate achievable
  within any formal system powerful enough to describe $(A, e)$.
- TPC is the correct computability class.  Its three-level depth $= N_\text{gen} = 3$
  is a non-trivial structural coincidence linking generation physics to computability theory,
  now Lean-certified.
- Five conjectures (C1–C5) formalize the deepest open questions.  C3 and C4 are the
  most tractable; C1 and C5 are long-range.

---

## Appendix A: Summary Table — What CAN and CANNOT Be Said

| Claim | Status | Evidence |
|---|---|---|
| $A$ determined by PSC + P28 chain | Proved | CatAL \[Lean\] |
| $e$ is the Cook encoding of Rule 110 Turing universality | Certified conditional | CatAL \[1 bridge axiom\] |
| $[D]$ satisfies D1–D5 | Proved from PSC | CatA (NEMS P10–P11–P13) |
| Gödel-Turing boundary of $(A,e)$ = computation/transputation boundary | Proved | CatA |
| TPC 3-level hierarchy: $0 < 1 < 2$, $N_\text{gen}$-depth | Lean-certified | CatAL \[zero sorry\] |
| Möbius architecture (single surface, two faces) | Argued | Theoretical |
| Lawvere structure of $(A,e)$ | Proved | CatA (Rule 110 + Lawvere) |
| No circular specification dependency | Established | Structural |
| Specific $D \in [D]$ for our universe | Underdetermined | Open |
| Specific TPC-selected outcomes | Not provable in $T_\text{GTE}$ | Diagonal barrier |
| $C1$: GTE = final coalgebra of $F_\text{PSC}$ | Conjectured | C1 |
| $C2$: $D$ = PR-0 AL-dissonance uniquely | Conjectured | C2 |
| $C3$: TPC Completeness | Conjectured | C3 (highest tractability) |
| $C4$: Lawvere-Physical Correspondence | Conjectured | C4 |
| $C5$: Incompleteness depth $= \varepsilon_0$ | Highly speculative | C5 |

---

## Appendix B: Lean Certification Status (P34-relevant modules)

| Module | Location | Key theorems | Sorry count | Cat |
|---|---|---|---|---|
| `GUTStructure.lean §62` | `ugp-lean` (to graduate) | 14 TPC items | 0 | CatAL |
| `GTEComputability.lean` | `ugp-lean` | `fmdl_vacuum_reachability_is_undecidable` | 6 bridge axioms | CatAL (conditional) |
| `GardenOfEden.lean` | `ugp-lean` | `garden_of_eden_gen1` | 0 | CatAL |
| `GenerationOrbit.lean` | `ugp-lean` | orbit period-3, GoE predecessor counts | 0 | CatAL |
| `CookTheorem.lean` (target, P30) | `ugp-lean` (planned) | `rule110_simulates_computable` | pending | — |

---

## Estimated Length

| Section | ~pages |
|---|---|
| Abstract | 0.5 |
| §1 Introduction | 3 |
| §2 Three Aspects | 5 |
| §3 Computation/Transputation Boundary | 5 |
| §4 TPC Power Class | 3 |
| §5 Five Consistency Conjectures | 6 |
| §6 Open Problems | 2 |
| §7 Summary | 1 |
| Appendices A–B | 2 |
| **Total** | **~27.5 pp** |

---

*OUTLINE.md — P34 GTE-Möbius Substrate — INTERNAL — Nova Spivack — 2026-05-20*
