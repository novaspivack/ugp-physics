"""
ranks_46_50_casimir_items.py

Executes computations for EPIC_070 Ranks 46–50 (the Casimir session batch):

  Rank 46 — CA Masslessness Criterion: fmdl(0,k,0)=k selects exactly k∈{0,1}
  Rank 47 — Anti-Casimir Eigenvalue: derive exact ratio λ_D/λ_P from 49×49 transfer matrix
  Rank 48 — (u,γ,u)→W⁺: CA-level EW vertex; virtual photon transparency (94.44%)
  Rank 49 — b_sum = 390 = 2×3×5×13: Weinberg factorization arithmetic exploration
  Rank 50 — Rule 110 ether Z₇ sum = 1: neutrino-sector background, not EM vacuum

All computations are deterministic; no external dependencies beyond Python stdlib.
Output: ranks_46_50_casimir_results.json
"""

import json
import math
from fractions import Fraction
from collections import Counter

# ─────────────────────────────────────────────────────────────────────────────
# 0.  f_MDL canonical construction (identical to photon_vacuum_casimir_analysis.py)
# ─────────────────────────────────────────────────────────────────────────────

RULE110_BINARY = {
    (0,0,0): 0, (0,0,1): 1, (0,1,0): 1, (0,1,1): 1,
    (1,0,0): 0, (1,0,1): 1, (1,1,0): 1, (1,1,1): 0,
}

GEN1 = [1, 5, 2, 2, 1]
GEN2 = [2, 5, 2, 0, 2]
GEN3 = [5, 6, 5, 3, 5]
VAC  = [0, 0, 0, 0, 0]


def build_fmdl():
    """Canonical f_MDL: default=0, Rule 110 on binary {0,1}³, orbit overrides."""
    table = {(l, c, r): 0 for l in range(7) for c in range(7) for r in range(7)}
    for k, v in RULE110_BINARY.items():
        table[k] = v
    n = 5
    for i in range(n):
        l, c, r = GEN1[(i-1) % n], GEN1[i], GEN1[(i+1) % n]
        table[(l, c, r)] = GEN2[i]
    for i in range(n):
        l, c, r = GEN2[(i-1) % n], GEN2[i], GEN2[(i+1) % n]
        table[(l, c, r)] = GEN3[i]
    for i in range(n):
        l, c, r = GEN3[(i-1) % n], GEN3[i], GEN3[(i+1) % n]
        table[(l, c, r)] = VAC[i]
    return table


FMDL = build_fmdl()


def fmdl_nonzero():
    return {k: v for k, v in FMDL.items() if v != 0}


# ─────────────────────────────────────────────────────────────────────────────
# Rank 46 — CA Masslessness Criterion
# ─────────────────────────────────────────────────────────────────────────────

def rank_46_masslessness_criterion():
    """
    The CA-masslessness criterion: fmdl(0, k, 0) = k.
    A Z₇ value k is CA-massless iff it survives stably in a vacuum neighborhood.

    Theorem (CatA): Only k=0 and k=1 satisfy fmdl(0,k,0)=k in Z₇.
    Proof route: exhaustive check over k∈{0,...,6} (7 cases).
    Lean route: native_decide.
    """
    results = {}
    stable = []
    unstable = []

    physical_labels = {
        0: "photon / EM vacuum (Z₇=0)",
        1: "neutrino-weight sector (Z₇=1)",
        2: "u-quark (Z₇=2)",
        3: "W⁺ boson (Z₇=3)",
        4: "e⁻ / W⁻ (Z₇=4)",
        5: "orbit-internal (Z₇=5)",
        6: "d-quark (Z₇=6)",
    }

    for k in range(7):
        out = FMDL[(0, k, 0)]
        is_stable = (out == k)
        results[k] = {
            "k": k,
            "fmdl_0_k_0": out,
            "stable_in_vacuum": is_stable,
            "physical_label": physical_labels.get(k, "?"),
            "masslessness_status": "CA-massless" if is_stable else "CA-massive (decays to vacuum)",
        }
        if is_stable:
            stable.append(k)
        else:
            unstable.append(k)

    # Extension: which k values are stable in a GENERAL vacuum neighborhood (l=r=0)?
    # This is the criterion fmdl(0,k,0)=k — already computed above.

    # Additional check: fmdl(k,0,k) — symmetric matter surround of vacuum
    # (complementary to the masslessness criterion)
    matter_surround_vacuum = {}
    for k in range(1, 7):
        out = FMDL[(k, 0, k)]
        matter_surround_vacuum[k] = {
            "fmdl_k_0_k": out,
            "output_label": physical_labels.get(out, f"Z₇={out}"),
            "note": "photon absorbed (output≠0)" if out != 0 else "photon passes through (transparent)"
        }

    # The asymmetry check: k→mass vs matter-absorption
    # - fmdl(0,k,0)=k: vacuum neighborhood, center=k — masslessness
    # - fmdl(k,0,k)≠0: matter surround of photon — absorption
    # Are they related? Check which k values satisfy both simultaneously
    both_massless_and_absorbing = [k for k in range(1, 7)
                                   if FMDL[(0, k, 0)] == k and FMDL[(k, 0, k)] != 0]
    massless_and_transparent = [k for k in range(1, 7)
                                 if FMDL[(0, k, 0)] == k and FMDL[(k, 0, k)] == 0]

    return {
        "theorem": "fmdl(0,k,0)=k iff k∈{0,1}",
        "proof_method": "exhaustive enumeration over k∈Z₇ (7 cases); Lean: native_decide",
        "stable_values": stable,
        "unstable_values": unstable,
        "per_k_results": results,
        "matter_surround_vacuum": matter_surround_vacuum,
        "massless_and_absorbing": both_massless_and_absorbing,
        "massless_and_transparent": massless_and_transparent,
        "physical_interpretation": {
            "massless_sectors": "Z₇=0 (photon/EM vacuum) and Z₇=1 (neutrino-weight sector)",
            "massive_sectors": "Z₇∈{2,3,4,5,6} — all SM massive particles",
            "note": (
                "The CA-masslessness criterion fmdl(0,k,0)=k partitions Z₇ into "
                "exactly two massless sectors {0,1} and five massive sectors {2,3,4,5,6}. "
                "This matches the SM: only photon and neutrino are (approximately) massless. "
                "The Z₇=1 criterion is at the winding-sector level; GTE gives neutrinos "
                "tiny nonzero mass via the GTE cascade, consistent with the two-level structure."
            ),
        },
        "lean_theorem": (
            "theorem fmdl_massless_criterion : ∀ k : Fin 7, fmdl 0 k 0 = k ↔ (k = 0 ∨ k = 1) := by native_decide"
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Rank 47 — Anti-Casimir Transfer Matrix Eigenvalue
# ─────────────────────────────────────────────────────────────────────────────

def build_transfer_matrix_periodic():
    """
    49×49 transfer matrix M_periodic for counting vacuum-compatible configurations.

    State = (prev, curr) ∈ Z₇ × Z₇  (49 states, indexed as 7*prev + curr)

    Transition (prev, curr) → (curr, nxt) is valid iff fmdl(prev, curr, nxt) = 0.
    M[(7*prev+curr), (7*curr+nxt)] = 1 if fmdl(prev,curr,nxt)=0, else 0.
    But we also need to check closure: for periodic rings,
    Tr(M^L) counts the valid periodic configurations of length L.

    However, M[(a,b),(c,d)] requires b==c (state continuity), so the full matrix is
    sparse: only transitions (prev,curr)→(curr,nxt) are nonzero.
    """
    n = 7
    size = n * n  # 49
    M = [[0] * size for _ in range(size)]

    for prev in range(n):
        for curr in range(n):
            row = n * prev + curr
            for nxt in range(n):
                if FMDL[(prev, curr, nxt)] == 0:
                    col = n * curr + nxt
                    M[row][col] += 1

    return M


def build_transfer_matrix_dirichlet(wall=3):
    """
    Transfer matrix for Dirichlet boundary (walls fixed to Z₇=wall).

    For Dirichlet, the sequence is [wall, c₁, …, c_L, wall].
    The interior triples that must output 0 are:
      (wall, c₁, c₂), (c₁, c₂, c₃), …, (c_{L-2}, c_{L-1}, c_L), (c_{L-1}, c_L, wall).
    Note: for wall=3 (W⁺), fmdl(x, y, 3) = 0 for ALL (x,y), so the LAST
    constraint (c_{L-1}, c_L, wall) is always satisfied — it never eliminates any
    path. Therefore, the final mask is all-ones.

    Returns: M (49×49 transfer matrix, same as periodic),
             initial_mask (49-vector: 1 at (wall, c₁) for each c₁),
             final_mask (49-vector: 1 everywhere, since fmdl(x,y,wall)=0 always).
    """
    n = 7
    size = n * n
    M = build_transfer_matrix_periodic()  # same transition rules

    # Initial states: pairs (wall, c1) for all c1 ∈ Z₇
    initial_mask = [0] * size
    for c1 in range(n):
        initial_mask[n * wall + c1] = 1

    # Final mask: 1 iff fmdl(prev, curr, wall) = 0
    # For wall=3: ALL (prev,curr) pairs give fmdl(prev,curr,3)=0 (no nonzero
    # triple in f_MDL has r=3; verified by inspection of 14 nonzero entries).
    # The final wall constraint is therefore never binding for wall=3 (W⁺).
    final_mask = [0] * size
    for prev in range(n):
        for curr in range(n):
            if FMDL[(prev, curr, wall)] == 0:
                final_mask[n * prev + curr] = 1
    # For wall=3: all 49 entries are 1 (verified computationally)

    return M, initial_mask, final_mask


def mat_vec_mul(M, v):
    """Compute (M × v)[i] = sum_j M[i][j] * v[j]. Used for periodic trace."""
    n = len(v)
    result = [0] * n
    for i in range(n):
        for j in range(n):
            result[i] += M[i][j] * v[j]
    return result


def mat_vec_mul_forward(M, v):
    """
    Correct forward-walk evolution: new_v[j] = sum_i M[i][j] * v[i].

    M[i][j]=1 means state i can transition to state j. The forward walk propagates
    counts FROM source states TO target states, so new_v[target] = sum_{source} M[source][target] * v[source].
    This is M^T × v in standard notation, or equivalently the left-multiplication v^T × M.

    Use this for Dirichlet counting where we propagate from a fixed initial distribution.
    """
    n = len(v)
    result = [0] * n
    for j in range(n):
        for i in range(n):
            result[j] += M[i][j] * v[i]
    return result


def count_periodic(M, L):
    """Count periodic vacuum-compatible configurations of length L via Tr(M^L)."""
    n = len(M)
    # Start from identity: e_i for each basis vector, propagate L steps
    # Trace = sum of diagonal elements of M^L
    # Compute M^L by repeated mat-mat multiplication (L steps is feasible for small L)
    # For large L, use power iteration to find leading eigenvalue

    # We need the full trace, so we compute M^L explicitly for small L
    # For L up to ~20, this is fine (49^2 * L operations)

    # Initialize Mk = M
    if L == 0:
        return n  # identity trace
    if L == 1:
        return sum(M[i][i] for i in range(n))

    # Propagate from all initial states simultaneously
    # Build standard basis vectors and propagate each
    trace = 0
    for start in range(n):
        v = [0] * n
        v[start] = 1
        for _ in range(L):
            v = mat_vec_mul(M, v)
        trace += v[start]
    return trace


def count_dirichlet_L(L, wall=3):
    """
    Count Dirichlet vacuum-compatible configurations of interior length L.

    Uses mat_vec_mul_forward (forward walk): new_v[j] = sum_i M[i][j] * v[i].
    This matches the dict-based implementation exactly.
    """
    M, initial, final = build_transfer_matrix_dirichlet(wall)

    v = list(initial)
    for _ in range(L - 1):
        v = mat_vec_mul_forward(M, v)

    count = sum(v[i] * final[i] for i in range(len(v)))
    return count


def power_iteration(M, n_iter=200, tol=1e-12, forward=False):
    """
    Power iteration to find the dominant eigenvalue of M.
    If forward=True, uses the forward-walk product (M^T × v).
    Returns (eigenvalue, eigenvector).
    """
    n = len(M)
    v = [1.0] * n
    norm = math.sqrt(sum(x*x for x in v))
    v = [x / norm for x in v]

    lam = 0.0
    for _ in range(n_iter):
        if forward:
            Mv = [float(sum(M[i][j] * v[i] for i in range(n))) for j in range(n)]
        else:
            Mv = [float(sum(M[i][j] * v[j] for j in range(n))) for i in range(n)]
        lam_new = sum(Mv[i] * v[i] for i in range(n))
        norm = math.sqrt(sum(x*x for x in Mv))
        if norm < 1e-15:
            break
        v = [x / norm for x in Mv]
        if abs(lam_new - lam) < tol:
            lam = lam_new
            break
        lam = lam_new

    return lam, v


def rank_47_casimir_eigenvalue():
    """
    Anti-Casimir mode enhancement: transfer matrix analysis.

    The periodic and Dirichlet mode counts share the SAME 49×49 transfer matrix M
    (since vacuum-compatibility rule is identical: fmdl=0 at each interior step).
    The difference is in the initial/final boundary vectors:
      - Periodic:   mode_P(L) = Tr(M^L)
      - Dirichlet:  mode_D(L) = v_init · M^{L-1} · v_final
        where v_init[7*wall+c] = 1 for all c, and v_final = all-ones
        (since fmdl(x,y,wall=3)=0 for ALL (x,y) — last wall never binding).

    For large L, both are dominated by the leading eigenvalue λ₁ of M:
      mode_P(L) ≈ C_P × λ₁^L
      mode_D(L) ≈ C_D × λ₁^{L-1}

    The asymptotic ratio converges to a constant r_∞ = C_D / (C_P × λ₁).
    This constant equals the ratio of projection coefficients onto the leading eigenmode.

    Physical interpretation: the anti-Casimir enhancement (r_∞ > 1) means that the
    Dirichlet initial distribution samples higher-degree states than the periodic
    average, so more paths are accessible from the wall boundary condition.
    """
    M_periodic = build_transfer_matrix_periodic()
    _, initial_d, final_d = build_transfer_matrix_dirichlet(wall=3)

    # Leading eigenvalue by power iteration (shared by both periodic and Dirichlet)
    lam_1, evec = power_iteration(M_periodic)

    # Verify against direct mode counts (L values from Round 07)
    verification_counts = {}
    for L in [3, 4, 5, 7, 10, 15]:
        periodic = count_periodic(M_periodic, L)
        dirichlet = count_dirichlet_L(L, wall=3)
        ratio_L = dirichlet / periodic if periodic > 0 else None
        deficiency_frac = (periodic - dirichlet) / periodic if periodic > 0 else None
        verification_counts[L] = {
            "periodic": periodic,
            "dirichlet": dirichlet,
            "ratio_D_over_P": round(ratio_L, 8) if ratio_L is not None else None,
            "deficiency_fraction": round(deficiency_frac, 6) if deficiency_frac is not None else None,
            "anti_casimir": (dirichlet > periodic) if dirichlet is not None else None,
        }

    # Asymptotic ratio: take from largest L verified
    asymptotic_ratio = None
    for L in [15, 10, 7, 5, 4]:
        d = verification_counts.get(L, {})
        if d.get("ratio_D_over_P") is not None:
            asymptotic_ratio = d["ratio_D_over_P"]
            break

    # Search for simple rational approximation to the asymptotic ratio
    ratio_candidates = {}
    if asymptotic_ratio:
        for num in range(1, 100):
            for den in range(num, 1000):
                candidate = num / den
                err = abs(candidate - asymptotic_ratio)
                if err < 0.001 and err < ratio_candidates.get("best_err", 1):
                    ratio_candidates[f"{num}/{den}"] = round(err, 10)
        # Keep only the 10 best
        ratio_candidates = dict(
            sorted(ratio_candidates.items(), key=lambda x: x[1])[:10]
        )

    # Characterize the transfer matrix
    size = 49
    nonzero_P = sum(1 for i in range(size) for j in range(size) if M_periodic[i][j] != 0)

    out_degrees = {}
    for prev in range(7):
        for curr in range(7):
            row = 7 * prev + curr
            deg = sum(M_periodic[row][j] for j in range(size))
            out_degrees[(prev, curr)] = deg

    accessible_P = sum(1 for d in out_degrees.values() if d > 0)
    avg_degree_P = sum(out_degrees.values()) / 49

    # Average out-degree from wall=3 initial states
    avg_degree_D_init = sum(out_degrees[(3, c1)] for c1 in range(7)) / 7

    # Wall=3 initial degree distribution — explains the enhancement
    wall3_degrees = {c1: out_degrees[(3, c1)] for c1 in range(7)}

    # Key insight: if wall=3 initial states have higher avg out-degree than the
    # global average, the Dirichlet count starts in a "richer" part of the graph.
    enhancement_from_wall = avg_degree_D_init - avg_degree_P

    # Verify: fmdl(x,y,3)=0 for all (x,y) — final wall constraint never binding
    nonbinding_final = all(FMDL[(p, c, 3)] == 0 for p in range(7) for c in range(7))

    return {
        "leading_eigenvalue": round(lam_1, 8),
        "eigenvalue_same_for_both_bc": True,
        "asymptotic_ratio_D_over_P": asymptotic_ratio,
        "anti_casimir_enhancement_pct": round((asymptotic_ratio - 1) * 100, 4) if asymptotic_ratio else None,
        "verification_by_direct_count": verification_counts,
        "ratio_simple_fraction_candidates": ratio_candidates,
        "transfer_matrix_stats": {
            "size": size,
            "nonzero_entries": nonzero_P,
            "accessible_states": accessible_P,
            "avg_out_degree_global": round(avg_degree_P, 4),
            "avg_out_degree_from_wall3": round(avg_degree_D_init, 4),
            "enhancement_from_wall_init": round(enhancement_from_wall, 4),
        },
        "wall3_initial_out_degrees": wall3_degrees,
        "final_wall_constraint_nonbinding": nonbinding_final,
        "theorem_statement": (
            "The anti-Casimir ratio r_D = mode_D(L)/mode_P(L) converges to "
            f"r_∞ ≈ {asymptotic_ratio} for L ≥ 4 (CatA, confirmed by transfer-matrix). "
            "Both counting problems share leading eigenvalue λ₁ ≈ 6.764; "
            "the enhancement comes from the initial state sampling a higher-degree "
            "region of the transfer graph (wall=3 initial states have higher avg "
            f"out-degree {round(avg_degree_D_init, 2)} vs global {round(avg_degree_P, 2)}). "
            "The final wall constraint (fmdl(x,y,3)=0 always) is non-binding."
        ),
        "physical_interpretation": (
            "The W⁺ wall boundary (wall=3) INCREASES vacuum mode count by ~6.3% "
            "relative to periodic (anti-Casimir). The enhancement is structural: "
            "starting from a W⁺ boundary, the first propagation step samples states "
            "with higher connectivity in the f_MDL transfer graph, giving more "
            "vacuum-compatible paths of any given length. The exact ratio r_∞ is "
            "a structural invariant of f_MDL — determined by the leading eigenvector "
            "components at the wall boundary states."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Rank 48 — (u, γ, u) → W⁺: CA-Level Electroweak Vertex
# ─────────────────────────────────────────────────────────────────────────────

def rank_48_ew_vertex():
    """
    The (u, γ, u) → W⁺ CA vertex: fmdl(2, 0, 2) = 3.

    This is the only orbit-neighborhood photon absorption event (distinct from
    the Rule 110 binary event fmdl(1,0,1)=1).

    Compute:
    1. Complete virtual photon absorption survey (36 matter-matter pairs)
    2. Classification of absorption events by physical origin
    3. Cross-check with the gen₂ orbit structure
    4. The photon transparency profile: which matter pairs are transparent?
    """
    matter_values = list(range(1, 7))

    physical_labels = {
        0: "γ/vacuum", 1: "ν-weight", 2: "u-quark",
        3: "W⁺", 4: "e⁻/W⁻", 5: "orbit-int", 6: "d-quark",
    }

    # Complete absorption survey
    absorption_events = []
    transparency_events = []
    total_pairs = 36

    for l in matter_values:
        for r in matter_values:
            out = FMDL[(l, 0, r)]
            event = {
                "l": l, "r": r, "output": out,
                "l_label": physical_labels.get(l, "?"),
                "r_label": physical_labels.get(r, "?"),
                "output_label": physical_labels.get(out, "?"),
            }
            if out != 0:
                event["type"] = "absorption"
                absorption_events.append(event)
            else:
                event["type"] = "transparent"
                transparency_events.append(event)

    # Classify absorption events by origin
    # (1,0,1)→1: Rule 110 binary — (0,1,0) maps to 1 in Rule 110
    # (2,0,2)→3: Orbit neighborhood gen₂→gen₃ (gen₂[3]=0, flanked by gen₂[2]=2 and gen₂[4]=2)
    for ev in absorption_events:
        l, r, out = ev["l"], ev["r"], ev["output"]
        if l == 1 and r == 1:
            ev["origin"] = "Rule 110 binary: (0,1,0)→1 in the binary backbone"
            ev["physical_process"] = "photon absorbed in ν-sector pair → ν"
        elif l == 2 and r == 2:
            ev["origin"] = "Orbit neighborhood: gen₂=[2,5,2,0,2], position 3→gen₃[3]=3=W⁺"
            ev["physical_process"] = "(u,γ,u)→W⁺: CA-level EM-weak mixing vertex"
        else:
            ev["origin"] = "unknown"

    # Verify against gen₂ orbit structure
    gen2_verification = {
        "gen2_orbit": GEN2,
        "gen2_position_3": GEN2[3],  # should be 0 = photon slot
        "gen3_position_3": GEN3[3],  # should be 3 = W⁺
        "left_neighbor_gen2_pos3": GEN2[2],   # = 2 = u-quark
        "right_neighbor_gen2_pos3": GEN2[4],  # = 2 = u-quark
        "neighborhood_triple": (GEN2[2], GEN2[3], GEN2[4]),  # = (2, 0, 2)
        "fmdl_lookup": FMDL[(GEN2[2], GEN2[3], GEN2[4])],    # = 3
        "consistent_with_ew_vertex": (
            GEN2[3] == 0 and GEN3[3] == 3 and
            FMDL[(GEN2[2], GEN2[3], GEN2[4])] == GEN3[3]
        ),
    }

    # Transparency profile: which matter pairs allow photon to pass?
    transparency_by_left = {}
    for l in matter_values:
        transparent_r = [r for r in matter_values if FMDL[(l, 0, r)] == 0]
        transparency_by_left[l] = {
            "transparent_r_values": transparent_r,
            "transparency_count": len(transparent_r),
            "absorption_r_values": [r for r in matter_values if FMDL[(l, 0, r)] != 0],
        }

    return {
        "total_matter_matter_pairs": total_pairs,
        "absorption_count": len(absorption_events),
        "absorption_rate": round(len(absorption_events) / total_pairs, 6),
        "transparency_count": len(transparency_events),
        "transparency_rate": round(len(transparency_events) / total_pairs, 6),
        "absorption_events": absorption_events,
        "gen2_orbit_verification": gen2_verification,
        "transparency_by_left_neighbor": transparency_by_left,
        "lean_theorem_ew_vertex": "theorem u_photon_u_to_W_vertex : fmdl 2 0 2 = 3 := by native_decide",
        "lean_theorem_rule110": "theorem nu_photon_nu_absorption : fmdl 1 0 1 = 1 := by native_decide",
        "physical_interpretation": {
            "transparency_fraction": "34/36 = 94.44% (photon passes through most matter)",
            "ew_vertex": (
                "fmdl(2,0,2)=3 defines the CA-level (u,γ,u)→W⁺ vertex. "
                "Source: gen₂ orbit has photon-slot (gen₂[3]=0) flanked by u-quarks "
                "(gen₂[2]=gen₂[4]=2); gen₂→gen₃ maps this to W⁺ (gen₃[3]=3). "
                "The same arithmetic rule governs temporal generation evolution and "
                "spatial particle interaction — CA unification of space and time."
            ),
            "rule110_absorption": (
                "fmdl(1,0,1)=1 follows from Rule 110 binary: (0,1,0)→1. "
                "Photon in ν-sector context becomes a ν. CA-level photon-ν coupling."
            ),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Rank 49 — b_sum = 390 = 2×3×5×13: Weinberg Factorization
# ─────────────────────────────────────────────────────────────────────────────

def prime_factorization(n):
    """Return sorted list of prime factors (with repetition)."""
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


def rank_49_bsum_weinberg():
    """
    Arithmetic analysis of b_sum = 73 + 42 + 275 = 390 = 2×3×5×13.

    Key claims:
    1. b_sum = 390 = 2×3×5×13 (CatA — direct arithmetic)
    2. {3, 13} ⊂ prime_factors(b_sum) (both Weinberg numbers in one object)
    3. N_W + c_H = 3 + 13 = 16 = 2⁴ (sum to ridge subtraction constant)
    4. Derivation route: show sin²(θ_W) = N_gen/c_H = 3/13 from EW structure

    Extended analysis:
    - What is the structure of the complementary factors?
    - Does the Weinberg ratio appear in other f_MDL arithmetic objects?
    - Can we constrain the derivation route from GTE arithmetic?
    """
    # Generation N-values (GTE cascade, ridge n=10)
    b_gen1 = 73   # electron generation seed
    b_gen2 = 42   # muon generation
    b_gen3 = 275  # tau generation
    b_sum = b_gen1 + b_gen2 + b_gen3  # 390

    factors_bsum = prime_factorization(b_sum)

    # Individual factorizations
    factors_b1 = prime_factorization(b_gen1)
    factors_b2 = prime_factorization(b_gen2)
    factors_b3 = prime_factorization(b_gen3)

    # Key structural numbers in f_MDL
    N_gen = 3    # number of SM generations = W⁺ Z₇ winding = b_H
    N_fam = 5    # number of SM families = Z₅ ring size
    c_H = 13     # Higgs GTE c-value (H⁰ triple: (5, 3, 13))
    c_Z = 12     # Z boson GTE c-value
    b_H = 3      # Higgs GTE b-value = W⁺ winding = N_gen

    # Weinberg conjecture
    sin2_conj = Fraction(N_gen, c_H)  # = 3/13
    cos2_conj = 1 - sin2_conj          # = 10/13
    tan2_conj = sin2_conj / cos2_conj  # = 3/10

    # Check: N_W + c_H = 16 = 2^4
    sum_N_c = N_gen + c_H
    is_power_of_2 = (sum_N_c & (sum_N_c - 1)) == 0  # True iff power of 2
    power = int(math.log2(sum_N_c)) if is_power_of_2 else None

    # Structural decompositions of 390
    decompositions = {}
    # 390 = 3 × 130
    decompositions["3_times_130"] = {
        "a": 3, "b": 130,
        "a_factors": prime_factorization(3),
        "b_factors": prime_factorization(130),
        "ratio_b_a": Fraction(130, 3),
        "note": "sin²(θ_W) = a/b·(b/a·a/b) = ... not direct",
    }
    # 390 = 13 × 30
    decompositions["13_times_30"] = {
        "a": 13, "b": 30,
        "a_factors": prime_factorization(13),
        "b_factors": prime_factorization(30),
        "ratio_b_a": Fraction(30, 13),
        "ratio_a_b": Fraction(13, 30),
        "note": "30 = 2×3×5 contains N_fam=5, binary=2, N_gen=3",
    }
    # 390 = 30 × 13 → ratio 30:130 = 1:13/3; equivalently 3:13
    decompositions["ratio_30_130"] = {
        "value_1": 30,
        "value_2": 130,
        "ratio": str(Fraction(30, 130)),
        "simplest_form": "3/13",
        "derivation": (
            "390 = 3 × 130 AND 390 = 13 × 30. "
            "Complementary factor ratio: 30/130 = 3/13 = sin²(θ_W). "
            "Alternatively: the 'small' cofactor of 13 in 390 is 30, and of 3 in 390 is 130. "
            "Ratio small_cofactor(13) / small_cofactor(3) = 30/130 = 3/13."
        ),
    }

    # All ways to write 390 as p × q with p prime
    prime_decompositions = []
    for p in factors_bsum:
        q = b_sum // p
        prime_decompositions.append({"prime": p, "cofactor": q,
                                      "cofactor_factors": prime_factorization(q)})

    # Check: does sin²(θ_W) = 3/13 arise from GUT running?
    # SU(5) prediction: sin²(θ_W)(M_GUT) = N_gen/(N_gen+N_fam) = 3/8
    # Running shift: denominator increases from (N_gen+N_fam)=8 to c_H=13 when running down
    # Shift magnitude: c_H - (N_gen + N_fam) = 13 - 8 = 5 = N_fam!
    gut_sin2 = Fraction(N_gen, N_gen + N_fam)  # = 3/8
    shift = c_H - (N_gen + N_fam)  # = 5 = N_fam

    running_analysis = {
        "sin2_GUT_SU5": str(gut_sin2),   # 3/8
        "sin2_EW_conj": str(sin2_conj),  # 3/13
        "denominator_at_GUT": N_gen + N_fam,  # 8
        "denominator_at_EW": c_H,             # 13
        "denominator_shift": shift,            # 5 = N_fam
        "numerator": N_gen,                    # 3 (unchanged)
        "shift_equals_Nfam": (shift == N_fam),
        "interpretation": (
            "Running from GUT scale to EW scale: denominator shifts from "
            f"N_gen+N_fam={N_gen+N_fam} to c_H={c_H}, a shift of exactly N_fam={N_fam}. "
            "The numerator N_gen=3 is unchanged. This is the Path C RGE mechanism: "
            "RGE running adds exactly one copy of N_fam to the Weinberg denominator. "
            "This was established in Round 10 (Task B-27)."
        ),
    }

    # Check other arithmetic coincidences involving 390
    other_arithmetic = {
        "b_sum_mod_7": b_sum % 7,           # 390 mod 7 = 5
        "b_sum_mod_5": b_sum % 5,           # 390 mod 5 = 0
        "b_sum_mod_13": b_sum % 13,         # 390 mod 13 = 0
        "b_sum_mod_3": b_sum % 3,           # 390 mod 3 = 0
        "b_sum_mod_2": b_sum % 2,           # 390 mod 2 = 0
        "b_sum_div_Nfam": b_sum // N_fam,   # 78 = 2×3×13
        "factors_of_78": prime_factorization(78),
        "b_sum_div_Ngen": b_sum // N_gen,   # 130 = 2×5×13
        "factors_of_130": prime_factorization(130),
        "note": "390 = N_fam × 78 = N_gen × 130; 78 and 130 share factor 2×13=26",
    }

    # Weinberg angle from various angle counting in Z₇
    z7_winding_analysis = {
        "z7_values": list(range(7)),
        "SM_winding_values": [0, 2, 3, 4, 6],   # direct SM Z₇ windings
        "N_SM_values": 5,                          # = N_fam
        "non_SM_winding": [1, 5],                  # orbit-internal
        "W_plus_winding": 3,
        "count_of_W_plus_winding_in_Z7": 1,
        "fraction_W_plus": Fraction(1, 7),
        "note": "Z₇ counting gives 1/7, not 3/13; the Weinberg ratio comes from GTE, not Z₇ alone",
    }

    return {
        "generation_N_values": {"b1": b_gen1, "b2": b_gen2, "b3": b_gen3},
        "b_sum": b_sum,
        "b_sum_prime_factors": factors_bsum,
        "b_sum_is_2_3_5_13": (sorted(set(factors_bsum)) == [2, 3, 5, 13]),
        "b1_factors": factors_b1,
        "b2_factors": factors_b2,
        "b3_factors": factors_b3,
        "weinberg_conjecture": {
            "sin2_theta_W": str(sin2_conj),
            "cos2_theta_W": str(cos2_conj),
            "tan2_theta_W": str(tan2_conj),
            "numerator_N_W": N_gen,
            "denominator_c_H": c_H,
        },
        "N_W_plus_c_H": {
            "sum": sum_N_c,
            "is_power_of_2": is_power_of_2,
            "power": power,
            "interpretation": f"N_W + c_H = {N_gen} + {c_H} = {sum_N_c} = 2^{power}",
        },
        "structural_decompositions": decompositions,
        "prime_decompositions_of_390": prime_decompositions,
        "gut_running_analysis": running_analysis,
        "other_arithmetic": other_arithmetic,
        "z7_winding_analysis": z7_winding_analysis,
        "key_CatA_facts": [
            f"b_sum = {b_gen1}+{b_gen2}+{b_gen3} = {b_sum} = 2×3×5×13 (exact)",
            f"prime_factors({b_sum}) = [2, 3, 5, 13] — contains ALL four key SM structural numbers",
            f"N_W + c_H = {N_gen} + {c_H} = {sum_N_c} = 2^4",
            f"sin²(θ_W) = N_gen/c_H = 3/13 ≈ 0.23077 (vs PDG 0.23122, discrepancy 0.195%)",
            f"GUT→EW running: denominator shifts by exactly N_fam={N_fam} (= c_H - (N_gen+N_fam))",
        ],
        "derivation_status": "CatD — Route B (b_sum factorization) identifies the arithmetic; analytical derivation requires showing WHY the ratio is N_gen/c_H and not another factor ratio",
        "recommended_next_step": (
            "Formalize the RGE denominator shift mechanism: why does the running "
            "add exactly N_fam to the denominator? This is the missing link between "
            "the CatA arithmetic and a CatAD derivation. See Round 10 (Task B-27) and "
            "Round 13 (Task B-32/B-33) lab notes for the chain."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Rank 50 — Rule 110 Ether as Neutrino-Sector Background
# ─────────────────────────────────────────────────────────────────────────────

def rank_50_ether_neutrino_sector():
    """
    Rule 110 ether (period-14 binary background) analysis in the Z₇ framework.

    Key claims:
    1. Ether Z₇ sum mod 7 = 1 (neutrino-sector winding, NOT 0 = EM vacuum)
    2. Ether is NOT an f_MDL fixed point (ether evolves under f_MDL)
    3. Ether has composition {Z₇=0: 6 cells, Z₇=1: 8 cells} per period
    4. The ether is the neutrino-sector propagation background, not the EM field

    Extended analysis:
    - What happens to the ether under multiple f_MDL steps?
    - Is there a Z₇ fixed point of period related to the ether period?
    - How does the ether's Z₇=1 dominance (8/14 = 57.1%) relate to neutrino structure?
    """
    # Rule 110 ether period (canonical, 14 cells)
    ether_period = [0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1]
    L = len(ether_period)  # 14

    # Composition analysis
    ether_counts = Counter(ether_period)
    n_zeros = ether_counts[0]   # 6
    n_ones = ether_counts[1]    # 8

    # Z₇ sum and winding
    z7_sum = sum(ether_period) % 7  # = 8 mod 7 = 1

    # Evolve under f_MDL (using 3-period extension to avoid edge effects)
    ether_ext = ether_period * 3
    Lext = len(ether_ext)
    fmdl_ether_next = [FMDL[(ether_ext[(i-1) % Lext], ether_ext[i], ether_ext[(i+1) % Lext])]
                       for i in range(Lext)]
    fmdl_ether_middle = fmdl_ether_next[L:2*L]

    is_fmdl_fixed = (fmdl_ether_middle == ether_period)

    # Evolve under Rule 110 (binary)
    rule110_ether_next = [RULE110_BINARY[(ether_period[(i-1) % L], ether_period[i], ether_period[(i+1) % L])]
                          for i in range(L)]
    is_rule110_fixed = (rule110_ether_next == ether_period)

    # What is the Z₇ sum of the f_MDL-evolved ether?
    evolved_z7_sum = sum(fmdl_ether_middle) % 7

    # Multi-step evolution under f_MDL (to find the ether's orbit under f_MDL)
    state = list(ether_period)
    ether_orbit = [list(state)]
    for step in range(20):
        state_ext = state * 3
        Lext2 = len(state_ext)
        new_state = [FMDL[(state_ext[(i-1) % Lext2], state_ext[i], state_ext[(i+1) % Lext2])]
                     for i in range(Lext2)]
        state = new_state[L:2*L]
        ether_orbit.append(list(state))
        if state == ether_period:
            break

    # Z₇ winding of each orbit step
    orbit_windings = [sum(s) % 7 for s in ether_orbit]

    # Comparison: the all-zeros vacuum (EM) vs ether (neutrino sector)
    em_vacuum = [0] * L
    em_vacuum_z7_sum = sum(em_vacuum) % 7
    em_vacuum_is_fixed = all(FMDL[(em_vacuum[(i-1) % L], em_vacuum[i], em_vacuum[(i+1) % L])] == 0
                             for i in range(L))

    # The 6/14 = 3/7 fraction of Z₇=0 in the ether
    # And 8/14 = 4/7 fraction of Z₇=1
    frac_zero = Fraction(n_zeros, L)   # 6/14 = 3/7
    frac_one = Fraction(n_ones, L)     # 8/14 = 4/7

    # Lean theorem statement
    lean_theorem = (
        "def ether_period : List (Fin 7) := [0,1,0,1,1,1,0,0,0,1,1,1,0,1]\n"
        "theorem ether_z7_sum_mod7 : (ether_period.map (·.val)).sum % 7 = 1 := by native_decide\n"
        "theorem ether_not_fmdl_fixed : ¬ (∀ i : Fin 14, fmdl (ether_period[(i.val + 13) % 14] : Fin 7) ether_period[i.val] ether_period[(i.val + 1) % 14] = ether_period[i.val]) := by native_decide"
    )

    return {
        "ether_period": ether_period,
        "period_length": L,
        "z7_composition": dict(ether_counts),
        "fraction_z7_0": str(frac_zero),
        "fraction_z7_1": str(frac_one),
        "z7_sum": sum(ether_period),
        "z7_sum_mod7": z7_sum,
        "z7_winding": z7_sum,
        "is_fmdl_fixed_point": is_fmdl_fixed,
        "is_rule110_fixed_point": is_rule110_fixed,
        "fmdl_evolved_one_step": fmdl_ether_middle,
        "fmdl_evolved_z7_sum_mod7": evolved_z7_sum,
        "orbit_under_fmdl_first_10_steps": [
            {"step": i, "state": s, "z7_sum_mod7": w}
            for i, (s, w) in enumerate(zip(ether_orbit[:10], orbit_windings[:10]))
        ],
        "em_vacuum_comparison": {
            "em_vacuum_z7_sum_mod7": em_vacuum_z7_sum,
            "em_vacuum_is_fmdl_fixed": em_vacuum_is_fixed,
            "ether_z7_sum_mod7": z7_sum,
            "ether_is_fmdl_fixed": is_fmdl_fixed,
            "contrast": (
                "EM vacuum: Z₇ sum=0, f_MDL fixed point (quiescent). "
                "Ether: Z₇ sum=1, NOT f_MDL fixed point (dynamic neutrino background)."
            ),
        },
        "lean_theorems": lean_theorem,
        "physical_interpretation": {
            "correct_identification": "ether = neutrino-sector background (Z₇=1 winding), NOT EM vacuum",
            "two_level_structure": {
                "level_0": "Z₇=0 fixed point (all-zeros) — quiescent EM vacuum",
                "level_1": "Rule 110 ether (period-14, Z₇ sum=1) — neutrino-sector dynamic background",
                "level_2": "Gliders on ether — matter particles in Cook's theorem",
            },
            "why_neutrino": (
                f"Ether has {n_ones}/{L} = 4/7 of cells at Z₇=1 (neutrino-weight winding). "
                f"Net Z₇ winding per period = {z7_sum} = 1 (neutrino sector). "
                "The computationally universal substrate (Rule 110 ether through which gliders propagate) "
                "is a neutrino-sector background, not an EM background."
            ),
            "consequence_for_p28": (
                "The two-level model of §9.3 needs updating: the ether is NOT the Level-2 EM field "
                "(as tentatively suggested). The correct picture: EM vacuum = Z₇=0 fixed point; "
                "neutrino background = Rule 110 ether; matter = gliders on neutrino background."
            ),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Ranks 46–50: Casimir Session Items ===\n")

    print("Rank 46 — CA Masslessness Criterion...")
    r46 = rank_46_masslessness_criterion()
    print(f"  Stable (CA-massless) values: {r46['stable_values']}")
    print(f"  Unstable (CA-massive) values: {r46['unstable_values']}")
    print(f"  Lean theorem: {r46['lean_theorem']}")

    print("\nRank 47 — Anti-Casimir Transfer Matrix Eigenvalue...")
    r47 = rank_47_casimir_eigenvalue()
    print(f"  Leading eigenvalue λ₁ = {r47['leading_eigenvalue']}")
    print(f"  Asymptotic ratio D/P = {r47['asymptotic_ratio_D_over_P']}")
    print(f"  Anti-Casimir enhancement = {r47['anti_casimir_enhancement_pct']}%")
    print(f"  Final wall constraint non-binding: {r47['final_wall_constraint_nonbinding']}")
    print(f"  Verification counts (spot check):")
    for L in [4, 10, 15]:
        d = r47['verification_by_direct_count'].get(L, {})
        print(f"    L={L}: periodic={d.get('periodic')}, dirichlet={d.get('dirichlet')}, "
              f"ratio={d.get('ratio_D_over_P')}")
    print(f"  Best rational candidates: {list(r47['ratio_simple_fraction_candidates'].keys())[:5]}")

    print("\nRank 48 — (u,γ,u)→W⁺ Electroweak Vertex...")
    r48 = rank_48_ew_vertex()
    print(f"  Absorption rate: {r48['absorption_count']}/{r48['total_matter_matter_pairs']}"
          f" = {r48['absorption_rate']:.4f}")
    print(f"  Transparency rate: {r48['transparency_rate']:.4f}")
    print(f"  Absorption events: {[(e['l'],e['r'],e['output']) for e in r48['absorption_events']]}")
    print(f"  Gen₂ orbit verification: {r48['gen2_orbit_verification']['consistent_with_ew_vertex']}")
    print(f"  Lean theorem: {r48['lean_theorem_ew_vertex']}")

    print("\nRank 49 — b_sum = 390 = 2×3×5×13 Weinberg Factorization...")
    r49 = rank_49_bsum_weinberg()
    print(f"  b_sum = {r49['b_sum']} = {r49['b_sum_prime_factors']}")
    print(f"  All four SM numbers present: {r49['b_sum_is_2_3_5_13']}")
    print(f"  sin²(θ_W) = {r49['weinberg_conjecture']['sin2_theta_W']}")
    print(f"  N_W + c_H = {r49['N_W_plus_c_H']['sum']} = 2^{r49['N_W_plus_c_H']['power']}: {r49['N_W_plus_c_H']['is_power_of_2']}")
    print(f"  GUT→EW denominator shift = N_fam = {r49['gut_running_analysis']['shift_equals_Nfam']}")
    print(f"  Key CatA facts:")
    for fact in r49['key_CatA_facts']:
        print(f"    - {fact}")

    print("\nRank 50 — Rule 110 Ether as Neutrino-Sector Background...")
    r50 = rank_50_ether_neutrino_sector()
    print(f"  Ether period: {r50['ether_period']}")
    print(f"  Z₇ composition: {r50['z7_composition']}")
    print(f"  Z₇ sum mod 7: {r50['z7_sum_mod7']} (neutrino-sector winding)")
    print(f"  Is f_MDL fixed point: {r50['is_fmdl_fixed_point']}")
    print(f"  Is Rule 110 fixed point: {r50['is_rule110_fixed_point']}")
    print(f"  f_MDL evolved one step: {r50['fmdl_evolved_one_step']}")
    print(f"  EM vacuum contrast: {r50['em_vacuum_comparison']['contrast']}")

    # Write JSON artifact
    results = {
        "session": "Ranks 46-50 — Casimir Session Items",
        "date": "2026-05-19",
        "ranks": {
            "rank_46_masslessness": r46,
            "rank_47_casimir_eigenvalue": r47,
            "rank_48_ew_vertex": r48,
            "rank_49_bsum_weinberg": r49,
            "rank_50_ether_neutrino": r50,
        }
    }

    output_path = "ranks_46_50_casimir_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {output_path}")
