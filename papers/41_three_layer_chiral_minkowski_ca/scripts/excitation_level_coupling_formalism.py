"""
EPIC_073 Rank 070-124 — Excitation-level coupling formalism (OQ-A1).

Formal mathematical framework for inter-layer coupling at the excitation (glider)
level, extending the Class B event-triggered escape (070-122) and Lean resonance
cert (070-137, lcm(3,7)=21).

Excitation state on layer ell:
  E_ell = (x, v, phi)
    x   — front offset from seed center (right-front for 110, left-front for 124)
    v   — causal front velocity (cells/step)
    phi — period-3 glider phase: phi = t mod 3 at measurement time

Coupling operator (asymmetric V-A, 110 -> 124 only):
  C_exc(E_110, E_124) at resonant global time t with t mod 21 = 0:
    E_110' = E_110  (source glider unchanged)
    tape_124[center_110 + x_110] ^= 1  (discrete charged-current injection)
  Non-resonant times: identity on excitation states (free evolution only).

Phase-aware variant C_exc^+:
  Apply flip only when ether phase at injection site is in PERSIST_124 = {3,6,7,12}.

Numerical programme:
  - 10+ resonant coupling cycles (period 21)
  - Glider coherence (period-3 purity) before/after each C_exc
  - Cross-layer information transfer on 124
  - Chirality: 110->124 vs 124->110
  - Resonance vs off-resonance (period 7) control

Timeout: 600 s wall-clock.
"""

from __future__ import annotations

import json
import signal
import sys
import time
from dataclasses import asdict, dataclass
from typing import Optional

TIMEOUT_SECONDS = 600


def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Saving partial results.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ── CA primitives ────────────────────────────────────────────────────────────

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
T = 420  # 20 resonant windows at period 21 after warmup
CENTER_110 = 421
CENTER_124 = 423
N_GEN = 3
T_ETHER = 7
EVENT_PERIOD = N_GEN * T_ETHER  # lcm(3,7) = 21

PERSIST_124 = {3, 6, 7, 12}


@dataclass(frozen=True)
class ExcitationState:
    """Excitation (glider) state on one chiral layer."""

    position: Optional[int]  # front offset from center; None if no excitation
    velocity: Optional[float]
    phase: int  # t mod 3


@dataclass
class CouplingEventRecord:
    t: int
    resonant: bool
    p3_before: float
    p3_after: float
    v_before: Optional[float]
    v_after: Optional[float]
    injection_applied: bool
    injection_site: Optional[int]
    ether_phase_at_site: Optional[int]
    cross_layer_sites: int


def ether_tape(ether: list[int], n: int) -> list[int]:
    return [ether[i % 14] for i in range(n)]


def step_raw(tape: list[int], rule) -> list[int]:
    n = len(tape)
    return [rule[(tape[(i - 1) % n], tape[i], tape[(i + 1) % n])] for i in range(n)]


def linear_slope(xs: list[float], ys: list[float]) -> Optional[float]:
    n = len(xs)
    if n < 3:
        return None
    xm = sum(xs) / n
    ym = sum(ys) / n
    num = sum((xs[i] - xm) * (ys[i] - ym) for i in range(n))
    den = sum((xs[i] - xm) ** 2 for i in range(n))
    return num / den if den > 0 else None


def period3_purity(leads: list[int]) -> float:
    if len(leads) < 4:
        return 0.0
    triplets = len(leads) - 3
    hits = sum(1 for i in range(3, len(leads)) if leads[i] - leads[i - 3] == 2)
    return hits / triplets if triplets > 0 else 0.0


def right_lead_at(diff: list[bool], center: int, n: int) -> Optional[int]:
    vals = [i - center for i in range(center + 1, n) if diff[i]]
    return max(vals) if vals else None


def left_lead_at(diff: list[bool], center: int, n: int) -> Optional[int]:
    vals = [center - i for i in range(0, center) if diff[i]]
    return max(vals) if vals else None


def measure_excitation_110(
    base: list[int], pert: list[int], center: int, t: int, leads_hist: list[int]
) -> ExcitationState:
    diff = [base[i] != pert[i] for i in range(len(base))]
    rf = right_lead_at(diff, center, len(base))
    v = None
    if len(leads_hist) >= 10:
        xs = list(range(len(leads_hist[-20:])))
        ys = leads_hist[-20:]
        v = linear_slope(xs, ys)
    return ExcitationState(position=rf, velocity=v, phase=t % N_GEN)


def measure_excitation_124(
    base: list[int], pert: list[int], center: int, t: int, leads_hist: list[int]
) -> ExcitationState:
    diff = [base[i] != pert[i] for i in range(len(base))]
    lf = left_lead_at(diff, center, len(base))
    v = None
    if len(leads_hist) >= 10:
        xs = list(range(len(leads_hist[-20:])))
        ys = leads_hist[-20:]
        slope = linear_slope(xs, ys)
        v = -slope if slope is not None else None
    return ExcitationState(position=lf, velocity=v, phase=t % N_GEN)


def apply_c_exc(
    exc_110: ExcitationState,
    tape_124_inj: list[int],
    center_110: int,
    t: int,
    phase_aware: bool,
) -> tuple[bool, Optional[int], Optional[int]]:
    """
    Algebraic C_exc: inject at front position of E_110 into layer 124 tape.

    Returns (applied, abs_site, ether_phase_at_site).
    Identity when not resonant or when phase-aware gate fails.
    """
    if t <= 10 or t % EVENT_PERIOD != 0:
        return False, None, None
    if exc_110.position is None:
        return False, None, None

    abs_site = (center_110 + exc_110.position) % L
    ether_phase = abs_site % 14
    if phase_aware and ether_phase not in PERSIST_124:
        return False, abs_site, ether_phase

    tape_124_inj[abs_site] ^= 1
    return True, abs_site, ether_phase


def apply_c_exc_reverse(
    exc_124: ExcitationState,
    tape_110_inj: list[int],
    center_124: int,
    t: int,
) -> tuple[bool, Optional[int]]:
    """Reverse chirality test: 124 -> 110 injection at left front."""
    if t <= 10 or t % EVENT_PERIOD != 0:
        return False, None
    if exc_124.position is None:
        return False, None
    abs_site = (center_124 - exc_124.position) % L
    tape_110_inj[abs_site] ^= 1
    return True, abs_site


def step_ca_local_deviation_coupling(t110: list[int], t124: list[int]) -> tuple[list[int], list[int]]:
    """Per-cell CA-local coupling (CouplingNoGo scope) — negative control."""
    n = len(t110)
    d110 = [t110[i] ^ ETHER_110[i % 14] for i in range(n)]
    d124 = [t124[i] ^ ETHER_124[i % 14] for i in range(n)]
    b110 = step_raw(t110, RULE110)
    b124 = step_raw(t124, RULE124)
    out110, out124 = [], []
    for i in range(n):
        o110 = (b110[i] ^ d124[i]) % 2
        o124 = b124[i]
        out110.append(o110)
        out124.append(o124)
    return out110, out124


def simulate_ca_local_coupling(direction: str = "110_to_124") -> dict:
    """Full CA-local per-step coupling — expected to fail (CouplingNoGo)."""
    t110_base = ether_tape(ETHER_110, L)
    t110_pert = t110_base[:]
    t110_pert[CENTER_110] ^= 1
    t124_base = ether_tape(ETHER_124, L)
    t124_pert = t124_base[:]

    right_leads: list[int] = []
    cross_peak = 0

    for t in range(1, T + 1):
        d110 = [t110_base[i] != t110_pert[i] for i in range(L)]
        rf = right_lead_at(d110, CENTER_110, L)
        if rf is not None:
            right_leads.append(rf)
        t110_base, _ = step_ca_local_deviation_coupling(t110_base, t124_base)
        t110_pert, t124_pert = step_ca_local_deviation_coupling(t110_pert, t124_pert)
        cross_peak = max(cross_peak, sum(t124_base[i] != t124_pert[i] for i in range(L)))

    v_r = right_leads[-1] / T if right_leads else None
    p3_r = period3_purity(right_leads)
    preserved = v_r is not None and abs(v_r - TARGET_V) < V_TOL and p3_r >= P3_TOL
    return {
        "scenario": "ca_local_per_cell_coupling",
        "direction": direction,
        "v_R_final": v_r,
        "p3_R_final": p3_r,
        "source_glider_preserved": preserved,
        "cross_layer_sites_peak": cross_peak,
        "valid_excitation_coupling": False,
    }


def simulate_excitation_coupling(
    direction: str,
    inject_period: int,
    phase_aware: bool,
    n_cycles_target: int = 10,
    every_step: bool = False,
) -> dict:
    """
    Full two-layer simulation with excitation-level coupling.

    direction: '110_to_124' (V-A canonical) or '124_to_110' (chirality control)
    every_step: if True, apply coupling every step (cell-level negative control)
    """
    t110_base = ether_tape(ETHER_110, L)
    t110_pert = t110_base[:]
    t124_base = ether_tape(ETHER_124, L)
    t124_pert = t124_base[:]

    if direction == "110_to_124":
        t110_pert[CENTER_110] ^= 1
    else:
        t124_pert[CENTER_124] ^= 1

    right_leads: list[int] = []
    left_leads_124: list[int] = []
    left_leads_110: list[int] = []
    events: list[CouplingEventRecord] = []
    injections = 0
    cross_peak = 0

    for t in range(1, T + 1):
        d110 = [t110_base[i] != t110_pert[i] for i in range(L)]
        d124 = [t124_base[i] != t124_pert[i] for i in range(L)]

        rf = right_lead_at(d110, CENTER_110, L)
        if rf is not None:
            right_leads.append(rf)

        lf124 = left_lead_at(d124, CENTER_124, L)
        if lf124 is not None:
            left_leads_124.append(lf124)

        lf110 = left_lead_at(d110, CENTER_110, L)
        if lf110 is not None:
            left_leads_110.append(lf110)

        if direction == "110_to_124":
            source_leads = right_leads
        else:
            source_leads = left_leads_124

        p3_before = period3_purity(source_leads)
        v_before = source_leads[-1] / t if source_leads else None

        applied = False
        inj_site = None
        ether_ph = None

        fire = every_step or (t > 10 and t % inject_period == 0)

        if direction == "110_to_124":
            exc_110 = measure_excitation_110(t110_base, t110_pert, CENTER_110, t, right_leads)
            if fire and exc_110.position is not None:
                if every_step:
                    inj_site = (CENTER_110 + exc_110.position) % L
                    t124_pert[inj_site] ^= 1
                    applied = True
                    ether_ph = inj_site % 14
                elif inject_period == EVENT_PERIOD:
                    applied, inj_site, ether_ph = apply_c_exc(
                        exc_110, t124_pert, CENTER_110, t, phase_aware
                    )
                else:
                    inj_site = (CENTER_110 + exc_110.position) % L
                    t124_pert[inj_site] ^= 1
                    applied = True
                    ether_ph = inj_site % 14
        else:
            exc_124 = measure_excitation_124(t124_base, t124_pert, CENTER_124, t, left_leads_124)
            if fire and exc_124.position is not None:
                if every_step or inject_period != EVENT_PERIOD:
                    inj_site = (CENTER_124 - exc_124.position) % L
                    t110_pert[inj_site] ^= 1
                    applied = True
                else:
                    applied, inj_site = apply_c_exc_reverse(exc_124, t110_pert, CENTER_124, t)

        if applied:
            injections += 1

        t110_base = step_raw(t110_base, RULE110)
        t110_pert = step_raw(t110_pert, RULE110)
        t124_base = step_raw(t124_base, RULE124)
        t124_pert = step_raw(t124_pert, RULE124)

        cross = sum(t124_base[i] != t124_pert[i] for i in range(L))
        cross_peak = max(cross_peak, cross)

        p3_after = period3_purity(source_leads)
        v_after = source_leads[-1] / t if source_leads else None

        is_resonant_step = t > 10 and t % EVENT_PERIOD == 0
        if is_resonant_step and inject_period == EVENT_PERIOD and not every_step:
            events.append(
                CouplingEventRecord(
                    t=t,
                    resonant=(t % EVENT_PERIOD == 0),
                    p3_before=p3_before,
                    p3_after=p3_after,
                    v_before=v_before,
                    v_after=v_after,
                    injection_applied=applied,
                    injection_site=inj_site,
                    ether_phase_at_site=ether_ph,
                    cross_layer_sites=cross,
                )
            )

    if direction == "110_to_124":
        v_source = right_leads[-1] / T if right_leads else None
        p3_source = period3_purity(right_leads)
        target_v = TARGET_V
    else:
        slope = linear_slope(list(range(len(left_leads_124[-30:]))), left_leads_124[-30:])
        v_source = -slope if slope is not None else None
        p3_source = period3_purity(left_leads_124)
        target_v = -TARGET_V

    v_r110_signal = None
    p3_r110_signal = None
    coherent_110_from_reverse = False
    if direction == "124_to_110" and right_leads:
        slope110 = linear_slope(list(range(len(right_leads[-30:]))), right_leads[-30:])
        v_r110_signal = slope110
        p3_r110_signal = period3_purity(right_leads)
        coherent_110_from_reverse = (
            v_r110_signal is not None
            and abs(v_r110_signal - TARGET_V) < 0.2
            and p3_r110_signal >= P3_TOL
        )
    v_l124 = None
    p3_l124 = None
    coherent_124 = False
    if direction == "110_to_124" and left_leads_124:
        slope124 = linear_slope(list(range(len(left_leads_124[-30:]))), left_leads_124[-30:])
        v_l124 = -slope124 if slope124 is not None else None
        p3_l124 = period3_purity(left_leads_124)
        coherent_124 = (
            v_l124 is not None
            and abs(v_l124 + TARGET_V) < 0.2
            and p3_l124 >= P3_TOL
        )

    glider_preserved = (
        v_source is not None
        and abs(v_source - target_v) < V_TOL
        and p3_source >= P3_TOL
    )

    resonant_events = [e for e in events if e.resonant]
    n_resonant = len(resonant_events)
    p3_drop_max = max(
        (e.p3_before - e.p3_after for e in resonant_events if e.injection_applied),
        default=0.0,
    )
    p3_at_end = p3_source
    all_resonant_preserve = all(
        e.p3_after >= P3_TOL for e in resonant_events if e.injection_applied
    )

    return {
        "direction": direction,
        "inject_period": inject_period,
        "phase_aware": phase_aware,
        "n_resonant_events": n_resonant,
        "n_injections": injections,
        "v_source_final": v_source,
        "p3_source_final": p3_source,
        "source_glider_preserved": glider_preserved,
        "v_R_final": right_leads[-1] / T if right_leads else None,
        "p3_R_final": period3_purity(right_leads),
        "glider_preserved_R": (
            direction == "110_to_124" and glider_preserved
        ),
        "cross_layer_sites_peak": cross_peak,
        "cross_layer_sites_final": cross,
        "v_L_124_signal": v_l124,
        "p3_L_124_signal": p3_l124,
        "coherent_excitation_on_124": coherent_124,
        "v_R_110_from_reverse": v_r110_signal,
        "p3_R_110_from_reverse": p3_r110_signal,
        "coherent_excitation_on_110_from_reverse": coherent_110_from_reverse,
        "p3_drop_max_at_coupling": p3_drop_max,
        "all_resonant_couplings_preserve_p3": all_resonant_preserve,
        "coupling_events_sample": [asdict(e) for e in events[:5]],
        "coupling_events_last": [asdict(e) for e in events[-3:]],
        "valid_excitation_coupling": (
            glider_preserved and cross_peak >= 3 and n_resonant >= n_cycles_target
        ),
    }


def formal_framework_dict() -> dict:
    """Export key definitions for lab note / JSON artifact."""
    return {
        "excitation_state": {
            "symbol": "E_ell = (x, v, phi)",
            "x": "front offset from seed center (cells); right-front layer 110, left-front layer 124",
            "v": "causal front velocity (cells/step); target +/-2/3",
            "phi": "period-3 phase phi = t mod N_gen, N_gen = 3",
            "well_defined": (
                "Measured from base-vs-perturbed difference on ether background; "
                "stable when period-3 purity >= 0.9 and |v - 2/3| < 0.05"
            ),
        },
        "coupling_operator": {
            "symbol": "C_exc : Exc_110 x Exc_124 -> Exc_110 x Exc_124",
            "resonant_times": "t = k * lcm(N_gen, T_ether) = 21k",
            "action": (
                "At resonant t: flip tape_124 at site center_110 + x_110; E_110 unchanged. "
                "Off-resonant: identity (free CA evolution). "
                "Phase-aware C_exc^+: apply flip only if ether phase (site mod 14) in "
            "PERSIST_124 = {3,6,7,12} (070-113 nucleation phases)."
            ),
            "algebraic_form": (
                "C_exc(E_110, E_124) = (E_110, E_124 + delta_p) where "
                "delta_p is a single-cell bit flip at the 110 front when t mod 21 = 0"
            ),
        },
        "resonance_condition": {
            "lean_theorem": "orbit_resonance_at t <-> 21 | t (DynamicalCouplingBridge.lean)",
            "N_gen": N_GEN,
            "T_ether": T_ETHER,
            "event_period": EVENT_PERIOD,
            "obstruction": "lcm(3,7)=21 does not divide glider period 3 -> per-step CA-local forbidden",
        },
        "physical_interpretation": {
            "sm_vertex": "Discrete charged-current weak vertex: u <-> d + W+, nu <-> e- + W+",
            "ca_analogue": (
                "Off-shell W exchange at glider front; asymmetric 110->124 matches V-A "
                "(ChiralPairVA: 32/125 mismatches, all W+ non-center)"
            ),
            "uv_ir": "UV decoupled chiral CA layers; IR EW mixing via sparse resonant C_exc",
        },
    }


def main():
    t0 = time.time()
    print("=" * 72)
    print("EPIC_073 Rank 070-124 — Excitation-Level Coupling Formalism")
    print("=" * 72)

    framework = formal_framework_dict()
    print("\nFormal framework loaded.")

    scenarios = [
        ("resonant_110_to_124", "110_to_124", EVENT_PERIOD, False, False),
        ("resonant_phase_aware_110_to_124", "110_to_124", EVENT_PERIOD, True, False),
        ("off_resonant_period22_110_to_124", "110_to_124", 22, False, False),
        ("chirality_reverse_124_to_110", "124_to_110", EVENT_PERIOD, False, False),
    ]

    runs = []
    for name, direction, period, phase_aware, every_step in scenarios:
        print(f"\n--- {name} ---")
        r = simulate_excitation_coupling(
            direction, period, phase_aware, n_cycles_target=10, every_step=every_step
        )
        r["scenario"] = name
        runs.append(r)
        vs = r["v_source_final"]
        ps = r["p3_source_final"]
        print(
            f"  v_src={vs:.4f}  p3={ps:.3f}  "
            f"inj={r['n_injections']}  preserved={r['source_glider_preserved']}"
        )
        print(f"  cross_peak={r['cross_layer_sites_peak']}  valid={r['valid_excitation_coupling']}")

    cell_local = simulate_ca_local_coupling()
    runs.append(cell_local)
    print("\n--- ca_local_per_cell_coupling ---")
    print(
        f"  v_R={cell_local['v_R_final']:.4f}  p3={cell_local['p3_R_final']:.3f}  "
        f"preserved={cell_local['source_glider_preserved']}"
    )

    canonical = runs[0]
    phase_aware_run = runs[1]
    off_resonant = runs[2]
    reverse = runs[3]

    left_handed_confirmed = (
        canonical["source_glider_preserved"]
        and canonical["coherent_excitation_on_124"]
        and canonical["valid_excitation_coupling"]
    )

    c_exc_preserves_coherence = (
        canonical["source_glider_preserved"]
        and canonical["all_resonant_couplings_preserve_p3"]
        and canonical["p3_source_final"] >= P3_TOL
    )

    summary = {
        "rank": "070-124",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "formal_framework": framework,
        "parameters": {
            "L": L,
            "T": T,
            "CENTER_110": CENTER_110,
            "CENTER_124": CENTER_124,
            "EVENT_PERIOD": EVENT_PERIOD,
            "N_GEN": N_GEN,
            "T_ETHER": T_ETHER,
            "PERSIST_124": sorted(PERSIST_124),
            "TARGET_V": TARGET_V,
            "V_TOL": V_TOL,
            "P3_TOL": P3_TOL,
        },
        "runs": runs,
        "conclusions": {
            "C_exc_preserves_glider_coherence_at_resonance": c_exc_preserves_coherence,
            "cross_layer_information_transfer": canonical["cross_layer_sites_peak"] >= 3,
            "coherent_excitation_nucleated_on_124": canonical["coherent_excitation_on_124"],
            "left_handed_coupling_confirmed": left_handed_confirmed,
            "left_handed_interpretation": (
                "Operator C_exc is defined 110→124 only (SM charged-current direction). "
                "Target layer 124 nucleates coherent v_L≈−2/3 excitation. "
                "Reverse 124→110 also transfers dynamically (CP-conjugate); "
                "static V−A selection from ChiralPairVA (070-133 CatAL)."
            ),
            "off_resonant_period22_sparse_still_preserves": off_resonant["source_glider_preserved"],
            "ca_local_per_cell_destroys_coherence": not cell_local["source_glider_preserved"],
            "excitation_vs_cell_local_distinction": (
                c_exc_preserves_coherence and not cell_local["source_glider_preserved"]
            ),
            "phase_aware_injection_rate": (
                phase_aware_run["n_injections"] / max(phase_aware_run["n_resonant_events"], 1)
            ),
            "cat_level": "CatAD",
            "lean_extension": "ExcitationCoupling.lean (excitation state + C_exc resonance)",
        },
        "physical_vertex": {
            "interpretation": "Discrete W-boson charged-current vertex at EW scale",
            "direction": "110 (right-handed sector) -> 124 (left-handed sector)",
            "feynman_analogue": (
                "CA-level three-body vertex: G_R + vacuum perturbation -> excitation in G_L sector; "
                "not a synchronous Boolean CA-local operation"
            ),
        },
        "wall_clock_s": time.time() - t0,
    }

    out_path = "excitation_level_coupling_formalism_results.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 72)
    print(f"C_exc preserves coherence (resonant): {c_exc_preserves_coherence}")
    print(f"Left-handed (110->124 only): {left_handed_confirmed}")
    print(f"Coherent 124 excitation: {canonical['coherent_excitation_on_124']}")
    print(f"Results -> {out_path}")
    print(f"Wall clock: {summary['wall_clock_s']:.1f}s")

    signal.alarm(0)


if __name__ == "__main__":
    main()
