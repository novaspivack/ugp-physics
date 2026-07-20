#!/usr/bin/env wolframscript
(* three_tape_wolfram_model.wl
   Three-tape WolframModel causal graph encoding of the GEN orbit.
   
   Encodes the GEN orbit GEN1->GEN2->GEN3->VAC as a SetReplace hyperedge
   rewriting rule. Each tape state is a 5-hyperedge; three tapes run in
   parallel with a shared DPP clock coupling.
   
   Requires Wolfram Engine 14.3.0 with SetReplace v0.3.196.
   Use Needs["SetReplace`"] (local package), NOT ResourceFunction.
   
   On failure (trivial output or unsupported API), prints diagnostic and exits 0.
*)

(* --- Related Code ---
   This file (historical — superseded):
       First attempt at three-tape orbit WolframModel encoding. Contains an integer
       node aliasing bug: raw GF(7) values 0-6 used as node IDs caused WolframModel
       to conflate distinct cells sharing the same value. Retained for reference only.

   Corrected version (use this instead):
     papers/49_gte_polynomial_wolfram/scripts/three_tape_wolframmodel_v2.wl
       Fixes the aliasing bug via string-atom node IDs ("x_g1", "y_g2", etc.).
       Use this for: three-tape DPP causal structure and all P49 §8 figures.

   Single-tape version (this paper):
     papers/49_gte_polynomial_wolfram/scripts/wolfram_model_causal_graph.wl
       Single-tape GEN orbit causal graph + orbit ring diagram.
       Use this for: §5 and §7 figures.

   Cell-level simulation:
     papers/45_three_tape_cmca/scripts/ThreeTapeCMCA.wl               (P45)
       Full three-layer CMCA with inner clock gating; SR dilation and 9 verifications.
       Use this for: cell-level physics that the orbit-level scripts do not cover.
 *)

Needs["SetReplace`"];

scriptDir = DirectoryName[$InputFileName];
outDir = FileNameJoin[{scriptDir, "figures"}];
If[!DirectoryQ[outDir], CreateDirectory[outDir]];

(* -----------------------------------------------------------------------
   Step 1: Single-tape GEN orbit as SetReplace rule
   GEN1 = {1,5,2,2,1}, GEN2 = {2,5,2,0,2}, GEN3 = {5,6,5,3,5}, VAC = {0,0,0,0,0}
   Encode as: rewrite a hyperedge on 5 nodes labeled by their Z7 values
   -----------------------------------------------------------------------*)

(* Encode each orbit state as a directed hyperedge: {a,b,c,d,e} *)
gen1 = {1,5,2,2,1};
gen2 = {2,5,2,0,2};
gen3 = {5,6,5,3,5};
vac  = {0,0,0,0,0};

(* Rewrite rule: replace a hyperedge matching GEN1 pattern -> GEN2, etc. *)
(* Use symbolic node names for SetReplace matching *)
rule1 = {1,5,2,2,1} -> {2,5,2,0,2};
rule2 = {2,5,2,0,2} -> {5,6,5,3,5};
rule3 = {5,6,5,3,5} -> {0,0,0,0,0};

(* Initial hypergraph: three parallel tapes, each starting at GEN1 *)
initSingleTape = {{1,5,2,2,1}};

(* Try SetReplace evolution for single tape *)
Print["Attempting single-tape SetReplace evolution..."];
singleResult = Check[
  SetReplace[initSingleTape, {rule1, rule2, rule3}, 3],
  $Failed
];
Print["Single tape result: ", singleResult];

(* -----------------------------------------------------------------------
   Step 2: Three-tape system
   Three tapes, each evolving GEN1->GEN2->GEN3->VAC, plus cross-tape edges
   -----------------------------------------------------------------------*)

(* Three-tape initial state: each tape gets distinct node labels *)
(* Tape x: nodes 10-14, Tape y: nodes 20-24, Tape z: nodes 30-34 *)
(* Cross-tape DPP clock: shared node 0 connects to all three tapes *)

initThreeTape = {
  {0, 10, 15, 12, 12, 11},  (* Tape x: clock + GEN1 values *)
  {0, 20, 25, 22, 22, 21},  (* Tape y: clock + GEN1 values *)
  {0, 30, 35, 32, 32, 31}   (* Tape z: clock + GEN1 values *)
};

(* rules3tape removed: placeholder patterns {10,15,12,...}+1 did not implement
   f_MDL and were never wired into the execution path. *)

(* Simpler: encode three-tape as three hyperedges with shared clock node *)
(* GEN1 x GEN1 x GEN1 -> GEN2 x GEN2 x GEN2 -> GEN3 x GEN3 x GEN3 -> VAC^3 *)

(* Use abstract node IDs: tape_id * 100 + orbit_id * 10 + cell_id *)
(* This is the three-tape product orbit as a SetReplace sequence *)

genOrbitEncoding = {
  (* Generation 1: node IDs 111..115, 211..215, 311..315 *)
  {111, 115, 112, 112, 111},  (* tape x, GEN1 *)
  {211, 215, 212, 212, 211},  (* tape y, GEN1 *)
  {311, 315, 312, 312, 311},  (* tape z, GEN1 *)
  {111, 211, 311}             (* DPP cross-tape clock edge *)
};

(* Rewrite each tape's GEN1 hyperedge to GEN2 simultaneously *)
threeTapeRules = {
  (* Tape x: GEN1 -> GEN2 *)
  {111, 115, 112, 112, 111} -> {121, 125, 122, 120, 122},
  (* Tape y: GEN1 -> GEN2 *)
  {211, 215, 212, 212, 211} -> {221, 225, 222, 220, 222},
  (* Tape z: GEN1 -> GEN2 *)
  {311, 315, 312, 312, 311} -> {321, 325, 322, 320, 322},
  (* GEN2 -> GEN3 for each tape *)
  {121, 125, 122, 120, 122} -> {151, 156, 155, 153, 155},
  {221, 225, 222, 220, 222} -> {251, 256, 255, 253, 255},
  {321, 325, 322, 320, 322} -> {351, 356, 355, 353, 355},
  (* GEN3 -> VAC for each tape *)
  {151, 156, 155, 153, 155} -> {100, 100, 100, 100, 100},
  {251, 256, 255, 253, 255} -> {200, 200, 200, 200, 200},
  {351, 356, 355, 353, 355} -> {300, 300, 300, 300, 300}
};

Print["Attempting three-tape SetReplace evolution..."];
threeTapeResult = Check[
  SetReplace[genOrbitEncoding, threeTapeRules, 3],
  $Failed
];
Print["Three-tape result after 3 steps: ", threeTapeResult];

(* -----------------------------------------------------------------------
   Step 3: Attempt WolframModelPlot on single-tape GEN orbit
   -----------------------------------------------------------------------*)

Print["Attempting WolframModel single-tape evolution..."];
wm1 = Check[
  WolframModel[
    {rule1, rule2, rule3},
    initSingleTape,
    3
  ],
  $Failed
];

If[wm1 =!= $Failed,
  Print["WolframModel succeeded for single tape."];
  (* Try to generate causal graph *)
  cg = Check[
    WolframModelPlot[wm1["CausalGraph"], "CausalGraph"],
    $Failed
  ];
  If[cg =!= $Failed,
    Print["CausalGraph plot succeeded."];
    Export[FileNameJoin[{outDir, "p49_three_tape_wolframmodel_causal.png"}], cg,
      ImageResolution -> 150];
    Print["Saved: p49_three_tape_wolframmodel_causal.png"];
  ,
    Print["CausalGraph plot failed or not supported."];
  ];
,
  Print["WolframModel failed for single tape."];
];

(* -----------------------------------------------------------------------
   Step 4: Attempt WolframModel with three-tape rules
   -----------------------------------------------------------------------*)

Print["Attempting WolframModel three-tape evolution..."];
wm3 = Check[
  WolframModel[
    threeTapeRules,
    genOrbitEncoding,
    3
  ],
  $Failed
];

If[wm3 =!= $Failed,
  Print["WolframModel succeeded for three-tape system."];
  cg3 = Check[
    WolframModelPlot[wm3["CausalGraph"], "CausalGraph"],
    $Failed
  ];
  If[cg3 =!= $Failed,
    Print["Three-tape CausalGraph plot succeeded."];
    Export[FileNameJoin[{outDir, "p49_three_tape_wolframmodel_causal_3tape.png"}], cg3,
      ImageResolution -> 150];
    Print["Saved: p49_three_tape_wolframmodel_causal_3tape.png"];
  ,
    Print["Three-tape CausalGraph plot failed."];
  ];
,
  Print["WolframModel failed for three-tape system."];
];

Print["WolframScript complete."];
