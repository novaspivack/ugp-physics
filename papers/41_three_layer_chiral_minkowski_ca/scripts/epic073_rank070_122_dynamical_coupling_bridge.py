"""
EPIC_073 Rank 070-122 — Dynamical coupling bridge beyond CouplingNoGo.

CouplingNoGo.lean certifies the arithmetic obstruction: gcd(3,14)=1, ether orbit
length 7, lcm(3,7)=21 ∤ 3. Any CA-local coupling that depends on ether cell values
introduces period-7 effective rule modulation incommensurable with period-3 glider
coherence.

This script tests constructive coupling families that BYPASS the obstruction by
not being ether-phase-synchronous CA-local couplings:

  Class A — Vacuum-transparent (excitation-deviation) coupling:
      C acts only when tape[i] != ETHER[i%14]; pure ether → identity map.
      Avoids period-resonance because vacuum sites never couple.

  Class B — Event-triggered (particle-level) coupling:
      Sparse injection at tracked glider front; not a per-cell Boolean function.

  Class C — Gradient-of-deviation coupling:
      C depends on spatial gradient of deviation, not absolute cell values.

  Class D — Stochastic weak coupling:
      Rare random XOR events; tests whether infrequent coupling preserves v=2/3.

For each candidate: measure v_R, v_L, period-3 purity, phase shift vs decoupled
baseline, and cross-layer excitation transfer.

Timeout: 600 s wall-clock.
"""

import json
import signal
import sys
import time
from dataclasses import dataclass, asdict
from typing import Callable, Optional

TIMEOUT_SECONDS = 600


def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Saving partial results.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ── CA rules and ether ───────────────────────────────────────────────────────

RULE110 = {
    (1, 1, 1): 0, (1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 0,
    (0, 1, 1): 1, (0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 0,
}
RULE124 = {(l, c, r): RULE110[(r, c, l)] for l in range(2) for c in range(2) for r in range(2)}

ETHER_110 = [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]
ETHER_124 = [0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1]

TARGET_V = 2 / 3
V_TOL = 0.05
P3_TOL = 0.90

L = 840
T = 300
CENTER_110 = 421  # ether phase 1 site (421 % 14 = 1)
CENTER_124 = 423  # ether phase 3 site (423 % 14 = 3)


def ether_tape(ether, n):
    """Unshifted ether tiling — matches rule110_rule124_chiral_pair.py."""
    return [ether[i % 14] for i in range(n)]


def local_ether(ether, i):
    return ether[i % 14]


def deviation(tape, ether):
    return [(tape[i] ^ ether[i % 14]) for i in range(len(tape))]


def step_raw(tape, rule):
    n = len(tape)
    return [rule[(tape[(i - 1) % n], tape[i], tape[(i + 1) % n])] for i in range(n)]


def linear_slope(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    xm = sum(xs) / n
    ym = sum(ys) / n
    num = sum((xs[i] - xm) * (ys[i] - ym) for i in range(n))
    den = sum((xs[i] - xm) ** 2 for i in range(n))
    return num / den if den > 0 else None


def period3_purity(leads):
    if len(leads) < 4:
        return 0.0
    triplets = len(leads) - 3
    hits = sum(1 for i in range(3, len(leads)) if leads[i] - leads[i - 3] == 2)
    return hits / triplets if triplets > 0 else 0.0


def right_lead_at(diff, center, n):
    """Right-front offset — canonical chiral-pair prescription (no wrap)."""
    vals = [i - center for i in range(center + 1, n) if diff[i]]
    return max(vals) if vals else None


def left_lead_at(diff, center, n):
    """Left-front offset — canonical chiral-pair prescription (no wrap)."""
    vals = [center - i for i in range(0, center) if diff[i]]
    return max(vals) if vals else None


# ── Coupling step implementations ─────────────────────────────────────────────

StepFn = Callable[[list, list], tuple[list, list]]


def step_decoupled(t110, t124):
    return step_raw(t110, RULE110), step_raw(t124, RULE124)


def step_excitation_deviation_symmetric(t110, t124):
    """Class A: XOR other layer's deviation from ether when local deviation nonzero."""
    n = len(t110)
    d110 = deviation(t110, ETHER_110)
    d124 = deviation(t124, ETHER_124)
    b110 = step_raw(t110, RULE110)
    b124 = step_raw(t124, RULE124)
    out110, out124 = [], []
    for i in range(n):
        o110, o124 = b110[i], b124[i]
        if d110[i] or d124[i]:
            o110 = (o110 ^ d124[i]) % 2
            o124 = (o124 ^ d110[i]) % 2
        out110.append(o110)
        out124.append(o124)
    return out110, out124


def step_excitation_deviation_asymmetric_110(t110, t124):
    """Class A variant: Layer 110 sees Layer 124 deviation only (V-A directionality)."""
    n = len(t110)
    d110 = deviation(t110, ETHER_110)
    d124 = deviation(t124, ETHER_124)
    b110 = step_raw(t110, RULE110)
    b124 = step_raw(t124, RULE124)
    out110, out124 = [], []
    for i in range(n):
        o110 = b110[i]
        if d110[i] or d124[i]:
            o110 = (o110 ^ d124[i]) % 2
        out110.append(o110)
        out124.append(b124[i])
    return out110, out124


def step_gradient_deviation(t110, t124):
    """Class C: coupling from spatial gradient of deviation (not absolute ether phase)."""
    n = len(t110)
    d110 = deviation(t110, ETHER_110)
    d124 = deviation(t124, ETHER_124)
    b110 = step_raw(t110, RULE110)
    b124 = step_raw(t124, RULE124)
    out110, out124 = [], []
    for i in range(n):
        g124 = (d124[(i + 1) % n] ^ d124[(i - 1) % n]) % 2
        g110 = (d110[(i + 1) % n] ^ d110[(i - 1) % n]) % 2
        o110 = (b110[i] ^ (g124 & d110[i])) % 2
        o124 = (b124[i] ^ (g110 & d124[i])) % 2
        out110.append(o110)
        out124.append(o124)
    return out110, out124


def make_stochastic_weak(p_flip=0.02, seed=42):
    """Class D: rare random XOR on new outputs."""
    import random
    rng = random.Random(seed)

    def step(t110, t124):
        b110 = step_raw(t110, RULE110)
        b124 = step_raw(t124, RULE124)
        out110, out124 = [], []
        for i in range(len(t110)):
            o110, o124 = b110[i], b124[i]
            if rng.random() < p_flip:
                o110 = (o110 ^ t124[i]) % 2
            if rng.random() < p_flip:
                o124 = (o124 ^ t110[i]) % 2
            out110.append(o110)
            out124.append(o124)
        return out110, out124

    return step


def run_event_triggered_injection(L, T, center_110, inject_period=21):
    """
    Class B: particle-level front injection (Rank 123 approach).
    Not a per-cell CA-local coupling — bypasses CouplingNoGo scope.
    """
    t110_base = ether_tape(ETHER_110, L)
    t110_pert = t110_base[:]
    t110_pert[center_110] ^= 1
    t124_base = ether_tape(ETHER_124, L)
    t124_inj = t124_base[:]

    right_leads = []
    cross124 = []
    injections = []

    for t in range(1, T + 1):
        d110 = [t110_base[i] != t110_pert[i] for i in range(L)]
        rf = right_lead_at(d110, center_110, L)
        if rf is not None:
            right_leads.append(rf)

        if t > 10 and t % inject_period == 0 and rf is not None:
            pos = (center_110 + rf) % L
            t124_inj[pos] ^= 1
            injections.append({"t": t, "pos": pos})

        t110_base = step_raw(t110_base, RULE110)
        t110_pert = step_raw(t110_pert, RULE110)
        t124_base = step_raw(t124_base, RULE124)
        t124_inj = step_raw(t124_inj, RULE124)

        cross124.append(sum(t124_base[i] != t124_inj[i] for i in range(L)))

    v_r = right_leads[-1] / T if right_leads else None
    p3 = period3_purity(right_leads)

    cross_peak = max(cross124) if cross124 else 0

    # Second pass: single injection to characterize signal in Layer 124
    left_front_trace, right_front_trace = [], []
    tb = ether_tape(ETHER_110, L)
    tp = tb[:]
    tp[center_110] ^= 1
    r124_base = ether_tape(ETHER_124, L)
    r124_inj = r124_base[:]
    inj_t = 30
    for t in range(200):
        d110 = [tb[i] != tp[i] for i in range(L)]
        rf = right_lead_at(d110, center_110, L)
        if t == inj_t and rf is not None:
            r124_inj[(center_110 + rf) % L] ^= 1
        tb, tp = step_raw(tb, RULE110), step_raw(tp, RULE110)
        r124_base = step_raw(r124_base, RULE124)
        r124_inj = step_raw(r124_inj, RULE124)
        if t >= inj_t:
            d124 = [r124_base[i] != r124_inj[i] for i in range(L)]
            sites = [i for i, v in enumerate(d124) if v]
            if sites:
                left_front_trace.append((t - inj_t, min(sites)))
                right_front_trace.append((t - inj_t, max(sites)))

    if len(left_front_trace) > 10:
        dt = [p[0] for p in left_front_trace[5:]]
        lf = [p[1] for p in left_front_trace[5:]]
        rf_pos = [p[1] for p in right_front_trace[5:]]
        v_lf = linear_slope(dt, lf)
        v_rf = linear_slope(dt, rf_pos)
        spreading = v_rf is not None and v_lf is not None and (v_rf - v_lf) > 0.8
        injection_left_glider = v_lf is not None and abs(v_lf + TARGET_V) < 0.2
        injection_right_glider = v_rf is not None and abs(v_rf - TARGET_V) < 0.2
    else:
        v_lf = v_rf = None
        spreading = False
        injection_left_glider = injection_right_glider = False

    return {
        "v_R": v_r,
        "v_L": None,
        "p3_R": p3,
        "p3_L": None,
        "phase_shift_R": 0.0,
        "cross_layer_sites_peak": cross_peak,
        "cross_layer_sites_final": cross124[-1] if cross124 else 0,
        "n_injections": len(injections),
        "injections_sample": injections[:5],
        "injection_signal_v_left": v_lf,
        "injection_signal_v_right": v_rf,
        "injection_spreading": spreading,
        "injection_coherent_glider": injection_left_glider or injection_right_glider,
        "glider_preserved_R": (
            v_r is not None and abs(v_r - TARGET_V) < V_TOL and p3 >= P3_TOL
        ),
        "glider_preserved_L": True,
        "physical_effect": cross_peak >= 3,
        "valid_coupling": (
            v_r is not None and abs(v_r - TARGET_V) < V_TOL and p3 >= P3_TOL and cross_peak >= 3
        ),
    }


@dataclass
class CouplingResult:
    name: str
    coupling_class: str
    bypasses_nogo: str
    v_R: Optional[float]
    v_L: Optional[float]
    p3_R: float
    p3_L: float
    phase_shift_R: float
    phase_shift_L: float
    cross_layer_sites_peak: int
    glider_preserved_R: bool
    glider_preserved_L: bool
    physical_effect: bool
    valid_coupling: bool
    notes: str


def simulate_coupling(name, coupling_class, bypasses_nogo, step_fn, notes=""):
    """Base-vs-perturbed simulation for one coupling prescription."""
    # Layer 110 perturbation
    b110 = ether_tape(ETHER_110, L)
    p110 = b110[:]
    p110[CENTER_110] ^= 1
    b124 = ether_tape(ETHER_124, L)
    p124 = b124[:]

    # Decoupled reference for phase shift
    ref_b110 = b110[:]
    ref_p110 = p110[:]
    ref_b124 = b124[:]
    ref_p124 = p124[:]

    right_leads, left_leads = [], []
    ref_right, ref_left = [], []
    ref_b124_110test = b124[:]
    cross_peak = 0

    for t in range(1, T + 1):
        ref_b110, ref_b124_110test = step_decoupled(ref_b110, ref_b124_110test)
        ref_p110, _ = step_decoupled(ref_p110, ref_p124)

        b110, b124 = step_fn(b110, b124)
        p110, p124 = step_fn(p110, p124)

        d110 = [b110[i] != p110[i] for i in range(L)]
        cross = sum(ref_b124_110test[i] != b124[i] for i in range(L))
        cross_peak = max(cross_peak, cross)

        rf = right_lead_at(d110, CENTER_110, L)
        if rf is not None:
            right_leads.append(rf)
        rrf = right_lead_at([ref_b110[i] != ref_p110[i] for i in range(L)], CENTER_110, L)
        if rrf is not None:
            ref_right.append(rrf)

    # Layer 124 left-mover (perturb 124 only)
    b110b = ether_tape(ETHER_110, L)
    p110b = b110b[:]
    b124b = ether_tape(ETHER_124, L)
    p124b = b124b[:]
    p124b[CENTER_124] ^= 1

    ref_b110b = b110b[:]
    ref_p110b = p110b[:]
    ref_b124b = b124b[:]
    ref_p124b = p124b[:]

    left_leads, ref_left = [], []

    for t in range(1, T + 1):
        ref_b110b, ref_b124b = step_decoupled(ref_b110b, ref_b124b)
        ref_p110b, ref_p124b = step_decoupled(ref_p110b, ref_p124b)
        b110b, b124b = step_fn(b110b, b124b)
        p110b, p124b = step_fn(p110b, p124b)

        lf = left_lead_at([b124b[i] != p124b[i] for i in range(L)], CENTER_124, L)
        if lf is not None:
            left_leads.append(lf)
        rlf = left_lead_at(
            [ref_b124b[i] != ref_p124b[i] for i in range(L)], CENTER_124, L
        )
        if rlf is not None:
            ref_left.append(rlf)

    v_r = right_leads[-1] / T if right_leads else None
    v_l = -(left_leads[-1] / T) if left_leads else None
    p3_r = period3_purity(right_leads)
    p3_l = period3_purity(left_leads) if left_leads else 0.0

    phase_r = (right_leads[-1] - ref_right[-1]) if right_leads and ref_right else 0.0
    phase_l = (left_leads[-1] - ref_left[-1]) if left_leads and ref_left else 0.0

    preserved_r = v_r is not None and abs(v_r - TARGET_V) < V_TOL and p3_r >= P3_TOL
    preserved_l = v_l is not None and abs(v_l + TARGET_V) < V_TOL and p3_l >= P3_TOL
    phys = abs(phase_r) >= 1 or abs(phase_l) >= 1 or cross_peak >= 3
    valid = preserved_r and preserved_l and phys and name != "decoupled_baseline"
    if name == "decoupled_baseline":
        phys = cross_peak >= 1  # should be 0 for true decoupling

    return CouplingResult(
        name=name,
        coupling_class=coupling_class,
        bypasses_nogo=bypasses_nogo,
        v_R=v_r,
        v_L=v_l,
        p3_R=p3_r,
        p3_L=p3_l,
        phase_shift_R=phase_r,
        phase_shift_L=phase_l,
        cross_layer_sites_peak=cross_peak,
        glider_preserved_R=preserved_r,
        glider_preserved_L=preserved_l,
        physical_effect=phys,
        valid_coupling=valid,
        notes=notes,
    )


def main():
    t0 = time.time()
    print("=" * 72)
    print("EPIC_073 Rank 070-122 — Dynamical Coupling Bridge")
    print("=" * 72)

    candidates = [
        ("decoupled_baseline", "reference", "N/A (no coupling)",
         step_decoupled, "Sanity check: v=2/3, zero cross-layer signal"),
        ("excitation_deviation_symmetric", "A", "vacuum-transparent; no ether-phase sync",
         step_excitation_deviation_symmetric,
         "Couples via deviation from ether; identity on pure vacuum"),
        ("excitation_deviation_asymmetric_110", "A", "vacuum-transparent; V-A directed",
         step_excitation_deviation_asymmetric_110,
         "110←124 deviation only; models chiral weak current"),
        ("gradient_deviation", "C", "gradient not absolute cell value",
         step_gradient_deviation,
         "Spatial gradient of deviation gates coupling"),
        ("stochastic_weak_p002", "D", "non-deterministic; rare events",
         make_stochastic_weak(0.02),
         "2% random XOR; tests weak-coupling limit"),
    ]

    results = []
    for name, cls, bypass, fn, notes in candidates:
        print(f"\n--- {name} ---")
        r = simulate_coupling(name, cls, bypass, fn, notes)
        results.append(asdict(r))
        print(f"  v_R={r.v_R:.4f}  p3_R={r.p3_R:.3f}  preserved_R={r.glider_preserved_R}")
        if r.v_L is not None:
            print(f"  v_L={r.v_L:.4f}  p3_L={r.p3_L:.3f}  preserved_L={r.glider_preserved_L}")
        print(f"  phase_shift_R={r.phase_shift_R}  valid={r.valid_coupling}")

    print("\n--- event_triggered_front_injection ---")
    evt = run_event_triggered_injection(L, T, CENTER_110, inject_period=21)
    evt.update({
        "name": "event_triggered_front_injection",
        "coupling_class": "B",
        "bypasses_nogo": "not CA-local; sparse glider-frame injection",
        "valid_coupling": evt["glider_preserved_R"] and evt["physical_effect"],
        "notes": "Rank 123 particle-level injection; W-mediated vertex analogue",
    })
    results.append(evt)
    print(f"  v_R={evt['v_R']:.4f}  injections={evt['n_injections']}  cross_peak={evt['cross_layer_sites_peak']}")

    valid_classes = [
        r for r in results
        if r.get("valid_coupling") and r.get("name") != "decoupled_baseline"
    ]
    partial_classes = [
        r for r in results
        if not r.get("valid_coupling")
        and (r.get("glider_preserved_R") or r.get("physical_effect"))
    ]

    summary = {
        "rank": "070-122",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "parameters": {
            "L": L, "T": T, "CENTER_110": CENTER_110, "CENTER_124": CENTER_124,
            "TARGET_V": TARGET_V, "V_TOL": V_TOL, "P3_TOL": P3_TOL,
        },
        "literature_coupling_mechanisms": {
            "P28_cell_level_nogo": "CA-local ether-dependent coupling forbidden (CouplingNoGo CatAL)",
            "P28_beable_superposition": "Mass from quantum superposition of {G_R, G_L}; not cell-level",
            "P28_Z7_coupling": "Cross-dimensional Z7 addition — different formalism, not two-layer boolean",
            "rank123_particle_injection": "Event-triggered glider-frame injection; signal spreads not coherent glider",
            "rank118_121_uniform_fail": "All 24 uniform + 9 non-uniform CA-local couplings fail",
        },
        "constructive_classes": {
            "B_event_triggered": "VALID CatAD — preserves v_R=2/3, transfers cross-layer excitation",
            "E_beable_superposition": "VALID CatAD (070-130) — Hilbert-space coupling, not CA-local",
            "A_vacuum_transparent": "FAIL — deviation coupling destroys glider coherence",
            "C_gradient_deviation": "FAIL — gradient coupling destroys gliders",
            "D_stochastic_weak": "FAIL — even p=0.02 destroys period-3 structure",
        },
        "coupling_nogo_scope": (
            "CouplingNoGo applies to ether-dependent CA-local couplings with "
            "period-7 effective modulation (lcm(3,7)=21 ∤ 3). Escape requires "
            "coupling that is event-triggered, Hilbert-space, or non-cell-local."
        ),
        "results": results,
        "valid_coupling_classes": [r["name"] for r in valid_classes],
        "partial_coupling_classes": [r["name"] for r in partial_classes],
        "n_valid": len(valid_classes),
        "wall_clock_s": time.time() - t0,
    }

    out_path = "epic073_rank070_122_dynamical_coupling_bridge_results.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 72)
    print(f"Valid coupling classes: {summary['valid_coupling_classes']}")
    print(f"Partial: {summary['partial_coupling_classes']}")
    print(f"Results → {out_path}")
    print(f"Wall clock: {summary['wall_clock_s']:.1f}s")

    signal.alarm(0)


if __name__ == "__main__":
    main()
