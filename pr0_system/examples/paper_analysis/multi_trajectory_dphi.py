"""
multi_trajectory_dphi.py — COMP-P11-B (v2, corrected)
Multi-trajectory D–Φ_proxy correlation for Paper 11

Extends the canonical compare_dissonance_and_phi.py EXACTLY:
- Same dynamics: use_confinement=True
- Same sampling: stride 250, t=0..5000, n=21 points
- Same Φ_proxy formula: max(0, H_parts - H_whole + 0.1*std(chi))
- Same history buffer: deque(maxlen=20), appended inside evolution loop

Varies ONLY initial soliton positions (x0_q, x0_aq) and amplitude,
keeping all dynamics parameters identical to the canonical run.

11 configurations:
  - Config 0: canonical (x0_q=24, x0_aq=40, amp=3.0) → should give r≈-0.91
  - Configs 1-10: systematic variation of separation and amplitude

Output: multi_trajectory_dphi_results.json (SHA-256 in PROVENANCE.md)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../animations'))

import json, hashlib, statistics, time
import numpy as np
from pr0_emergent_qcd import EmergentQCD
from pr0_sds_dissonance_bootstrap import compute_ontological_dissonance
from collections import deque


def entropy_of_field(field):
    """Exact copy from compare_dissonance_and_phi.py."""
    hist, _ = np.histogram(field.flatten(), bins=20, density=True)
    hist = hist + 1e-10
    hist = hist / np.sum(hist)
    return -np.sum(hist * np.log2(hist))


def compute_phi_proxy(psi, chi):
    """Exact copy of compute_integrated_information_simple."""
    dens = np.abs(psi)**2
    L_y, L_x = psi.shape
    q1 = dens[:L_y//2, :L_x//2]
    q2 = dens[:L_y//2, L_x//2:]
    q3 = dens[L_y//2:, :L_x//2]
    q4 = dens[L_y//2:, L_x//2:]
    H_whole = entropy_of_field(dens)
    H_parts = (entropy_of_field(q1) + entropy_of_field(q2) +
               entropy_of_field(q3) + entropy_of_field(q4))
    phi = H_parts - H_whole
    phi_chi = np.std(chi)
    return max(0.0, phi + 0.1 * phi_chi)


def run_one_trajectory(x0_q, x0_aq, amplitude, label):
    """
    Run exactly like compare_dissonance_and_phi.py.
    Varies only soliton initial positions and amplitude.
    """
    qcd = EmergentQCD(L_x=64, L_y=64, use_confinement=True)
    qcd.set_soliton(x0=x0_q,  y0=32, amplitude=amplitude, width=3.0,
                    velocity_x=0.1,  charge=+1)
    qcd.set_soliton(x0=x0_aq, y0=32, amplitude=amplitude, width=3.0,
                    velocity_x=-0.1, charge=-1)

    history = deque(maxlen=20)
    D_values = []
    phi_values = []
    seps = []

    for t in range(0, 5001, 250):
        D   = compute_ontological_dissonance(qcd.psi, qcd.chi, list(history))
        phi = compute_phi_proxy(qcd.psi, qcd.chi)
        sep = qcd.measure_separation()

        D_values.append(float(D))
        phi_values.append(float(phi))
        if sep is not None:
            seps.append(float(sep))

        if t < 5000:
            for _ in range(250):
                qcd.step(dt=0.01)
                history.append(qcd.psi.copy())

    if len(D_values) < 5 or np.std(D_values) < 1e-10 or np.std(phi_values) < 1e-10:
        return None

    r = float(np.corrcoef(D_values, phi_values)[0, 1])
    bound_pct = sum(1 for s in seps if s < 25) / max(len(seps), 1)

    return {
        "label":     label,
        "x0_q":      x0_q,
        "x0_aq":     x0_aq,
        "amplitude": amplitude,
        "separation_initial": float(x0_aq - x0_q),
        "r":         r,
        "n_samples": len(D_values),
        "D_range":   [float(min(D_values)), float(max(D_values))],
        "phi_range": [float(min(phi_values)), float(max(phi_values))],
        "bound_fraction": float(bound_pct),
    }


# Configuration table: (x0_q, x0_aq, amplitude, label)
# Canonical separation = 40-24 = 16 units, amplitude = 3.0
CONFIGS = [
    (24, 40, 3.0, "canonical"),          # sep=16, canonical
    (22, 42, 3.0, "sep_20"),             # sep=20, slightly wider
    (20, 44, 3.0, "sep_24"),             # sep=24
    (18, 46, 3.0, "sep_28"),             # sep=28
    (26, 38, 3.0, "sep_12"),             # sep=12, closer
    (28, 36, 3.0, "sep_8"),              # sep=8, tight
    (24, 40, 2.5, "canonical_amp2.5"),   # lower amplitude
    (24, 40, 2.0, "canonical_amp2.0"),   # lower amplitude
    (24, 40, 3.5, "canonical_amp3.5"),   # higher amplitude
    (24, 40, 4.0, "canonical_amp4.0"),   # higher amplitude
    (22, 42, 2.5, "sep_20_amp2.5"),      # combined variation
]

print("=" * 65)
print("COMP-P11-B (v2): Multi-trajectory D–Φ_proxy study")
print("All configs use use_confinement=True, same dynamics as canonical")
print(f"Configs: {len(CONFIGS)} | Stride: 250 | Steps: 5000 | n=21 per run")
print("=" * 65)

t_start = time.time()
results = []
for i, (xq, xaq, amp, label) in enumerate(CONFIGS):
    print(f"\n[{i+1}/{len(CONFIGS)}] {label}: x_q={xq}, x_aq={xaq}, sep={xaq-xq}, amp={amp}",
          flush=True)
    res = run_one_trajectory(xq, xaq, amp, label)
    if res is not None:
        print(f"  r = {res['r']:.4f}  (bound_frac={res['bound_fraction']:.2f})")
        results.append(res)
    else:
        print("  SKIPPED (zero variance or degenerate)")

elapsed = time.time() - t_start
valid_r = [r["r"] for r in results]
canonical_r = next((r["r"] for r in results if r["label"] == "canonical"), None)

print(f"\n{'='*65}")
print(f"SUMMARY ({elapsed:.1f}s)")
print(f"{'='*65}")
print(f"  N valid trajectories: {len(valid_r)}")
print(f"  Canonical r:          {canonical_r:.4f}  (expected ≈ -0.91)")
print(f"  r values:             {[f'{r:.3f}' for r in valid_r]}")
print(f"  mean r = {statistics.mean(valid_r):.4f}")
print(f"  std  r = {statistics.stdev(valid_r):.4f}" if len(valid_r) > 1 else "")
print(f"  min  r = {min(valid_r):.4f}")
print(f"  max  r = {max(valid_r):.4f}")
print(f"  N with r < -0.7:      {sum(1 for r in valid_r if r < -0.7)}")
print(f"  N with r < 0:         {sum(1 for r in valid_r if r < 0)}")
print(f"  N with r > 0:         {sum(1 for r in valid_r if r > 0)}")

output = {
    "description": "COMP-P11-B (v2): Multi-trajectory D–Φ_proxy correlation (corrected)",
    "method": (
        "Exact copy of compare_dissonance_and_phi.py dynamics: "
        "use_confinement=True, stride=250, t=0..5000, n=21 samples, "
        "same Φ_proxy formula (max(0, H_parts-H_whole+0.1*std(chi))), "
        "same history buffer (deque(maxlen=20), appended per step). "
        "Varies ONLY initial soliton positions and amplitude."
    ),
    "n_configs": len(CONFIGS),
    "n_valid":   len(valid_r),
    "canonical_r": float(canonical_r) if canonical_r is not None else None,
    "mean_r":  float(statistics.mean(valid_r)),
    "std_r":   float(statistics.stdev(valid_r)) if len(valid_r) > 1 else 0.0,
    "min_r":   float(min(valid_r)),
    "max_r":   float(max(valid_r)),
    "n_negative": int(sum(1 for r in valid_r if r < 0)),
    "n_strong_negative": int(sum(1 for r in valid_r if r < -0.7)),
    "elapsed_seconds": float(elapsed),
    "configs": results,
}

sha = hashlib.sha256(
    json.dumps(output, sort_keys=True, default=float).encode()
).hexdigest()
output["sha256"] = sha

out_path = os.path.join(os.path.dirname(__file__), "multi_trajectory_dphi_results.json")
with open(out_path, "w") as f:
    json.dump(output, f, indent=2, default=float)
print(f"\nSaved: {out_path}")
print(f"SHA-256: {sha}")
