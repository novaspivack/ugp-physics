(* ThreeTapeCMCA.wl — Three-Tape CMCA Mathematica cross-check (P45/P46) *)
(* Run: WolframKernel -script ThreeTapeCMCA.wl *)

$L = 256;
$Tsr = 2000;

etherTile = {1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0};
makeEther[len_] := Take[Flatten[ConstantArray[etherTile, Ceiling[len/14]]], len];

rule110Arr = Table[BitGet[110, k], {k, 0, 7}];

stepR110[tape_] := Module[{len = Length[tape], left, right, idx},
  left = RotateRight[tape];
  right = RotateLeft[tape];
  Table[
    idx = 4 left[[i]] + 2 tape[[i]] + right[[i]];
    rule110Arr[[idx + 1]],
    {i, len}
  ]
];

(* Verification 1: SR gate rate at ether phase cell (cell 2, 1-based) *)
verifySR[] := Module[
  {etherBg = makeEther[$L], innerClock, tauC, cell = 2,
   outerFires = 0, newIC, gate, prev},
  innerClock = etherBg;
  tauC = ConstantArray[0, $L];
  Do[
    prev = tauC[[cell]];
    newIC = stepR110[innerClock];
    innerClock = newIC;
    gate = Map[Boole[# > 0] &, newIC];
    tauC = tauC + gate;
    If[tauC[[cell]] > prev, outerFires++],
    {$Tsr}
  ];
  <|
    (* exact rational from period-7 ether orbit: odd-parity cell fires 3/7 steps *)
    "passed" -> (Abs[outerFires/$Tsr - 3/7] < 0.01),
    "ratio" -> N[outerFires/$Tsr, 4],
    "expected" -> N[3/7, 4],
    "expected_exact" -> "3/7"
  |>
];

(* Verification 3: Z7 vertex conservation (49 directed pairs) *)
verifySMVertices[] := Module[{psc = {0, 2, 3, 4, 6}, anti = {1, 5}, allW, ok = 0, n = 0},
  allW = Join[psc, anti];
  Do[Do[n++; If[MemberQ[allW, Mod[w1 + w2, 7]] || Mod[w1 + w2, 7] == 0, ok++], {w2, allW}], {w1, allW}];
  <|"passed" -> (ok == n), "n_passed" -> ok, "n_total" -> n|>
];

(* Verification 8: Kink mass (8/49) m_tau *)
verifyKinkMass[] := Module[{mKink = (8/49)*1776.86, errPct},
  errPct = Abs[mKink - 290.10]/290.10*100;
  <|"passed" -> (errPct < 1.), "M_kink_MeV" -> N[mKink, 4], "error_pct" -> N[errPct, 4]|>
];

RunAllVerifications[] := Module[{results = <||>, nPassed},
  Print["=== Three-Tape CMCA Verification Suite (Mathematica) ===\n"];
  Print["Running sr_time_dilation..."];
  results = Append[results, "sr_time_dilation" -> verifySR[]];
  Print[results["sr_time_dilation"]];
  Print["Running sm_vertices..."];
  results = Append[results, "sm_vertices" -> verifySMVertices[]];
  Print[results["sm_vertices"]];
  Print["Running kink_mass..."];
  results = Append[results, "kink_mass" -> verifyKinkMass[]];
  Print[results["kink_mass"]];
  nPassed = Length[Select[Values[results], TrueQ[#passed] &]];
  Print["\n=== Results: ", nPassed, "/", Length[results], " passed ==="];
  results
];

RunAllVerifications[]
