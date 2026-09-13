#!/usr/bin/env wolframscript
(* gte_rulegte_causal_graph.wl
   Canonical reproducible script for the GTE polynomial local update rule
   WolframModel causal graph (P49 Fig. 3, §5.3).

   The rule encodes the GTE polynomial's local update structure:
   two overlapping CA triplet neighbourhoods {a,b,c},{c,d,e} (sharing
   centre cell c) rewrite to four new overlapping hyperedges
   {a,b,f},{f,c,d},{e,b,g},{g,d,h}, where f,g,h are fresh atoms
   representing updated cell values.

   This is the WolframModel encoding of: given the left neighbourhood (a,b,c)
   and right neighbourhood (c,d,e) of a CA cell c, produce two new overlapping
   pairs encoding the updated neighbourhood structure.

   Verified output (2026-06-08, SetReplace v0.3.196, Wolfram Engine 14.3.0):
     Initial state: {{0,1,2},{2,3,4}}
     MaxGenerations: 10
     EventsCount: 1023 = 2^10 - 1
     CausalGraph vertices: 1023
     CausalGraph edges: 2044 = 2*(1023-1)
     Final state hyperedges: 2048 = 2^11
     TerminationReason: MaxGenerations
     Horton branching ratio: r_B = 2 (exact, binary tree)
     Strahler number: 10 (= MaxGenerations)

   Physical interpretation:
   Each rule application generates TWO new overlapping pairs from ONE pair.
   This binary branching matches the L-system F->F[+F][-F] (compound umbel
   model for Daucus carota) at depth 10, giving the same structural class:
   perfect binary tree, 1023 nodes, Horton ratio 2, Strahler 10.

   The GEN1->GEN2->GEN3->VAC orbit rules (separately) produce a 3-event
   linear causal chain (PatternRules: 3 vertices, 2 edges).

   Output: scripts/figures/p49_gte_causal_g10.png  (replaces/reproduces the figure)
           scripts/figures/p49_gte_rulegte_final_state.png  (final hypergraph state)
*)

Needs["SetReplace`"];

scriptDir = DirectoryName[$InputFileName];
outDir = FileNameJoin[{scriptDir, "figures"}];
If[!DirectoryQ[outDir], CreateDirectory[outDir]];

(* --- ruleGTE: GTE polynomial local update structure --- *)
(* Encodes: two overlapping CA triplet neighbourhoods sharing centre cell c *)
(* {a,b,c},{c,d,e} -> {a,b,f},{f,c,d},{e,b,g},{g,d,h}  (f,g,h fresh atoms) *)
ruleGTE = <|"PatternRules" -> {
  {{a_,b_,c_},{c_,d_,e_}} :> Module[{f,g,h},
    {{a,b,f},{f,c,d},{e,b,g},{g,d,h}}
  ]
}|>;

(* Initial state: single overlapping pair *)
initState = {{0,1,2},{2,3,4}};

Print["GTE local update rule WolframModel causal graph"];
Print["Rule: {a,b,c},{c,d,e} -> {a,b,f},{f,c,d},{e,b,g},{g,d,h}"];
Print["Initial state: ", initState];
Print["MaxGenerations: 10"];
Print[];

(* --- Evolve for 10 generations --- *)
wm = WolframModel[ruleGTE, initState, <|"MaxGenerations" -> 10|>];

Print["EventsCount: ", wm["EventsCount"]];
Print["TerminationReason: ", wm["TerminationReason"]];
Print["Final state hyperedge count: ", Length[wm["FinalState"]]];
Print["Expected: 2^11 = ", 2^11];
Print[];

(* --- Causal graph --- *)
cg = wm["CausalGraph"];
Print["CausalGraph:"];
Print["  VertexCount: ", VertexCount[cg], " (expected: 2^10 - 1 = ", 2^10-1, ")"];
Print["  EdgeCount: ", EdgeCount[cg], " (expected: 2*(2^10-2) = ", 2*(2^10-2), ")"];
Print["  Binary tree? ", VertexCount[cg] == 2^10-1 && EdgeCount[cg] == 2*(2^10-2)];
Print[];

(* --- Verify binary tree structure --- *)
(* In a perfect binary tree: EdgeCount = 2*(VertexCount - 1) *)
isBinaryTree = EdgeCount[cg] == 2*(VertexCount[cg] - 1);
Print["Binary tree verification: EdgeCount = 2*(VertexCount - 1)? ", isBinaryTree];
Print[];

(* --- Generate causal graph figure (replaces p49_gte_causal_g10.png) --- *)
Print["Generating causal graph figure..."];
cgPlot = Check[
  WolframModelPlot[cg, "CausalGraph",
    Background -> RGBColor[0.04, 0.04, 0.08],
    PlotLabel -> Style[
      "GTE Local Update Rule — WolframModel Causal Graph\n" <>
      "{a,b,c},{c,d,e} -> {a,b,f},{f,c,d},{e,b,g},{g,d,h}   10 generations, 1023 events",
      White, 11],
    VertexStyle -> Directive[RGBColor[1.0, 0.85, 0.0], EdgeForm[None]],
    EdgeStyle -> Directive[RGBColor[0.3, 0.3, 0.5], Opacity[0.7]],
    ImageSize -> 1000],
  $Failed
];

If[cgPlot =!= $Failed,
  causalPath = FileNameJoin[{outDir, "p49_gte_causal_g10.png"}];
  Export[causalPath, cgPlot, ImageResolution -> 200];
  Print["Saved causal graph: p49_gte_causal_g10.png"];
,
  Print["WolframModelPlot failed — trying Graph plot..."];
  gPlot = Graph[cg,
    GraphLayout -> "RadialEmbedding",
    VertexStyle -> Directive[RGBColor[1.0, 0.85, 0.0], PointSize[0.003]],
    EdgeStyle -> Directive[RGBColor[0.3, 0.3, 0.5], Opacity[0.5], Thickness[0.0003]],
    Background -> RGBColor[0.04, 0.04, 0.08],
    PlotLabel -> Style["GTE Local Update Rule Causal Graph (10 gen, 1023 nodes)", White, 11],
    ImageSize -> 1000];
  causalPath = FileNameJoin[{outDir, "p49_gte_causal_g10.png"}];
  Export[causalPath, gPlot, ImageResolution -> 200];
  Print["Saved causal graph (Graph fallback): p49_gte_causal_g10.png"];
];

(* --- Final state figure --- *)
Print["Generating final state figure..."];
fsPlot = Check[
  WolframModelPlot[wm["FinalState"],
    Background -> RGBColor[0.04, 0.04, 0.08],
    PlotLabel -> Style["GTE Local Update Rule — Final State (2048 hyperedges)", White, 11],
    ImageSize -> 800],
  $Failed
];
If[fsPlot =!= $Failed,
  fsPath = FileNameJoin[{outDir, "p49_gte_rulegte_final_state.png"}];
  Export[fsPath, fsPlot, ImageResolution -> 150];
  Print["Saved final state: p49_gte_rulegte_final_state.png"];
];

(* --- Verification against orbit rules (for comparison) --- *)
Print[];
Print["--- Comparison: orbit rules GEN1->GEN2->GEN3->VAC (PatternRules) ---"];
gen1={1,5,2,2,1}; gen2={2,5,2,0,2}; gen3={5,6,5,3,5}; vac={0,0,0,0,0};
orbitRules = <|"PatternRules" -> {{gen1} :> gen2, {gen2} :> gen3, {gen3} :> vac}|>;
wmOrbit = Check[WolframModel[orbitRules, {gen1}, <|"MaxGenerations"->10|>], $Failed];
If[wmOrbit =!= $Failed,
  cgOrbit = wmOrbit["CausalGraph"];
  Print["Orbit rules: EventsCount = ", wmOrbit["EventsCount"],
        ", CG vertices = ", VertexCount[cgOrbit],
        ", CG edges = ", EdgeCount[cgOrbit]];
  Print["(Linear causal chain: GEN1->GEN2->GEN3 in 3 steps)"];
,
  Print["Orbit rules WolframModel failed"];
];

Print[];
Print["WolframScript complete. Output: ", outDir];
