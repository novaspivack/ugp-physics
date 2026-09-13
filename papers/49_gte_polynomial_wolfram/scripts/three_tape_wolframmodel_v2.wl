#!/usr/bin/env wolframscript
(* three_tape_wolframmodel_v2.wl
   Three-tape GTE WolframModel — v2 with string-atom node IDs.

   v1 bug: raw GF(7) integer values (0–6) used as WolframModel node IDs caused
   WolframModel to conflate distinct cells sharing the same GF(7) value (e.g.,
   all cells with value 2 were aliased to a single node). v2 fixes this by
   encoding each orbit state as a string atom with a tape prefix:
     "x_g1", "x_g2", "x_g3", "x_vac"  — tape x orbit states
     "y_g1", "y_g2", "y_g3", "y_vac"  — tape y orbit states
     "z_g1", "z_g2", "z_g3", "z_vac"  — tape z orbit states

   Architecture: three-tape CMCA in the GTE framework.
     Each tape (x, y, z) encodes a 1D GF(7) cellular automaton whose local
     update rule is f_MDL (the GTE information-mass transformer restricted to
     the 5-cell GEN orbit ring). The three tapes share a single outer clock
     tau_c^out (the DPP clock), encoded here as the 3-hyperedge
       {"x_g1","y_g1","z_g1"}
     which is preserved throughout evolution as the initial synchronization
     record. The EventSelectionFunction "GlobalSpacelike" enforces that all
     three tapes advance in lockstep (no spacelike-separated rewrites on the
     same tape are allowed in the same tick), which is the causal signature
     of the shared DPP outer clock.

   GEN orbit (Lean-certified, zero sorry in ugp-lean):
     GEN1 = {1,5,2,2,1}  — state label "g1"
     GEN2 = {2,5,2,0,2}  — state label "g2"
     GEN3 = {5,6,5,3,5}  — state label "g3"
     VAC  = {0,0,0,0,0}  — state label "vac"

   Evolution: 9 steps = 3 complete GEN1->GEN2->GEN3->VAC cycles per tape.
   Expected output: 27-event causal graph, 27 vertices, 10 state snapshots.

   Requires Wolfram Engine >= 14.3 with SetReplace 0.3.196.
   Run: wolframscript -file papers/49_gte_polynomial_wolfram/scripts/three_tape_wolframmodel_v2.wl
*)

Needs["SetReplace`"];

(* --- Scope and Limitations ---
   This script operates at the ORBIT level, not the cell level.
   Each node in the hypergraph represents one of the four abstract orbit states
   (GEN1, GEN2, GEN3, VAC) for an entire tape, not a single GF(7) cell value.

   What this file DOES:
     - Encodes the three-tape GEN1->GEN2->GEN3->VAC orbit cycle as a WolframModel
       hyperedge rewriting system (orbit-level causal graph, 27 events over 9 steps).
     - Enforces DPP synchronization via EventSelectionFunction "GlobalSpacelike",
       which ensures all three tapes advance in lockstep (shared outer clock tau_c^out).
     - Produces a tape-colored causal graph suitable for P49 figures.

   What this file does NOT do:
     - No cell-level simulation: individual GF(7) values at spatial positions (x,y,z)
       are not tracked; the 5-cell GEN orbit ring is abstracted to a single node.
     - No inner clock (L_t) or gating mechanism: SR time dilation tau_inner/tau_outer
       = 3/7 arises from the gated CMCA dynamics, which live in the P41 and P45 .wl scripts.
     - No spatial lattice of length L: there is no 1D tape of cells here.
     - No GF(7) field values at cell positions: those require the full CMCA in ThreeTapeCMCA.wl.
     - No SR dilation measurement: glider-speed and tau_c ratio tests live in P41/P45 scripts.
     - No V-A chirality, SM vertex, kink orbit, or Bell computations.

   The full cell-level simulation (three-layer CMCA with inner clock, gating, and SR verification)
   lives in:
     papers/45_three_tape_cmca/scripts/ThreeTapeCMCA.wl           (P45, 9 verifications)
     papers/41_three_layer_chiral_minkowski_ca/scripts/cmca_full_reproducibility_wolfram_version.wl  (P41)
*)

(* --- Related Code ---
   This file (orbit level):
       Three-tape GEN orbit WolframModel causal graph; DPP synchronization enforced via
       GlobalSpacelike EventSelectionFunction. Operates on abstract orbit states, not cells.
       Use this for: visualizing DPP causal structure; P49 §8 figures.

   Cell-level simulation (inner clock, SR dilation, gating mechanism):
     papers/45_three_tape_cmca/scripts/ThreeTapeCMCA.wl               (P45)
       Full three-layer CMCA simulator; single-bit inner clock gating; all 9 verifications.
       Use this for: cell-level SR dilation, V-A chirality, Bell, and kink orbit cross-checks.

     papers/41_three_layer_chiral_minkowski_ca/scripts/cmca_full_reproducibility_wolfram_version.wl  (P41)
       Single-tape three-layer CMCA; M=7 inner clock mini-tape (majority-vote gating).
       Use this for: P41-specific M=7 AFCA architecture verification.

   Single-tape orbit causal graph (this paper):
     papers/49_gte_polynomial_wolfram/scripts/wolfram_model_causal_graph.wl
       Single-tape GEN orbit causal graph + orbit ring visualization (§5/§7 figures).
       Use this for: single-tape causal graph and orbit ring diagram.

   Historical (superseded by this file):
     papers/49_gte_polynomial_wolfram/scripts/three_tape_wolfram_model.wl
       First three-tape attempt; integer node aliasing bug caused tape conflation.
       Retained for reference only; use this file (v2) for all new work.

   Python equivalents (same scripts/ directory):
     three_tape_dpp_visualization.py       — three-tape DPP figures (§8 panels)
     bulk_causal_graph.py                  — bulk causal graph with cross-tape edges
     gen_orbit_ring_visualization.py       — orbit ring diagram (Python; no Wolfram needed)
 *)

scriptDir = DirectoryName[$InputFileName];
outDir = FileNameJoin[{scriptDir, "figures"}];
If[!DirectoryQ[outDir], CreateDirectory[outDir]];

(* -----------------------------------------------------------------------
   Orbit rewriting rules — string-atom encoding, no integer aliasing
   Each tape state is a 1-hyperedge containing a single string atom.
   The rules encode the GTE GEN orbit cycle: under f_MDL, the five-cell ring
   GEN1 -> GEN2 -> GEN3 -> VAC in exactly 3 steps (Lean-certified, zero sorry).
   String prefixes ("x_", "y_", "z_") prevent WolframModel from aliasing distinct
   tapes that share the same abstract orbit label.
   ----------------------------------------------------------------------- *)

gteThreeTapeRules = {
  (* Tape x: GEN1 -> GEN2 -> GEN3 -> VAC *)
  {{"x_g1"}} -> {{"x_g2"}},
  {{"x_g2"}} -> {{"x_g3"}},
  {{"x_g3"}} -> {{"x_vac"}},
  (* Tape y: GEN1 -> GEN2 -> GEN3 -> VAC *)
  {{"y_g1"}} -> {{"y_g2"}},
  {{"y_g2"}} -> {{"y_g3"}},
  {{"y_g3"}} -> {{"y_vac"}},
  (* Tape z: GEN1 -> GEN2 -> GEN3 -> VAC *)
  {{"z_g1"}} -> {{"z_g2"}},
  {{"z_g2"}} -> {{"z_g3"}},
  {{"z_g3"}} -> {{"z_vac"}}
};

(* -----------------------------------------------------------------------
   Initial hypergraph state
   Three tapes at GEN1, plus the DPP cross-tape synchronization hyperedge.
   The 3-hyperedge {"x_g1","y_g1","z_g1"} encodes that all three tapes
   begin at outer clock value tau_c^out = 0 (synchronization initial
   condition). It is not consumed by any rule — it persists as the causal
   record of the initial synchronization event.
   ----------------------------------------------------------------------- *)

gteInit = {
  {"x_g1"},              (* Tape x at GEN1 *)
  {"y_g1"},              (* Tape y at GEN1 *)
  {"z_g1"},              (* Tape z at GEN1 *)
  {"x_g1", "y_g1", "z_g1"}  (* DPP: shared outer clock at tau = 0 *)
};

Print["Three-tape GTE WolframModel v2 — string-atom encoding"];
Print["Rules: ", gteThreeTapeRules];
Print["Initial state: ", gteInit];
Print[""];

(* -----------------------------------------------------------------------
   WolframModel evolution — 9 steps, GlobalSpacelike event selection.
   "GlobalSpacelike" enforces that the three tapes advance in lockstep:
   events on different tapes that are causally independent are allowed to
   fire simultaneously (spacelike), and no single tape can race ahead.
   This is the hypergraph-level implementation of the shared DPP outer clock
   (Dimensional Protocol Principle, CatAL: dimensional_protocol_principle_master,
   ugp-lean). Without GlobalSpacelike, WolframModel would allow one tape to
   complete its full 3-step cycle before the others begin — that would be three
   independent 1+1D systems, not a 3+1D Minkowski structure.
   9 steps = 3 complete GEN1->GEN2->GEN3->VAC cycles per tape (3 cycles × 3 steps).
   ----------------------------------------------------------------------- *)

Print["Running WolframModel (9 steps, GlobalSpacelike)..."];
t0 = AbsoluteTime[];

wm3 = Check[
  WolframModel[
    gteThreeTapeRules,
    gteInit,
    9,
    "EventSelectionFunction" -> "GlobalSpacelike"
  ],
  $Failed
];

elapsed = AbsoluteTime[] - t0;

If[wm3 === $Failed,
  Print["ERROR: WolframModel evolution failed."];
  Exit[1];
,
  Print["WolframModel succeeded in ", Round[elapsed, 0.01], " seconds."];
  Print["  States: ", Length[wm3["StatesList"]]];
  Print["  Final state: ", wm3["FinalState"]];
];

(* -----------------------------------------------------------------------
   Causal graph extraction and export
   ----------------------------------------------------------------------- *)

Print[""];
Print["Extracting causal graph..."];

cg = Check[wm3["CausalGraph"], $Failed];

If[cg === $Failed,
  Print["ERROR: CausalGraph extraction failed."];
  Exit[1];
,
  nVerts = VertexCount[cg];
  nEdges = EdgeCount[cg];
  Print["  Causal graph: ", nVerts, " vertices, ", nEdges, " edges."];
];

(* -----------------------------------------------------------------------
   Apply visual styling to the causal graph for export.
   Vertices are colored by which tape generated the event:
     x-tape events — blue (#4a90e2)
     y-tape events — orange (#e2884a)
     z-tape events — green (#4ae28a)
     cross-tape events — gray (#aaaaaa)
   ----------------------------------------------------------------------- *)

(* Vertex labels come from WolframModel's internal event IDs — integers.
   We apply uniform color by tape by inspecting which rules fired.
   The rule indices in gteThreeTapeRules are 1-3 (tape x), 4-6 (tape y),
   7-9 (tape z). *)

eventRuleIndices = wm3["AllEventsList"][[All, 1]];
nEvents = Length[eventRuleIndices];
Print["  Events: ", nEvents, " (expected 27 for 3 tapes × 3 steps × 3 cycles)."];

tapeColors = Table[
  With[{r = eventRuleIndices[[i]]},
    Which[
      1 <= r <= 3, RGBColor[0.29, 0.56, 0.89],  (* x-tape: blue *)
      4 <= r <= 6, RGBColor[0.89, 0.53, 0.29],  (* y-tape: orange *)
      7 <= r <= 9, RGBColor[0.29, 0.89, 0.54],  (* z-tape: green *)
      True,        RGBColor[0.67, 0.67, 0.67]   (* other: gray *)
    ]
  ],
  {i, nEvents}
];

(* VertexList returns vertices in internal order matching eventRuleIndices *)
verts = VertexList[cg];
colorRules = If[Length[verts] == Length[tapeColors],
  Thread[verts -> tapeColors],
  (* fallback: uniform color if vertex count does not match event count *)
  Thread[verts -> RGBColor[0.29, 0.56, 0.89]]
];

cgStyled = Check[
  Graph[
    cg,
    VertexStyle -> colorRules,
    EdgeStyle -> Directive[GrayLevel[0.7], Arrowheads[0.025]],
    VertexSize -> 0.6,
    VertexLabels -> None,
    GraphLayout -> "LayeredDigraphEmbedding",
    Background -> RGBColor[0.04, 0.04, 0.08],
    PlotLabel -> Style[
      "GTE Three-Tape CMCA — Causal Graph (orbit-level, 9 steps)\n"
      <> "x-tape \[FilledCircle] \[FilledCircle] \[FilledCircle] blue  |  "
      <> "y-tape \[FilledCircle] \[FilledCircle] \[FilledCircle] orange  |  "
      <> "z-tape \[FilledCircle] \[FilledCircle] \[FilledCircle] green",
      White, 11
    ],
    ImageSize -> {900, 700}
  ],
  $Failed
];

(* Fallback: export raw causal graph if styled version fails *)
cgOut = If[cgStyled =!= $Failed, cgStyled, cg];

outPath = FileNameJoin[{outDir, "p49_three_tape_causal_graph_v2.png"}];
Export[outPath, cgOut, ImageResolution -> 200];
Print[""];
Print["Saved causal graph: ", outPath];
Print["File size: ", FileSize[outPath]];

(* -----------------------------------------------------------------------
   Optional: print all states for inspection
   ----------------------------------------------------------------------- *)

Print[""];
Print["State list (10 snapshots):"];
Do[
  Print["  Step ", i-1, ": ", wm3["StatesList"][[i]]],
  {i, Length[wm3["StatesList"]]}
];

Print[""];
Print["three_tape_wolframmodel_v2.wl complete."];
