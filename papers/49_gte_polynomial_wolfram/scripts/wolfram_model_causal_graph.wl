#!/usr/bin/env wolframscript
(* wolfram_model_causal_graph.wl
   WolframModel causal graph of the GTE GEN orbit.
   
   Encodes the GTE three-generation orbit GEN1→GEN2→GEN3→VAC as a SetReplace
   hyperedge rewriting rule and generates the causal graph at 10 generations.
   
   Requires Wolfram Engine 14.3.0 with SetReplace v0.3.196.
   Use Needs["SetReplace`"] (local package), NOT ResourceFunction["WolframModel"].
   
   GEN orbit values (Lean-certified, zero sorry):
     GEN1 = {1, 5, 2, 2, 1}
     GEN2 = {2, 5, 2, 0, 2}
     GEN3 = {5, 6, 5, 3, 5}
     VAC  = {0, 0, 0, 0, 0}
   
   Output files saved to figures/ subdirectory:
     p49_gte_causal_g10.png   — causal graph at 10 generations
     p49_gte_final_state_g10.png — final hypergraph state
     p49_gte_orbit_rings_v2.png — ring state diagram (alternative to Python version)
*)

Needs["SetReplace`"];

(* --- Scope and Limitations ---
   This script produces a single-tape orbit causal graph and a state-transition
   ring diagram. It is a visualization tool, not a physical dynamics simulator.

   What this file DOES:
     - Encodes the single-tape GEN orbit (GEN1->GEN2->GEN3->VAC) as a WolframModel
       5-node hyperedge rewriting rule and evolves it for 10 generations.
     - Attempts native WolframModel causal graph extraction; falls back to a
       manually constructed linear causal graph if WolframModel fails (version guard).
     - Generates the orbit state-transition ring diagram (orbit_rings_v2.png) as a
       supplementary figure showing the four-state ring structure.

   What this file does NOT do:
     - No three-tape coupling: only a single tape is simulated. For three-tape
       orbit-level causal graphs with DPP synchronization, see three_tape_wolframmodel_v2.wl.
     - No inner clock or gating: SR dilation, V-A chirality, and CHSH Bell tests
       live in the P41 and P45 CMCA scripts.
     - No GF(7) cell-level dynamics: orbit states are abstract 5-node hyperedges.
     - The causal graph shows EVENT causality (which rewrite caused which) — it does
       NOT show spatial adjacency between GF(7) cells.

   Causal graph semantics in GTE terms:
     A directed edge A->B in the causal graph means event B consumed a hyperedge
     produced by event A. In the orbit interpretation: the rewrite that advanced
     the tape from GEN_k to GEN_{k+1} causally precedes the next rewrite.
     The causal graph thus records the temporal ordering of orbit state transitions.
*)

(* --- Related Code ---
   This file:
       Single-tape GEN orbit WolframModel causal graph (10 generations) and orbit
       state-transition ring diagram. Visualization tool; no physical dynamics.
       Use this for: §5 causal graph figure and §7 orbit ring figure (Wolfram version).

   Python equivalent (no Wolfram Engine required):
     papers/49_gte_polynomial_wolfram/scripts/gen_orbit_ring_visualization.py
       Produces the same orbit ring diagram (p49_gte_orbit_rings_v2.png) via matplotlib.
       Use this for: orbit ring figure generation without Wolfram Engine.

   Three-tape version (this paper):
     papers/49_gte_polynomial_wolfram/scripts/three_tape_wolframmodel_v2.wl
       Three-tape orbit causal graph with DPP synchronization (GlobalSpacelike).
       Use this for: three-tape DPP causal structure and §8 figures.

   Historical three-tape attempt (superseded):
     papers/49_gte_polynomial_wolfram/scripts/three_tape_wolfram_model.wl
       First three-tape attempt; integer node aliasing bug. Superseded by v2.

   Cell-level simulation:
     papers/45_three_tape_cmca/scripts/ThreeTapeCMCA.wl               (P45)
       Full three-layer CMCA with inner clock gating; SR dilation and 9 verifications.
       Use this for: cell-level physics; SR, V-A, and kink orbit cross-checks.
 *)

scriptDir = DirectoryName[$InputFileName];
outDir = FileNameJoin[{scriptDir, "figures"}];
If[!DirectoryQ[outDir], CreateDirectory[outDir]];

(* GEN orbit states as hyperedges on 5 nodes.
   Each GEN state is represented as a 5-element list encoding the GF(7) cell values
   of the 5-cell orbit ring. WolframModel treats these lists as hyperedges. The four
   states form the complete PSC kink orbit under f_MDL (Lean-certified, zero sorry,
   ugp-lean: fmdl_gen1_to_gen2, fmdl_gen1_is_garden_of_eden). *)
gen1 = {1, 5, 2, 2, 1};
gen2 = {2, 5, 2, 0, 2};
gen3 = {5, 6, 5, 3, 5};
vac  = {0, 0, 0, 0, 0};

(* Rewriting rules: each orbit state maps to the next under f_MDL.
   WolframModel interprets each rule as: consume the LHS hyperedge, produce the RHS.
   The 3-step orbit (GEN1->GEN2->GEN3->VAC) reflects the three-generation decay
   of the GTE PSC kink; VAC ({0,0,0,0,0}) is the true vacuum (zero winding). *)
orbitRules = {
  gen1 -> gen2,
  gen2 -> gen3,
  gen3 -> vac
};

(* Initial hypergraph: single tape at GEN1 *)
initState = {gen1};

Print["GTE GEN orbit WolframModel causal graph"];
Print["Initial state: ", initState];
Print["Rules: ", orbitRules];

(* Attempt WolframModel evolution for 10 generations *)
Print["\nAttempting WolframModel evolution (10 generations)..."];
wm = Check[
  WolframModel[orbitRules, initState, 10],
  $Failed
];

If[wm === $Failed,
  Print["WolframModel failed — trying SetReplace directly..."];
  
  sr = Check[SetReplace[initState, orbitRules, 10], $Failed];
  Print["SetReplace result: ", sr];
  
  Print["Generating schematic causal graph via Graph[]..."];
  
  (* Manual causal graph: each step causes the next *)
  causalEdges = Table[
    DirectedEdge[
      Style[Row[{"Step ", t}], FontSize -> 10, FontColor -> White],
      Style[Row[{"Step ", t+1}], FontSize -> 10, FontColor -> White]
    ],
    {t, 0, 9}
  ];
  
  g = Graph[
    causalEdges,
    GraphLayout -> "LayeredDigraphEmbedding",
    VertexStyle -> Directive[RGBColor[0.2, 0.4, 0.8], EdgeForm[White]],
    EdgeStyle -> Directive[White, Arrowheads[0.03]],
    Background -> RGBColor[0.04, 0.04, 0.08],
    PlotLabel -> Style["GTE GEN Orbit Causal Graph (10 generations)", White, 14],
    ImageSize -> 800
  ];
  
  causalPath = FileNameJoin[{outDir, "p49_gte_causal_g10.png"}];
  Export[causalPath, g, ImageResolution -> 200];
  Print["Saved schematic causal graph: p49_gte_causal_g10.png"];
,
  Print["WolframModel succeeded."];
  Print["  States count: ", wm["StatesList"] // Length];
  
  (* Causal graph *)
  cg = Check[wm["CausalGraph"], $Failed];
  
  If[cg =!= $Failed,
    cgPlot = Check[
      WolframModelPlot[cg, "CausalGraph",
        Background -> RGBColor[0.04, 0.04, 0.08],
        PlotLabel -> Style["GTE GEN Orbit Causal Graph (10 generations)", White, 14],
        ImageSize -> 800],
      $Failed
    ];
    If[cgPlot =!= $Failed,
      causalPath = FileNameJoin[{outDir, "p49_gte_causal_g10.png"}];
      Export[causalPath, cgPlot, ImageResolution -> 200];
      Print["Saved: p49_gte_causal_g10.png"];
    ,
      Print["CausalGraph plot failed."];
    ];
  ,
    Print["CausalGraph extraction failed."];
  ];
  
  (* Final state *)
  finalState = wm["FinalState"];
  Print["  Final state: ", finalState];
  
  fsPlot = Check[
    WolframModelPlot[finalState,
      Background -> RGBColor[0.04, 0.04, 0.08],
      PlotLabel -> Style["GTE Final State (10 generations)", White, 14],
      ImageSize -> 600],
    $Failed
  ];
  If[fsPlot =!= $Failed,
    fsPath = FileNameJoin[{outDir, "p49_gte_final_state_g10.png"}];
    Export[fsPath, fsPlot, ImageResolution -> 200];
    Print["Saved: p49_gte_final_state_g10.png"];
  ];
];

(* Generate orbit state transition diagram as a Graph.
   This ring diagram is a state-space view (which state follows which), distinct from
   the causal graph above (which event caused which). The ring shows the topology of
   the GEN orbit as a directed 4-cycle terminating at VAC; it is NOT a causal graph. *)
Print["\nGenerating orbit state transition diagram..."];
stateLabels = {
  {gen1, "GEN₁\n[1,5,2,2,1]"},
  {gen2, "GEN₂\n[2,5,2,0,2]"},
  {gen3, "GEN₃\n[5,6,5,3,5]"},
  {vac,  "VAC\n[0,0,0,0,0]"}
};

stateColors = {
  RGBColor[1.0, 0.2, 0.2],   (* GEN1 — red *)
  RGBColor[1.0, 0.53, 0.0],  (* GEN2 — orange *)
  RGBColor[0.0, 0.9, 1.0],   (* GEN3 — cyan *)
  RGBColor[0.4, 0.4, 0.4]    (* VAC — gray *)
};

orbitGraph = Graph[
  {"GEN₁", "GEN₂", "GEN₃", "VAC"},
  {
    DirectedEdge["GEN₁", "GEN₂"],
    DirectedEdge["GEN₂", "GEN₃"],
    DirectedEdge["GEN₃", "VAC"]
  },
  VertexStyle -> Thread[{"GEN₁", "GEN₂", "GEN₃", "VAC"} -> stateColors],
  VertexLabels -> "Name",
  VertexLabelStyle -> Directive[White, FontSize -> 12, Bold],
  EdgeStyle -> Directive[White, Arrowheads[0.05]],
  GraphLayout -> "LinearEmbedding",
  Background -> RGBColor[0.04, 0.04, 0.08],
  PlotLabel -> Style["GTE Three-Generation Orbit (f_MDL, 5-cell ring)", White, 13],
  ImageSize -> {700, 200}
];

ringsPath = FileNameJoin[{outDir, "p49_gte_orbit_rings_v2.png"}];
Export[ringsPath, orbitGraph, ImageResolution -> 200];
Print["Saved: p49_gte_orbit_rings_v2.png"];

Print["\nWolframScript complete. Output in: ", outDir];
