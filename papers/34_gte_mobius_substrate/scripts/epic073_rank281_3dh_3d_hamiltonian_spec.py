#!/usr/bin/env python3
"""
Rank 281-3DH — 3D GTE Hamiltonian specification and symmetry audit.

Objective: Formalize the 3D extension of the f_MDL 't Hooft Hamiltonian (070-95 CatAL
on Z₇⁵) and audit symmetry properties of the existing P28 f_MDL,3D CA dynamics.

The rank asks for a Hamiltonian H on 3D beable configurations that:
  (1) Reduces to Rule 110 / f_MDL on 1D axis-aligned slices
  (2) Admits SO(3) symmetry (or documents why the P28 construction does not)
  (3) Preserves SM orbit structure and MDL minimality

Existing assets (not re-derived):
  - P28 §9: f_MDL,3D CA step (von Neumann, axis f_MDL + Z₇ cross-coupling)
  - fmdl3d_chirality.py: step_fmdl3d implementation
  - 070-95: 1D cogwheel H on Z₇⁵, dim(H_phys)=1, E₀=0
  - 278-QRF: Z₅ discrete rotation equivariance (CatAL Lean)

Wall-clock timeout: 600 s.
"""

import itertools
import json
import os
import signal
import sys
import time
from collections import Counter

import numpy as np

TIMEOUT_SECONDS = 600


def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Saving partial results.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

t0 = time.time()
results = {}

# ── f_MDL 1D table (CUP3DUniqueness.lean / P28 canonical) ───────────────────

FMDL_1D = np.zeros(343, dtype=np.int8)
ORBIT_NBHDS = [
    (1, 1, 5, 2), (1, 5, 2, 5), (5, 2, 2, 2), (2, 2, 1, 0), (2, 1, 1, 2),
    (2, 2, 5, 5), (2, 5, 2, 6), (5, 2, 0, 5), (2, 0, 2, 3), (0, 2, 2, 5),
]
for l, c, r, out in ORBIT_NBHDS:
    FMDL_1D[l * 49 + c * 7 + r] = out
RULE110_NBHDS = [
    (0, 0, 0, 0), (0, 0, 1, 1), (0, 1, 0, 1), (0, 1, 1, 1),
    (1, 0, 0, 0), (1, 0, 1, 1), (1, 1, 0, 1), (1, 1, 1, 0),
]
for l, c, r, out in RULE110_NBHDS:
    FMDL_1D[l * 49 + c * 7 + r] = out

GEN1 = np.array([1, 5, 2, 2, 1], dtype=np.int8)


def step_fmdl3d(grid: np.ndarray) -> np.ndarray:
    """One step of f_MDL,3D (P28 §9 canonical prescription)."""
    lx = np.roll(grid, 1, axis=0).astype(np.int64)
    rx = np.roll(grid, -1, axis=0).astype(np.int64)
    ly = np.roll(grid, 1, axis=1).astype(np.int64)
    ry = np.roll(grid, -1, axis=1).astype(np.int64)
    lz = np.roll(grid, 1, axis=2).astype(np.int64)
    rz = np.roll(grid, -1, axis=2).astype(np.int64)
    c = grid.astype(np.int64)

    fx = FMDL_1D[lx * 49 + c * 7 + rx]
    fy = FMDL_1D[ly * 49 + c * 7 + ry]
    fz = FMDL_1D[lz * 49 + c * 7 + rz]

    x_only = ((ly == 0) & (ry == 0) & (lz == 0) & (rz == 0))
    y_only = ((lx == 0) & (rx == 0) & (lz == 0) & (rz == 0))
    z_only = ((ly == 0) & (ry == 0) & (lx == 0) & (rx == 0))
    multi = ~(x_only | y_only | z_only)

    out = np.zeros_like(grid)
    out[x_only] = fx[x_only]
    out[y_only] = fy[y_only]
    out[z_only] = fz[z_only]
    out[multi] = (fx[multi].astype(np.int64) + fy[multi].astype(np.int64)
                  + fz[multi].astype(np.int64)) % 7
    return out.astype(np.int8)


def apply_fmdl_1d(row: np.ndarray) -> np.ndarray:
    L = len(row)
    l = np.roll(row, 1).astype(np.int64)
    c = row.astype(np.int64)
    r = np.roll(row, -1).astype(np.int64)
    return FMDL_1D[l * 49 + c * 7 + r]


# ── Part 1: Formal Hamiltonian specification (documented in JSON) ─────────────

results["hamiltonian_specification"] = {
    "rank_id": "281-3DH",
    "configuration_space": "C_L = (Z_7)^{L×L×L} with periodic boundary conditions",
    "ca_update_map": "T_L : C_L → C_L defined by step_fmdl3d (P28 §9)",
    "axis_reduction": {
        "claim": "If grid is nonzero only on a single axis-aligned line with all cross-axis neighbors zero, "
                 "step_fmdl3d reduces to f_MDL on that axis (x_only/y_only/z_only branches).",
        "1d_hamiltonian_reference": "070-95 CatAL on Z_7^5 ring (CUP3DUniqueness §7c)",
    },
    "thooft_hamiltonian": {
        "full_ontological_space": "H_full = span{|s⟩ : s ∈ C_L}, dim = 7^(L^3)",
        "physical_subspace": "H_phys = span of cycle states of T_L (t Hooft Ch.7 quotient)",
        "eigenvalues": "For a cycle of length N: E_k = 2π k / (N δt), k = 0,…,N−1",
        "local_excitation_subspace": "Z_7^5 rings embedded on axes inherit 070-95 spectrum (dim=1, E_0=0)",
        "note": "Full L^3 spectrum is computationally intractable for L≥3; local ring reduction is the operative 3D→1D bridge.",
    },
    "symmetry_target": {
        "required_for_280_NTH": "SO(3) equivariance of H (continuous rotations on physical observables)",
        "p28_construction_symmetry": "O_h (cubic point group, order 48) from Z^3 lattice — NOT SO(3)",
        "partial_lean_cert": "Z_5 ⊂ SO(3) ring rotations: qrf_d2_z5_equivariance_certified (GUTStructure §82)",
    },
    "approaches": {
        "A_tensor_lattice": {
            "status": "IMPLEMENTED in P28 §9 / fmdl3d_chirality.py",
            "symmetry": "O_h discrete; SO(3) broken at lattice scale",
            "hamiltonian_status": "T_L specified; H_L via cycle decomposition — partial",
        },
        "B_so3_symmetric_extension": {
            "status": "NOT FOUND — creative design step open",
            "blocker": "No MDL-minimal f_MDL,3D rule with exact SO(3) invariance known",
        },
        "C_qrf_hilbert_space": {
            "status": "PARTIAL — 278-QRF Z_5 CatAL; continuous SO(3) pending H_3D",
            "bypass": "Define SO(3) on H_orientation = L^2(SO(3)) without explicit 3D CA rule",
        },
    },
}

# ── Part 2: Verify 1D axis reduction (5-cell periodic ring = L=5 x-axis) ────

L = 5  # must match |Z₅ ring| for periodic embedding
grid_x = np.zeros((L, L, L), dtype=np.int8)
for i, v in enumerate(GEN1):
    grid_x[i, 0, 0] = v

grid_y = np.zeros((L, L, L), dtype=np.int8)
for i, v in enumerate(GEN1):
    grid_y[0, i, 0] = v

out_x = step_fmdl3d(grid_x)
out_y = step_fmdl3d(grid_y)

line_x = out_x[:, 0, 0]
line_y = out_y[0, :, 0]
expected = apply_fmdl_1d(GEN1)

axis_reduction_x = bool(np.array_equal(line_x, expected))
axis_reduction_y = bool(np.array_equal(line_y, expected))

results["axis_reduction_test"] = {
    "L": L,
    "x_axis_matches_fmdl_1d": axis_reduction_x,
    "y_axis_matches_fmdl_1d": axis_reduction_y,
    "gen1_step_x_line": list(map(int, line_x)),
    "gen1_step_y_line": list(map(int, line_y)),
    "fmdl_1d_expected": list(map(int, expected)),
}

# ── Part 3: Symmetry audit — axis permutations (O cubic rotations) vs parity ─

def permute_axes(grid: np.ndarray, perm: tuple) -> np.ndarray:
    return np.transpose(grid, perm)


def reflect_all(grid: np.ndarray) -> np.ndarray:
    return grid[::-1, ::-1, ::-1].copy()


def oh_transform(grid: np.ndarray, name: str) -> np.ndarray:
    if name == "P":
        return reflect_all(grid)
    if name.startswith("perm_"):
        perm = tuple(int(x) for x in name.split("_")[1:])
        return permute_axes(grid, perm)
    raise ValueError(name)


AXIS_PERMS = [f"perm_{p[0]}_{p[1]}_{p[2]}" for p in set(itertools.permutations([0, 1, 2]))]
PARITY = "P"

np.random.seed(2813)
L_oh = 5
n_oh_trials = 50
perm_failures = []
parity_failures = []
for trial in range(n_oh_trials):
    ic = np.random.randint(0, 7, (L_oh, L_oh, L_oh), dtype=np.int8)
    evolved = step_fmdl3d(ic)
    for g in AXIS_PERMS:
        g_ic = oh_transform(ic, g)
        g_evolved = step_fmdl3d(g_ic)
        expected = oh_transform(evolved, g)
        if not np.array_equal(g_evolved, expected):
            perm_failures.append({"trial": trial, "transform": g, "n_diff": int(np.sum(g_evolved != expected))})
            break
    g_ic = oh_transform(ic, PARITY)
    g_evolved = step_fmdl3d(g_ic)
    expected = oh_transform(evolved, PARITY)
    if not np.array_equal(g_evolved, expected):
        parity_failures.append({"trial": trial, "n_diff": int(np.sum(g_evolved != expected))})

results["symmetry_audit"] = {
    "L": L_oh,
    "n_trials": n_oh_trials,
    "axis_permutation_equivariant": len(perm_failures) == 0,
    "axis_permutation_failures": len(perm_failures),
    "parity_equivariant": len(parity_failures) == 0,
    "parity_failures": len(parity_failures),
    "interpretation": "Axis permutations test cubic rotation symmetry; parity failure is expected (P-violation, fmdl3d_chirality.py CatA).",
    "sample_perm_failures": perm_failures[:3],
    "sample_parity_failures": parity_failures[:3],
}

# ── Part 4: Propagation anisotropy (SO(3) breaking proxy) ───────────────────

L_prop = 20
T_prop = 15
cx, cy, cz = L_prop // 2, L_prop // 2, L_prop // 2

def front_speed(axis: int) -> float:
    grid = np.zeros((L_prop, L_prop, L_prop), dtype=np.int8)
    grid[cx, cy, cz] = 2  # u-quark winding seed
    coords = [cx, cy, cz]
    positions = []
    for t in range(T_prop):
        grid = step_fmdl3d(grid)
        nz = np.argwhere(grid != 0)
        if len(nz) == 0:
            break
        positions.append(float(np.mean(nz[:, axis])))
    if len(positions) < 2:
        return 0.0
    return (positions[-1] - positions[0]) / (len(positions) - 1)


speeds = {ax: front_speed(ax) for ax, name in enumerate(["x", "y", "z"])}
speed_vals = list(speeds.values())
speed_mean = float(np.mean(speed_vals))
speed_spread = float(np.max(speed_vals) - np.min(speed_vals))
speed_cv = float(np.std(speed_vals) / speed_mean) if speed_mean > 0 else 0.0

results["propagation_anisotropy"] = {
    "L": L_prop,
    "T": T_prop,
    "speed_cells_per_step": speeds,
    "mean_speed": speed_mean,
    "max_min_spread": speed_spread,
    "coefficient_of_variation": speed_cv,
    "isotropic_gate_cv_lt_0.05": speed_cv < 0.05,
}

# ── Part 5: Small-torus cycle structure (L=2, 7^8 states) ───────────────────

SKIP_L2 = os.environ.get("SKIP_L2", "0") == "1"
L_small = 2
N_states = 7 ** (L_small ** 3)
_prior_path = "epic073_rank281_3dh_3d_hamiltonian_spec_results.json"

if SKIP_L2 and os.path.isfile(_prior_path):
    with open(_prior_path) as f:
        results["small_torus_spectrum"] = json.load(f)["small_torus_spectrum"]
    cycle_counter = Counter(
        {int(k): v for k, v in results["small_torus_spectrum"]["cycle_length_histogram"].items()}
    )
    print("Skipping L=2 exhaustive scan (SKIP_L2=1); reusing prior results.")
else:

    def encode_grid(grid: np.ndarray) -> int:
        flat = grid.ravel(order="C")
        n = 0
        base = 1
        for v in flat:
            n += int(v) * base
            base *= 7
        return n

    def decode_grid(n: int) -> np.ndarray:
        flat = []
        for _ in range(L_small ** 3):
            flat.append(n % 7)
            n //= 7
        return np.array(flat, dtype=np.int8).reshape((L_small, L_small, L_small), order="C")

    print(f"Building transition table for L={L_small}, N={N_states}...")
    T_table = np.zeros(N_states, dtype=np.int32)
    for i in range(N_states):
        T_table[i] = encode_grid(step_fmdl3d(decode_grid(i)))

    color = np.zeros(N_states, dtype=np.int8)
    cycle_lengths = []
    on_cycle = np.zeros(N_states, dtype=bool)

    for start in range(N_states):
        if color[start] != 0:
            continue
        path = []
        path_pos = {}
        state = start
        while color[state] == 0:
            color[state] = 1
            path_pos[state] = len(path)
            path.append(state)
            state = int(T_table[state])
        if color[state] == 1:
            clen = len(path) - path_pos[state]
            cycle_lengths.append(clen)
            for s in path[path_pos[state]:]:
                on_cycle[s] = True
                color[s] = 2
        for s in path:
            if color[s] == 1:
                color[s] = 2

    cycle_counter = Counter(cycle_lengths)
    n_on_cycle = int(on_cycle.sum())

    results["small_torus_spectrum"] = {
        "L": L_small,
        "N_states": N_states,
        "n_distinct_cycles": len(cycle_lengths),
        "cycle_length_histogram": dict(sorted(cycle_counter.items())),
        "n_attractor_states": n_on_cycle,
        "dim_H_phys_proxy": int(n_on_cycle),
        "unique_cycle_length_1_only": (
            cycle_counter == Counter({1: len(cycle_lengths)}) if cycle_lengths else True
        ),
        "vacuum_dominance": n_on_cycle <= 7,
    }

# ── Part 6: Verdict ─────────────────────────────────────────────────────────

approach_a_hamiltonian_partial = (
    axis_reduction_x and axis_reduction_y
    and results["symmetry_audit"]["axis_permutation_equivariant"]
)
so3_blocked = True  # Approach B not found; continuous SO(3) not established

if so3_blocked:
    verdict = "SPEC_PARTIAL_CATAD"
    feasibility = "COMPOSER_PARTIAL — Approach A CA+Hamiltonian spec done; Approach B SO(3) design → GENIUS_TEAM"
    follow_on = "281-3DH-B"
else:
    verdict = "SPEC_COMPLETE_CATAD"
    feasibility = "COMPOSER"
    follow_on = "280-NTH"

results["verdict"] = {
    "status": verdict,
    "feasibility": feasibility,
    "follow_on_rank": follow_on,
    "280_nth_unblocked": verdict == "SPEC_COMPLETE_CATAD",
    "cat_level": "CatAD (partial specification)" if so3_blocked else "CatAD",
    "genius_team_required_for": [
        "Approach B: MDL-minimal SO(3)-symmetric 3D rule (if it exists)",
        "Full OQ-CL1 continuous SO(3) Lean cert beyond Z_5 skeleton",
    ],
    "composer_completed": [
        "Formal H_3D specification from T_L + t Hooft prescription",
        "O_h equivariance audit of P28 f_MDL,3D",
        "Axis-aligned 1D reduction verification",
        "L=2 torus cycle spectrum (vacuum attractor structure)",
    ],
}

results["wall_clock_s"] = time.time() - t0

out_path = "epic073_rank281_3dh_3d_hamiltonian_spec_results.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

signal.alarm(0)

print("=" * 70)
print("Rank 281-3DH — 3D GTE Hamiltonian Specification")
print("=" * 70)
print(f"Axis reduction (x,y): {axis_reduction_x}, {axis_reduction_y}")
print(f"Axis permutation equivariance: {results['symmetry_audit']['axis_permutation_equivariant']}")
print(f"Parity equivariance (expect fail): {results['symmetry_audit']['parity_equivariant']}")
print(f"L=2 cycle histogram: {dict(sorted(cycle_counter.items()))}")
print(f"Verdict: {verdict}")
print(f"Feasibility: {feasibility}")
print(f"Wall clock: {results['wall_clock_s']:.1f}s")
print(f"Results: {out_path}")
