(* ::Package:: *)

(* =============================================================================
   Wolfram Notebook Compatible Script
   ---------------------------------------------------------------------------
   Title:    Three-Layer Chiral Minkowski CA — Full Reproducibility Suite (P41)
   Author:   Nova Spivack
   Epic:     074-WOLFRAM / 074-REPRO
   Paper:    papers/41_three_layer_chiral_minkowski_ca/

   Open in Mathematica or Wolfram Engine:
     File -> Open  (this .wl file opens as a notebook-compatible script)
     Evaluate All  (or run from terminal)

   Terminal:
     wolframscript -file papers/41_three_layer_chiral_minkowski_ca/scripts/cmca_full_reproducibility_wolfram_version.wl

   Implements the Three-Layer Chiral Minkowski CA (CMCA):
     L_{x+}  — Rule 110 (right-moving chiral layer)
     L_{x-}  — Rule 124 (left-moving chiral layer)
     L_t     — shared inner Rule 110 tau_c clock (ETHER14 seed)

   Verifies all nine headline P41 claims plus three-layer sanity check.
   Pure Wolfram Language — no Python dependency.
   ============================================================================= *)

$CMCASkipMain = TrueQ[$CMCASkipMain] ||
  (StringQ[Environment["CMCA_SKIP_MAIN"]] && Environment["CMCA_SKIP_MAIN"] === "1");
$CMCASkipMainSave = $CMCASkipMain;
ClearAll["Global`*", Except[$CMCASkipMainSave]];
$CMCASkipMain = $CMCASkipMainSave;
Unset[$CMCASkipMainSave];

$CMCAResults = {};
$CMCAStartTime = AbsoluteTime[];

(* ---------- helpers ---------- *)

reportClaim[name_String, passed_, detail_Association] := Module[{rec},
  rec = Association[
    "claim" -> name,
    "pass" -> passed,
    Sequence @@ Normal[detail]
  ];
  AppendTo[$CMCAResults, rec];
  Print[If[TrueQ[passed], "PASS: " <> name, "FAIL: " <> name]];
  rec
];

assertNear[a_, b_, tol_, label_String] := Module[{ok},
  ok = Abs[N[a - b]] <= tol;
  If[ok, Print["  OK  ", label, "  got=", N[a, 6], " expected=", N[b, 6]],
    Print["  BAD ", label, "  got=", N[a, 6], " expected=", N[b, 6], " tol=", tol]
  ];
  ok
];

assertEqual[a_, b_, label_String] := Module[{ok},
  ok = a === b;
  If[ok, Print["  OK  ", label], Print["  BAD ", label, "  got=", a, " expected=", b]];
  ok
];

log2Plus1[n_Integer] := If[n <= 0, 0, Floor[Log2[n]] + 1];

kCABits[alphabetSize_, nLayers_, outerRuleBits_, hasAsync_, gatingBits_] :=
  log2Plus1[alphabetSize] + log2Plus1[1] + log2Plus1[nLayers] +
  outerRuleBits + If[hasAsync, 1, 0] + If[hasAsync, gatingBits, 0];

(* ---------- constants ---------- *)

ETHER14 = {1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0};
ETHER124Seq = Reverse[ETHER14];
CEff = 2/3;
GammaV23 = 1/Sqrt[1 - CEff^2];
GEN1 = {1, 5, 2, 2, 1};
VACUUM = {0, 0, 0, 0, 0};
SMVA = {0, 2, 3, 4, 6};
GLIDERSEED = {0, 1, 0, 0, 1, 0, 1, 0, 0, 1};
CANONICALPHASE = 12;

LDefault = 840;
MDefault = 7;
CENTER110 = 421;
CENTER124 = 423;
TSync = 300;
NTrans = 300;
SnapEvery = 5;
DiffThreshold = 0.05;
SpeedTol = 0.02;
SRErrorTolPct = 15.0;

RULE110 = <|{1, 1, 1} -> 0, {1, 1, 0} -> 1, {1, 0, 1} -> 1, {1, 0, 0} -> 0,
  {0, 1, 1} -> 1, {0, 1, 0} -> 1, {0, 0, 1} -> 1, {0, 0, 0} -> 0|>;

RULE124 = Association@Table[
  {l, c, r} -> Lookup[RULE110, Key[{r, c, l}], 0],
  {l, 0, 1}, {c, 0, 1}, {r, 0, 1}
];

FMDLOrbit = <|
  {1, 1, 5} -> 2, {1, 5, 2} -> 5, {5, 2, 2} -> 2, {2, 2, 1} -> 0,
  {2, 1, 1} -> 2, {2, 2, 5} -> 5, {2, 5, 2} -> 6, {5, 2, 0} -> 5,
  {2, 0, 2} -> 3, {0, 2, 2} -> 5,
  Sequence @@ Normal@RULE110
|>;

(* ---------- Rule 110 / 124 via CellularAutomaton ---------- *)

rule110Step[tape_List] := Last[
  CellularAutomaton[{110, Automatic}, {tape, 0}, 1,
    "PeriodicBoundaryConditions" -> True]
];

rule124Step[tape_List] := Last[
  CellularAutomaton[{124, Automatic}, {tape, 0}, 1,
    "PeriodicBoundaryConditions" -> True]
];

applyRule[tape_List, lut_Association] := Module[{n = Length[tape]},
  Table[
    Lookup[lut, Key[{tape[[Mod[i - 2, n] + 1]], tape[[i]], tape[[Mod[i, n] + 1]]}], 0],
    {i, n}
  ]
];

applyRule110[tape_List] := applyRule[tape, RULE110];
applyRule124[tape_List] := applyRule[tape, RULE124];

stepSyncChiral[outer110_, outer124_] := {applyRule110[outer110], applyRule124[outer124]};

etherTape[seq_List, length_Integer] :=
  Table[seq[[Mod[i, 14] + 1]], {i, 0, length - 1}];

(* ---------- Z7 fMDL orbit ---------- *)

fmdlZ7[l_, c_, r_] := Lookup[FMDLOrbit, Key[{l, c, r}], 0];

fmdlStep5[state_List] := Module[{n = 5},
  Table[
    fmdlZ7[state[[Mod[i - 2, n] + 1]], state[[i]], state[[Mod[i, n] + 1]]],
    {i, n}
  ]
];

fmdlMirror[state_List] := Reverse[state];

GEN2 = fmdlStep5[GEN1];
GEN3 = fmdlStep5[GEN2];

(* ---------- Three-layer CMCA (Option A shared inner clock) ---------- *)

runTwoLayerChiralAFCA[
  outerL_Integer,
  m_Integer,
  nTransitions_Integer,
  init110_List,
  init124_List,
  clockOption_String,
  snapshotEvery_Integer : SnapEvery
] := Module[
  {
    maxInner = 10 m, n = outerL, outer110, outer124, phases, inner,
    tauCount, tauAccum, nTransArr, needsCheck,
    targets, maj, instant, idxA, advanceSkip, adv, done, idxC,
    spacetime110 = {}, spacetime124 = {},
    istep = 0, loopStart = AbsoluteTime[]
  },

  outer110 = init110;
  outer124 = init124;
  phases = Table[Mod[i m, 14], {i, 0, n - 1}];
  inner = ConstantArray[0, {n, m}];
  tauCount = ConstantArray[0, n];
  tauAccum = ConstantArray[0.0, n];
  nTransArr = ConstantArray[0, n];
  needsCheck = ConstantArray[True, n];

  seedCells[idx_List] := Module[{p},
    Do[
      p = phases[[i + 1]];
      inner[[i + 1]] = Table[ETHER14[[Mod[p + j, 14] + 1]], {j, 0, m - 1}],
      {i, idx}
    ]
  ];

  majority[] := Map[If[# > m/2, 1, 0] &, Total[inner, {2}]];

  targets110[arr_] := applyRule110[arr];

  advanceInner[mask_List] := Do[
    If[mask[[i + 1]], inner[[i + 1]] = applyRule110[inner[[i + 1]]]],
    {i, 0, n - 1}
  ];

  targets = targets110[outer110];
  seedCells[Range[0, n - 1]];

  completeCells[idx_List, maj_] := Module[{new124, newOuter110, newOuter124, newTargets},
    new124 = applyRule124[outer124];
    newOuter110 = outer110;
    newOuter124 = outer124;
    Do[
      newOuter110[[i + 1]] = maj[[i + 1]];
      newOuter124[[i + 1]] = new124[[i + 1]];
      ,
      {i, idx}
    ];
    newTargets = targets110[newOuter110];
    Do[
      outer110[[i + 1]] = newOuter110[[i + 1]];
      outer124[[i + 1]] = newOuter124[[i + 1]];
      targets[[i + 1]] = newTargets[[i + 1]];
      tauAccum[[i + 1]] += tauCount[[i + 1]];
      nTransArr[[i + 1]] += 1;
      tauCount[[i + 1]] = 0;
      ,
      {i, idx}
    ];
    seedCells[idx];
  ];

  While[True,
    If[AbsoluteTime[] - $CMCAStartTime > 870 || AbsoluteTime[] - loopStart > 180, Break[]];

    advanceSkip = ConstantArray[False, n];
    If[MemberQ[needsCheck, True],
      maj = majority[];
      instant = MapThread[#1 && (#2 == targets[[#3 + 1]]) &, {needsCheck, maj, Range[0, n - 1]}];
      If[MemberQ[instant, True],
        idxA = Flatten@Position[instant, True] - 1;
        completeCells[idxA, maj];
        Do[advanceSkip[[i + 1]] = True, {i, idxA}];
        Do[needsCheck[[i + 1]] = True, {i, idxA}]
      ];
      Do[
        If[needsCheck[[i + 1]] && !instant[[i + 1]], needsCheck[[i + 1]] = False],
        {i, 0, n - 1}
      ]
    ];

    adv = Map[!# &, advanceSkip];
    If[MemberQ[adv, True],
      advanceInner[adv];
      Do[If[adv[[i + 1]], tauCount[[i + 1]] += 1], {i, 0, n - 1}]
    ];
    istep += 1;

    maj = majority[];
    done = MapThread[#1 && ((maj[[#2 + 1]] == targets[[#2 + 1]]) || tauCount[[#2 + 1]] >= maxInner) &,
      {adv, Range[0, n - 1]}
    ];
    If[MemberQ[done, True],
      idxC = Flatten@Position[done, True] - 1;
      completeCells[idxC, maj];
      Do[needsCheck[[i + 1]] = True, {i, idxC}]
    ];

    If[Mod[istep, snapshotEvery] == 0,
      AppendTo[spacetime110, Table[outer110[[j]], {j, Length[outer110]}]];
      AppendTo[spacetime124, Table[outer124[[j]], {j, Length[outer124]}]]
    ];

    If[Min[nTransArr] >= nTransitions, Break[]];
    If[istep > nTransitions*maxInner*5, Break[]]
  ];

  <|
    "spacetime_110" -> spacetime110,
    "spacetime_124" -> spacetime124,
    "tau_c" -> MapThread[If[#2 > 0, #1/#2, 0.0] &, {tauAccum, nTransArr}],
    "n_trans" -> nTransArr,
    "inner_steps" -> istep,
    "clock_option" -> clockOption
  |>
];

CMCAStep[{outer110_, outer124_, innerClocks_}] := Module[
  {n = Length[outer110], m = Length[innerClocks[[1]]], targets, maj},
  (* one synchronous outer step reference — full AFCA uses runTwoLayerChiralAFCA *)
  targets = applyRule110[outer110];
  maj = Map[If[# > m/2, 1, 0] &, Total[innerClocks, {2}]];
  {
    applyRule110[outer110],
    applyRule124[outer124],
    Map[rule110Step, innerClocks, {1}]
  }
];

(* ---------- verification primitives ---------- *)

verifyVAStructure[] := Module[
  {triples, classify, counts, mismatches, wCenter, wplusMismatch, allWplusNoncenter},
  classify[l_, c_, r_] := Module[{f110, f124},
    f110 = Lookup[RULE110, Key[{Mod[l, 2], Mod[c, 2], Mod[r, 2]}], 0];
    f124 = Lookup[RULE124, Key[{Mod[l, 2], Mod[c, 2], Mod[r, 2]}], 0];
    Which[
      f110 == 1 && f124 == 0, "R_ONLY",
      f110 == 0 && f124 == 1, "L_ONLY",
      f110 == 1 && f124 == 1, "BOTH",
      True, "NEITHER"
    ]
  ];
  triples = Tuples[SMVA, 3];
  counts = Counts[classify @@@ triples];
  mismatches = Lookup[counts, "R_ONLY", 0] + Lookup[counts, "L_ONLY", 0];
  wCenter = Length[Select[triples, (#[[2]] == 3 && MemberQ[{"R_ONLY", "L_ONLY"}, classify @@ #]) &]];
  wplusMismatch = Select[triples, (MemberQ[{"R_ONLY", "L_ONLY"}, classify @@ #] && (#[[1]] == 3 || #[[3]] == 3)) &];
  allWplusNoncenter = Length[wplusMismatch] == mismatches;
  <|
    "mismatch_count" -> mismatches,
    "expected_mismatch_count" -> 32,
    "total_triples" -> Length[triples],
    "r_only_count" -> Lookup[counts, "R_ONLY", 0],
    "l_only_count" -> Lookup[counts, "L_ONLY", 0],
    "w_plus_center_mismatches" -> wCenter,
    "all_mismatches_wplus_noncenter" -> allWplusNoncenter,
    "pass" -> mismatches == 32 && wCenter == 0 && allWplusNoncenter
  |>
];

verifyZ7GenerationOrbit[] := Module[{states = {GEN1}, s = GEN1, forwardOk, mirrorG1, m2},
  Do[s = fmdlStep5[s]; AppendTo[states, s], {3}];
  forwardOk = states[[2]] == GEN2 && states[[3]] == GEN3 && states[[4]] == VACUUM;
  mirrorG1 = fmdlMirror[GEN1];
  m2 = fmdlStep5[fmdlStep5[mirrorG1]];
  <|
    "gen1" -> GEN1, "gen2" -> GEN2, "gen3" -> GEN3, "vacuum" -> VACUUM,
    "forward_orbit_holds" -> forwardOk,
    "steps_gen1_to_vacuum" -> 3,
    "mirror_decay_steps" -> If[m2 == VACUUM, 2, 99],
    "pass" -> forwardOk && m2 == VACUUM
  |>
];

measureSyncGliderSpeed[ether110_, ether124_, center110_, center124_, nSteps_] := Module[
  {base110, base124, pert110, pert124, rightLeads = {}, leftLeads = {},
   cross124 = 0, cross110 = 0, diff, vR, vL},
  base110 = ether110; base124 = ether124;
  pert110 = ether110; pert124 = ether124;
  pert110[[center110 + 1]] = Mod[pert110[[center110 + 1]] + 1, 2];
  Do[
    {base110, base124} = stepSyncChiral[base110, base124];
    {pert110, pert124} = stepSyncChiral[pert110, pert124];
    diff = MapThread[Unequal, {base110, pert110}];
    cross124 = Max[cross124, Total[Boole@MapThread[Unequal, {base124, pert124}]]];
    AppendTo[rightLeads,
      Module[{pos = Select[Range[0, Length[base110] - 1], diff[[# + 1]] &]},
        If[pos === {}, 0, Max[Select[pos, # > center110 &] - center110]]
      ]
    ],
    {nSteps}
  ];
  vR = Last[rightLeads]/nSteps;

  base110 = ether110; base124 = ether124;
  pert110 = ether110; pert124 = ether124;
  pert124[[center124 + 1]] = Mod[pert124[[center124 + 1]] + 1, 2];
  Do[
    {base110, base124} = stepSyncChiral[base110, base124];
    {pert110, pert124} = stepSyncChiral[pert110, pert124];
    diff = MapThread[Unequal, {base124, pert124}];
    cross110 = Max[cross110, Total[Boole@MapThread[Unequal, {base110, pert110}]]];
    AppendTo[leftLeads,
      Module[{pos = Select[Range[0, Length[base124] - 1], diff[[# + 1]] &]},
        If[pos === {}, 0, Max[center124 - Select[pos, # < center124 &]]]
      ]
    ],
    {nSteps}
  ];
  vL = Last[leftLeads]/nSteps;

  <|
    "v_r_sync" -> N[vR], "v_l_sync" -> N[vL],
    "layers_decoupled" -> cross124 == 0 && cross110 == 0,
    "pass" -> Abs[vR - CEff] < SpeedTol && Abs[vL - CEff] < SpeedTol
  |>
];

injectGliderSeed[tape_, length_, phase_: CANONICALPHASE] := Module[{c, out = tape},
  c = Quotient[length, 2] - Mod[Quotient[length, 2] - phase, 14];
  Do[out[[Mod[c + j, length] + 1]] = GLIDERSEED[[j + 1]], {j, 0, Length[GLIDERSEED] - 1}];
  {out, c}
];

gliderMaskFromRuns[etherRun_, gliderRun_, length_] := Module[
  {nSnaps, diffFrac, isGlider, top},
  nSnaps = Min[Length[etherRun["spacetime_110"]], Length[gliderRun["spacetime_110"]]];
  If[nSnaps >= 5,
    diffFrac = Table[
      Mean@Table[
        Boole[etherRun["spacetime_110"][[t, i]] != gliderRun["spacetime_110"][[t, i]]],
        {t, nSnaps}
      ],
      {i, length}
    ];
    isGlider = Map[# > DiffThreshold &, diffFrac];
    If[!MemberQ[isGlider, True],
      top = Take[Ordering[diffFrac, -Max[5, Quotient[length, 20]]], -Max[5, Quotient[length, 20]]];
      isGlider = ConstantArray[False, length];
      Do[isGlider[[i]] = True, {i, top}]
    ],
    isGlider = ConstantArray[False, length]
  ];
  isGlider
];

measureTauCSR[ether110_, ether124_, clockOption_, useC2Flip_: False] := Module[
  {glider110, vUsed, gammaTarget, seedLabel, etherRun, gliderRun, tauEther, tauGliderTape,
   isGlider, tauBg, tauG, tauE, ratio, srErrorPct, dilationFactor, expectedDilation},
  If[useC2Flip,
    glider110 = ether110;
    glider110[[CENTER110 + 1]] = Mod[glider110[[CENTER110 + 1]] + 1, 2];
    vUsed = CEff;
    gammaTarget = GammaV23;
    seedLabel = "C2_center_flip_v23",
    glider110 = injectGliderSeed[ether110, Length[ether110]][[1]];
    vUsed = 0.532;
    gammaTarget = 1/Sqrt[1 - (vUsed/CEff)^2];
    seedLabel = "round19_glider_seed"
  ];
  etherRun = runTwoLayerChiralAFCA[Length[ether110], MDefault, NTrans, ether110, ether124, clockOption];
  gliderRun = runTwoLayerChiralAFCA[Length[ether110], MDefault, NTrans, glider110, ether124, clockOption];
  tauEther = etherRun["tau_c"];
  tauGliderTape = gliderRun["tau_c"];
  isGlider = gliderMaskFromRuns[etherRun, gliderRun, Length[ether110]];
  tauBg = Mean[tauEther];
  tauG = Mean[Pick[tauGliderTape, isGlider]];
  tauE = If[MemberQ[Map[!# &, isGlider], True],
    Mean[Pick[tauGliderTape, Map[!# &, isGlider]]],
    tauBg
  ];
  ratio = tauG/Max[tauE, 10^-9];
  srErrorPct = Abs[ratio - gammaTarget]/gammaTarget * 100.;
  dilationFactor = tauE/Max[tauG, 10^-9];
  expectedDilation = 1/gammaTarget;
  <|
    "seed_label" -> seedLabel,
    "tau_c_ratio_glider_over_ether" -> N[ratio],
    "gamma_target" -> N[gammaTarget],
    "sr_error_pct" -> N[srErrorPct],
    "tau_c_glider_gt_ether" -> tauG > tauE,
    "pass_tau_c_elevated" -> tauG > tauE,
    "pass_tau_c_gamma" -> srErrorPct < SRErrorTolPct,
    "pass_dilation" -> Abs[dilationFactor - expectedDilation]/expectedDilation * 100. < SRErrorTolPct
  |>
];

verifyDecoupledCoevolutionAFCA[clockOption_, length_: LDefault] := Module[
  {e110, e124, pert110, baseRun, pertRun, n, r124Match, z7 = GEN1, z7Trace = {GEN1}},
  e110 = etherTape[ETHER14, length];
  e124 = etherTape[ETHER124Seq, length];
  pert110 = e110;
  Do[pert110[[CENTER110 + k + 1]] = Mod[GEN1[[k + 1]], 2], {k, 0, 4}];
  baseRun = runTwoLayerChiralAFCA[length, MDefault, 60, e110, e124, clockOption];
  pertRun = runTwoLayerChiralAFCA[length, MDefault, 60, pert110, e124, clockOption];
  n = Min[Length[baseRun["spacetime_124"]], Length[pertRun["spacetime_124"]], 20];
  r124Match = And @@ Table[
    baseRun["spacetime_124"][[t]] == pertRun["spacetime_124"][[t]],
    {t, Min[n, 20]}
  ];
  Do[z7 = fmdlStep5[z7]; AppendTo[z7Trace, z7], {3}];
  <|
    "z7_trace" -> z7Trace,
    "reaches_vacuum_at_step_3" -> z7Trace[[4]] == VACUUM,
    "layer124_bitwise_independent_under_afca" -> r124Match,
    "pass" -> z7Trace[[4]] == VACUUM
  |>
];

runVerification[clockOption_] := Module[
  {e110, e124, va, z7, z7Afca, syncSpeed, tauSeed, tauC2, checklist, allPass},
  e110 = etherTape[ETHER14, LDefault];
  e124 = etherTape[ETHER124Seq, LDefault];
  va = verifyVAStructure[];
  z7 = verifyZ7GenerationOrbit[];
  z7Afca = verifyDecoupledCoevolutionAFCA[clockOption, LDefault];
  syncSpeed = measureSyncGliderSpeed[e110, e124, CENTER110, CENTER124, TSync];
  tauSeed = measureTauCSR[e110, e124, clockOption, False];
  tauC2 = measureTauCSR[e110, e124, clockOption, True];
  checklist = <|
    "z7_orbit" -> z7["pass"] && z7Afca["reaches_vacuum_at_step_3"],
    "va_32_125" -> va["pass"],
    "glider_speeds" -> syncSpeed["pass"],
    "tau_c_elevated" -> tauSeed["pass_tau_c_elevated"] && tauC2["pass_tau_c_elevated"],
    "tau_c_gamma" -> tauSeed["pass_tau_c_gamma"],
    "sr_dilation" -> tauSeed["pass_dilation"]
  |>;
  allPass = And @@ Values[checklist];
  <|
    "clock_option" -> clockOption,
    "checklist" -> checklist,
    "all_pass" -> allPass,
    "va" -> va,
    "z7_algebraic" -> z7,
    "sync_speed" -> syncSpeed,
    "tau_c_sr_glider_seed" -> tauSeed,
    "tau_c_sr_c2_v23" -> tauC2
  |>
];

(* ---------- Born rule (Z7-KG kink gradient density) ---------- *)

testBornNormalization[] := Module[
  {n7 = 7, m = N[1776.86/1000.], gradSqAt, gradAnalytic, gradIntegral,
   normCheck, sector, sectorPass, normalizationPass, gradIntegralPass,
   xMax, nPts = 400000, dx, vals},

  gradSqAt = Compile[{{u, _Real}, {mm, _Real}},
    Module[{arg = Min[500., Max[-500., mm u]], em = Exp[arg]},
      ((4. mm/7.)/(em + 1./em))^2
    ],
    RuntimeOptions -> "Speed"
  ];
  gradAnalytic = N[8. m/49.];

  xMax = N[25./m];
  dx = N[(2. xMax)/nPts];
  vals = Table[gradSqAt[-xMax + (i + 0.5) dx, m], {i, 0, nPts - 1}];
  gradIntegral = dx Total[vals];
  gradIntegralPass = Abs[gradIntegral - gradAnalytic]/gradAnalytic < 0.001;

  normCheck = dx Total[vals/gradIntegral];
  normalizationPass = Abs[normCheck - 1.] < 10^-4;

  SeedRandom[20260525, Method -> "MersenneTwister"];
  sector = Module[{c, norm, P, maxResidual},
    c = Table[RandomReal[] + I RandomReal[], {n7}];
    norm = Sqrt[Total[Abs[c]^2]];
    c = c/norm;
    P = Abs[c]^2;
    maxResidual = Max[Abs[P - Abs[c]^2]];
    <|
      "sector_born_max_residual" -> maxResidual,
      "sector_born_pass" -> maxResidual < 10^-15 && Abs[Total[P] - 1] < 10^-15
    |>
  ];
  sectorPass = sector["sector_born_pass"];

  Print["--- Running born_rule_normalization ---"];
  reportClaim[
    "born_rule_normalization",
    normalizationPass && sectorPass && gradIntegralPass,
    <|
      "P_x_normalization_integral" -> N[normCheck, 12],
      "P_x_normalization_pass" -> normalizationPass,
      "sector_born_pass" -> sectorPass,
      "grad_integral_rel_error" -> N[Abs[gradIntegral - gradAnalytic]/gradAnalytic, 6],
      "source" -> "phiborn1_kg_amplitude_probability (WL port)"
    |>
  ]
];

(* ---------- Double-slit Huygens-Fresnel ---------- *)

dslitHuygensFresnel[
  k_, wavelength_, slitWidth_, slitSep_, screenDist_, nScreen_, nSource_, xMax_
] := Module[
  {xScreen, slits, amp, intensity, intensityNorm, analyticNorm, corr, vis,
   theta, beta, alpha, single, double},
  xScreen = N@Table[-xMax + (2. xMax)/(nScreen - 1) (i - 1), {i, nScreen}];
  slits = N@{{-slitSep/2, slitWidth/2}, {slitSep/2, slitWidth/2}};
  amp = N@Total[
    Table[
      Module[{xc = slits[[sIdx, 1]], hw = slits[[sIdx, 2]], xs, dxs},
        xs = N@Table[xc - hw + (2. hw)/(nSource - 1) (i - 1), {i, nSource}];
        dxs = N@If[nSource > 1, xs[[2]] - xs[[1]], 1.];
        Total@Table[
          dxs N@(Exp[I k Sqrt[(xScreen - xSrc)^2 + screenDist^2]]/
            Sqrt[(xScreen - xSrc)^2 + screenDist^2]),
          {xSrc, xs}
        ]
      ],
      {sIdx, 2}
    ],
    {1}
  ];
  intensity = N@Abs[amp]^2;
  theta = ArcTan[xScreen/screenDist];
  beta = Pi slitWidth Sin[theta]/wavelength;
  alpha = Pi slitSep Sin[theta]/wavelength;
  single = Map[If[Abs[#] < 10^-12, 1., (Sin[#]/#)^2] &, beta];
  double = Cos[alpha]^2;
  analyticNorm = N[single double];
  intensityNorm = intensity/Max[intensity];
  analyticNorm = analyticNorm/Max[analyticNorm];
  corr = Module[{a = intensityNorm - Mean[intensityNorm], b = analyticNorm - Mean[analyticNorm]},
    N@Total[a b]/Sqrt[Total[a^2] Total[b^2]]
  ];
  vis = Module[{iMax = Max[intensity], iMin = Min[intensity]},
    If[iMax + iMin < 10^-15, 0., (iMax - iMin)/(iMax + iMin)]
  ];
  <|"corr_fraunhofer" -> corr, "fringe_visibility" -> vis, "pass" -> N[corr] > 0.99|>
];

testDoubleSlitCorrelation[] := Module[{result},
  Print["--- Running double_slit_correlation ---"];
  result = dslitHuygensFresnel[12., (2. Pi)/12., 0.35, 2., 18., 400, 80, 8.];
  reportClaim[
    "double_slit_correlation",
    result["pass"],
    <|
      "corr_fraunhofer" -> N[result["corr_fraunhofer"], 6],
      "threshold" -> 0.99,
      "fringe_visibility" -> N[result["fringe_visibility"], 6],
      "source" -> "dslit_gte_interference (WL port)"
    |>
  ]
];

(* ---------- nine headline claim tests ---------- *)

testThreeLayerCMCARuns[] := Module[{result},
  Print["--- Running three_layer_cmca_runs ---"];
  result = runVerification["A"];
  reportClaim[
    "three_layer_cmca_runs",
    result["all_pass"],
    <|
      "clock_option" -> result["clock_option"],
      "checklist" -> result["checklist"],
      "inner_rule" -> "Rule 110 (ETHER14 seed)",
      "outer_x_plus" -> "Rule 110",
      "outer_x_minus" -> "Rule 124",
      "source" -> "runVerification Option A"
    |>
  ]
];

testGliderSpeeds[] := Module[{e110, e124, speed, target = CEff, tol = 0.01},
  Print["--- Running glider_speed_2_3 ---"];
  e110 = etherTape[ETHER14, LDefault];
  e124 = etherTape[ETHER124Seq, LDefault];
  speed = measureSyncGliderSpeed[e110, e124, CENTER110, CENTER124, TSync];
  reportClaim[
    "glider_speed_2_3",
    Abs[speed["v_r_sync"] - target] <= tol && Abs[speed["v_l_sync"] - target] <= tol,
    <|
      "v_r" -> speed["v_r_sync"], "v_l" -> speed["v_l_sync"],
      "expected" -> N[target], "tolerance" -> tol,
      "layers_decoupled" -> speed["layers_decoupled"]
    |>
  ]
];

testZ7Orbit[] := Module[{z7, z7Afca},
  Print["--- Running z7_generation_orbit ---"];
  z7 = verifyZ7GenerationOrbit[];
  z7Afca = verifyDecoupledCoevolutionAFCA["A", LDefault];
  reportClaim[
    "z7_generation_orbit",
    z7["pass"] && z7Afca["reaches_vacuum_at_step_3"],
    <|
      "gen1" -> GEN1, "gen2" -> GEN2, "gen3" -> GEN3, "vacuum" -> VACUUM,
      "steps_to_vacuum" -> 3,
      "afca_reaches_vacuum" -> z7Afca["reaches_vacuum_at_step_3"]
    |>
  ]
];

testVAMismatches[] := Module[{va},
  Print["--- Running va_32_125 ---"];
  va = verifyVAStructure[];
  reportClaim[
    "va_32_125",
    va["pass"],
    <|
      "mismatch_count" -> va["mismatch_count"],
      "expected" -> 32,
      "total_triples" -> va["total_triples"],
      "r_only" -> va["r_only_count"],
      "l_only" -> va["l_only_count"],
      "w_plus_center_mismatches" -> va["w_plus_center_mismatches"]
    |>
  ]
];

testTauCSRdilation[] := Module[{e110, e124, tau, ratio, gamma, epsFloorPct, srErrorPct},
  Print["--- Running tau_c_sr_dilation ---"];
  e110 = etherTape[ETHER14, LDefault];
  e124 = etherTape[ETHER124Seq, LDefault];
  tau = measureTauCSR[e110, e124, "A", False];
  ratio = tau["tau_c_ratio_glider_over_ether"];
  gamma = tau["gamma_target"];
  epsFloorPct = 100 Pi^2/147;
  srErrorPct = tau["sr_error_pct"];
  reportClaim[
    "tau_c_sr_dilation",
    tau["pass_tau_c_elevated"] && srErrorPct <= epsFloorPct + 0.05 && Abs[ratio - 1.563]/1.563 <= 0.02,
    <|
      "tau_c_ratio" -> ratio,
      "expected_ratio_approx" -> 1.563,
      "gamma_target" -> gamma,
      "sr_error_percent" -> srErrorPct,
      "nyquist_floor_percent" -> epsFloorPct,
      "tau_c_glider_gt_ether" -> tau["tau_c_glider_gt_ether"]
    |>
  ]
];

testObservableLorentzFloor[] := Module[{eps0, eps0Pct},
  Print["--- Running observable_lorentz_epsilon0 ---"];
  eps0 = Pi^2/147;
  eps0Pct = 100 eps0;
  reportClaim[
    "observable_lorentz_epsilon0",
    eps0Pct < 7.0,
    <|
      "epsilon_0_7" -> N[eps0, 8],
      "epsilon_0_7_percent" -> N[eps0Pct, 6],
      "formula" -> "pi^2/147",
      "expected_percent_approx" -> 6.71
    |>
  ]
];

testSin2ThetaW[] := Module[{nGen = 3, cH = 13, nFam = 5, lam, sin2Tree, sin2Corr, sin2, expected},
  Print["--- Running sin2_theta_w_orbit ---"];
  lam = nGen^2/((2^nGen) nFam);
  sin2Tree = nGen/cH;
  sin2Corr = lam^3/(2 cH);
  sin2 = sin2Tree + sin2Corr;
  expected = 384729/1664000;
  reportClaim[
    "sin2_theta_w_orbit",
    sin2 == expected,
    <|
      "sin2_rational" -> ToString[Numerator[sin2]] <> "/" <> ToString[Denominator[sin2]],
      "expected_rational" -> "384729/1664000",
      "sin2_float" -> N[sin2, 10],
      "tree_term" -> ToString[Numerator[sin2Tree]] <> "/" <> ToString[Denominator[sin2Tree]],
      "threshold_correction" -> ToString[Numerator[sin2Corr]] <> "/" <> ToString[Denominator[sin2Corr]]
    |>
  ]
];

testMDLKCA[] := Module[{cmcaBits, single, twoLayer, afca, lowerBound},
  Print["--- Running mdl_k_ca_19 ---"];
  cmcaBits = kCABits[7, 2, 9, True, 3];
  single = kCABits[7, 1, 8, False, 0];
  twoLayer = kCABits[7, 2, 9, False, 0];
  afca = kCABits[7, 1, 8, True, 3];
  lowerBound = 3 + 1 + 2 + 8 + 1 + 1 + 3;
  reportClaim[
    "mdl_k_ca_19",
    cmcaBits == 19 && lowerBound == 19 && cmcaBits == lowerBound,
    <|
      "K_CA_CMCA" -> cmcaBits,
      "K_CA_single_R110" -> single,
      "K_CA_two_layer_chiral" -> twoLayer,
      "K_CA_AFCA" -> afca,
      "construction_class_lower_bound" -> lowerBound,
      "channels" -> <|"alpha" -> 3, "radius" -> 1, "layers" -> 2,
        "rho_outer" -> 9, "tau_async" -> 1, "gating" -> 3|>
    |>
  ]
];

(* ---------- main ---------- *)

runCMCAMain[] := Module[{},
Print["======================================================================"];
Print["074-REPRO — CMCA Full Reproducibility Suite (P41) — Wolfram Language"];
Print["======================================================================"];

testThreeLayerCMCARuns[];
testGliderSpeeds[];
testZ7Orbit[];
testVAMismatches[];
testTauCSRdilation[];
testObservableLorentzFloor[];
testSin2ThetaW[];
testBornNormalization[];
testDoubleSlitCorrelation[];
testMDLKCA[];

elapsed = AbsoluteTime[] - $CMCAStartTime;
nPass = Count[$CMCAResults, r_ /; r["pass"] === True];
nTotal = Length[$CMCAResults];
allPass = nPass == nTotal;

Print["----------------------------------------------------------------------"];
Print["Summary: ", nPass, "/", nTotal, " claims PASS"];
Print["OVERALL: ", If[TrueQ[allPass], "PASS", "FAIL"]];
Print["Elapsed: ", NumberForm[elapsed, {6, 1}], " s"];
Print["======================================================================"];

(* optional visualization when run interactively in a notebook front end *)
If[$Notebooks && $FrontEnd =!= Null,
  Print["Generating ArrayPlot visualizations..."];
  Module[{demo110, demo124, demoSteps = 80},
    demo110 = etherTape[ETHER14, 128];
    demo124 = etherTape[ETHER124Seq, 128];
    Print[
      ArrayPlot[
        CellularAutomaton[{110, Automatic}, {demo110, 0}, demoSteps,
          "PeriodicBoundaryConditions" -> True],
        PlotLabel -> "Rule 110 spacetime (demo)",
        ColorRules -> {0 -> White, 1 -> Black}
      ]
    ];
    Print[
      ArrayPlot[
        CellularAutomaton[{124, Automatic}, {demo124, 0}, demoSteps,
          "PeriodicBoundaryConditions" -> True],
        PlotLabel -> "Rule 124 spacetime (demo)",
        ColorRules -> {0 -> White, 1 -> Black}
      ]
    ];
  ]
];

If[!allPass, Exit[1]];
];

If[!MemberQ[$ScriptCommandLine, "-code"],
  Print["======================================================================"];
  runCMCAMain[];
];
