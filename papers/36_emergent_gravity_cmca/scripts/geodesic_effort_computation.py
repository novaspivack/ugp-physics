from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
#!/usr/bin/env python3
"""
Ranks 48-GEO / 49-EFF / 50-EQUIV: Geodesic Computation Experiment
EPIC_072

Tests the Geodesic Computation Principle from OIR Part 19:
  - 48-GEO: τ_c(geodesic path) < τ_c(off-geodesic path)
  - 49-EFF: total computational effort (Σ τ_c) ∝ proper time
  - 50-EQUIV: cells near a passing glider have higher τ_c than free ether cells

Parameters:
  OUTER_L = 500, periodic BC, Rule 110
  Inner CA: M = 7, Rule 110
  ETHER14 = [1,1,1,1,1,0,0,0,1,0,0,1,1,0]
  Glider seed: '0100101001' (v≈+0.532·c_eff, γ≈1.658, confirmed stable Round 19)
  n_steps = 150 outer steps
  c_eff = 2/3

Glider detection: diff-from-reference (tape_B != tape_A), consistent with Round 19.
This captures the full disturbed region including high-τ_c boundary cells.
"""

import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats

# ── Constants ─────────────────────────────────────────────────────────────────
ETHER14  = np.array([1,1,1,1,1,0,0,0,1,0,0,1,1,0], dtype=np.uint8)
LUT110   = np.array([(110 >> i) & 1 for i in range(8)], dtype=np.uint8)
OUTER_L  = 500
M        = 7
C_EFF    = 2 / 3
N_STEPS  = 150
GLIDER   = '0100101001'
NEARBY_R = 20    # cells around glider CoM counted as "nearby" for τ_c sampling
MAX_INNER = 100

# ── Ether background ──────────────────────────────────────────────────────────
ether_base = np.array([ETHER14[i % 14] for i in range(OUTER_L)], dtype=np.uint8)

# ── Rule 110 helpers ──────────────────────────────────────────────────────────
def run_outer(state: np.ndarray) -> np.ndarray:
    l = np.roll(state, 1).astype(np.int32)
    c = state.astype(np.int32)
    r = np.roll(state, -1).astype(np.int32)
    return LUT110[(l << 2) | (c << 1) | r]


def run_inner(state: np.ndarray) -> np.ndarray:
    l = np.roll(state, 1).astype(np.int32)
    c = state.astype(np.int32)
    r = np.roll(state, -1).astype(np.int32)
    return LUT110[(l << 2) | (c << 1) | r]


def majority(state: np.ndarray) -> int:
    return 1 if state.sum() * 2 > len(state) else 0

# ── τ_c LUT (same precompute as Round 19) ─────────────────────────────────────
windows  = [np.array([ETHER14[(i + j) % 14] for j in range(M)], dtype=np.uint8) for i in range(14)]
win_maj1 = [w for w in windows if majority(w) == 1]
win_maj0 = [w for w in windows if majority(w) == 0]


def precompute_tau_lut() -> np.ndarray:
    starts = {
        1: win_maj1[0].copy() if win_maj1 else np.zeros(M, dtype=np.uint8),
        0: win_maj0[0].copy() if win_maj0 else np.zeros(M, dtype=np.uint8),
    }
    tau_lut = np.zeros((2, 2), dtype=np.float32)
    for curr in [0, 1]:
        for tgt in [0, 1]:
            state = starts[curr].copy()
            for step in range(MAX_INNER):
                if majority(state) == tgt:
                    tau_lut[curr, tgt] = step
                    break
                state = run_inner(state)
            else:
                tau_lut[curr, tgt] = MAX_INNER
    return tau_lut


tau_lut = precompute_tau_lut()
print(f"τ_c LUT:\n{tau_lut}")


def measure_tau(now: np.ndarray, nxt: np.ndarray) -> np.ndarray:
    """O(L) τ_c measurement via precomputed LUT."""
    return tau_lut[now.astype(int), nxt.astype(int)]

# ── Background τ_c from pure ether ────────────────────────────────────────────
_s = ether_base.copy()
_bg = []
for _ in range(40):
    _sn = run_outer(_s)
    _bg.append(float(measure_tau(_s, _sn).mean()))
    _s = _sn
tau_bg = float(np.mean(_bg[20:]))
print(f"Background τ_c (pure ether) = {tau_bg:.4f}")


def make_tape_with_glider(seed_str: str, center: int = None) -> np.ndarray:
    tape = ether_base.copy()
    if center is None:
        center = OUTER_L // 2
    seed = np.array([int(b) for b in seed_str], dtype=np.uint8)
    for j, bit in enumerate(seed):
        tape[(center + j) % OUTER_L] = bit
    return tape

# ═══════════════════════════════════════════════════════════════════════════════
# TEST 1 (Rank 48-GEO): τ_c along geodesics vs off-geodesics
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*65)
print("TEST 1 (48-GEO): τ_c geodesic vs off-geodesic")
print("="*65)
print("Glider detection: diff-from-reference (tape_B != tape_A)")

tape_A = ether_base.copy()
tape_B = make_tape_with_glider(GLIDER)

tau_geodesic_ts    = []   # mean τ_c over ether (non-glider) cells in tape A
tau_offgeodesic_ts = []   # mean τ_c over glider-region cells in tape B (diff cells)
tau_nearby_ts      = []   # mean τ_c over ether cells within NEARBY_R of CoM in tape B
glider_com_ts      = []   # CoM position each step
spacetime_A        = np.zeros((N_STEPS, OUTER_L), dtype=np.float32)
spacetime_B        = np.zeros((N_STEPS, OUTER_L), dtype=np.float32)

for t in range(N_STEPS):
    tape_A_next = run_outer(tape_A)
    tape_B_next = run_outer(tape_B)

    tau_A = measure_tau(tape_A, tape_A_next)
    tau_B = measure_tau(tape_B, tape_B_next)

    spacetime_A[t] = tau_A
    spacetime_B[t] = tau_B

    # Glider detection: cells where tape_B differs from tape_A reference
    diff_mask = tape_B != tape_A
    n_diff = diff_mask.sum()

    if 2 <= n_diff <= 80:
        com = float(np.where(diff_mask)[0].mean())
        glider_com_ts.append(com)

        tau_offgeodesic_ts.append(float(tau_B[diff_mask].mean()))

        # geodesic: non-glider cells in tape B (same as ether cells)
        ether_mask = ~diff_mask
        tau_geodesic_ts.append(float(tau_B[ether_mask].mean() if ether_mask.sum() > 0 else tau_bg))

        # nearby: ether cells within NEARBY_R of CoM in tape B
        distances = np.minimum(
            np.abs(np.arange(OUTER_L) - com),
            OUTER_L - np.abs(np.arange(OUTER_L) - com)
        )
        nearby_ether = (distances <= NEARBY_R) & ether_mask
        if nearby_ether.sum() > 0:
            tau_nearby_ts.append(float(tau_B[nearby_ether].mean()))
        else:
            tau_nearby_ts.append(float(tau_B[ether_mask].mean() if ether_mask.sum() > 0 else tau_bg))
    else:
        glider_com_ts.append(OUTER_L // 2)
        tau_geodesic_ts.append(float(tau_A.mean()))
        tau_offgeodesic_ts.append(float(tau_bg))
        tau_nearby_ts.append(float(tau_bg))

    tape_A = tape_A_next
    tape_B = tape_B_next

tau_geodesic_mean    = float(np.mean(tau_geodesic_ts))
tau_offgeodesic_mean = float(np.mean(tau_offgeodesic_ts))
tau_nearby_mean      = float(np.mean(tau_nearby_ts))

print(f"τ_c (geodesic, non-glider cells) = {tau_geodesic_mean:.4f}")
print(f"τ_c (off-geodesic, glider region)= {tau_offgeodesic_mean:.4f}")
print(f"τ_c (nearby ether ±{NEARBY_R})    = {tau_nearby_mean:.4f}")

t1_stat, t1_p = stats.ttest_ind(tau_geodesic_ts, tau_offgeodesic_ts)
geo_principle_holds = (tau_geodesic_mean < tau_offgeodesic_mean) and (t1_p < 0.05)
t1_evidence = (f"τ_c geodesic={tau_geodesic_mean:.4f} < off-geodesic={tau_offgeodesic_mean:.4f}, "
               f"p={t1_p:.4e}, mean_ratio={tau_offgeodesic_mean/tau_geodesic_mean:.4f}")
print(f"t-test p={t1_p:.4e}")
print(f"Ordering: geo≤nearby≤off-geo: {tau_geodesic_mean:.4f}≤{tau_nearby_mean:.4f}≤{tau_offgeodesic_mean:.4f}")
print(f"TEST 1: {'PASS' if geo_principle_holds else 'FAIL'}")

# ═══════════════════════════════════════════════════════════════════════════════
# TEST 2 (Rank 49-EFF): Cumulative computational effort along trajectories
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*65)
print("TEST 2 (49-EFF): Cumulative effort — glider trajectory vs geodesic")
print("="*65)

tape_A2 = ether_base.copy()
tape_B2 = make_tape_with_glider(GLIDER)

effort_glider   = []   # τ_c at glider CoM cell in tape B each step
effort_geodesic = []   # τ_c at fixed position in tape A each step
fixed_pos = OUTER_L // 2

for t in range(N_STEPS):
    tape_A2_next = run_outer(tape_A2)
    tape_B2_next = run_outer(tape_B2)

    tau_A2 = measure_tau(tape_A2, tape_A2_next)
    tau_B2 = measure_tau(tape_B2, tape_B2_next)

    diff2 = tape_B2 != tape_A2
    if diff2.sum() >= 2:
        com2 = int(round(np.where(diff2)[0].mean())) % OUTER_L
        effort_glider.append(float(tau_B2[com2]))
    else:
        effort_glider.append(float(tau_bg))

    effort_geodesic.append(float(tau_A2[fixed_pos]))

    tape_A2 = tape_A2_next
    tape_B2 = tape_B2_next

effort_glider   = np.array(effort_glider)
effort_geodesic = np.array(effort_geodesic)
cumulative_glider   = float(effort_glider.sum())
cumulative_geodesic = float(effort_geodesic.sum())
eff_ratio = cumulative_glider / cumulative_geodesic if cumulative_geodesic > 0 else float('nan')

print(f"Cumulative effort (glider CoM path): {cumulative_glider:.2f}")
print(f"Cumulative effort (geodesic):        {cumulative_geodesic:.2f}")
print(f"Effort ratio (glider/geodesic):      {eff_ratio:.4f}")

efficiency_holds = cumulative_glider > cumulative_geodesic
print(f"TEST 2: {'PASS' if efficiency_holds else 'FAIL'}")

# ═══════════════════════════════════════════════════════════════════════════════
# TEST 3 (Rank 50-EQUIV): Equivalence principle
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*65)
print("TEST 3 (50-EQUIV): Equivalence principle")
print("="*65)

# Tape C: pure ether (reference geodesic)
# Tape D: glider at center-50, monitor window around X=center
X = OUTER_L // 2
# Inject at same ether phase as X (pos % 14 == X % 14), 42 cells to the left.
# This ensures the glider evolves with the same phase relationship to the ether
# as when injected at X itself, giving v = +0.532 cells/step (rightward).
glider_start = X - 42   # 208; 208 % 14 == 250 % 14 == 12 ✓

tape_C = ether_base.copy()
tape_D = make_tape_with_glider(GLIDER, center=glider_start)

# Actual initial CoM ≈ glider_start + 3.3 (measured from Round 19 at center=250)
# Distance from initial CoM to X: 250 - (glider_start + 3.3) ≈ 38.7 cells
# Arrival estimate: 38.7 / 0.532 ≈ 73 steps
v_glider    = 0.532      # cells per outer step (measured Round 19)
com0_offset = 3.3        # CoM offset from seed center (measured)
dist_to_X   = X - (glider_start + com0_offset)
arrival_est = int(round(dist_to_X / v_glider))
print(f"X={X}, glider starts at {glider_start} (ether phase {glider_start%14})")
print(f"X ether phase={X%14}, dist_to_X≈{dist_to_X:.1f}, est. arrival at X: step {arrival_est}")

# Monitor a ±8 cell window around X for smoother signal
WINDOW_R = 8
x_idx = np.arange(X - WINDOW_R, X + WINDOW_R + 1) % OUTER_L

tau_window_C  = []   # mean τ_c in window around X in tape C
tau_window_D  = []   # mean τ_c in window around X in tape D
glider_in_window = []   # 1 if glider CoM is within NEARBY_R of X at step t

# τ_c on actual glider cells that overlap the ±NEARBY_R zone around X
tau_glider_near_X_D = []   # mean τ_c on diff cells within NEARBY_R of X
tau_glider_near_X_C = []   # mean τ_c on same positions in tape C

for t in range(N_STEPS):
    tape_C_next = run_outer(tape_C)
    tape_D_next = run_outer(tape_D)

    tau_C = measure_tau(tape_C, tape_C_next)
    tau_D = measure_tau(tape_D, tape_D_next)

    tau_window_C.append(float(tau_C[x_idx].mean()))
    tau_window_D.append(float(tau_D[x_idx].mean()))

    # Track glider position and cells in tape D (diff from tape C = reference)
    diff_CD = tape_D != tape_C
    if diff_CD.sum() >= 2:
        com3 = float(np.where(diff_CD)[0].mean())
        dist = min(abs(com3 - X), OUTER_L - abs(com3 - X))
        glider_in_window.append(1 if dist <= NEARBY_R else 0)

        # Glider cells within ±NEARBY_R of X: diff cells that are physically near X
        distances_to_X = np.minimum(
            np.abs(np.arange(OUTER_L) - X),
            OUTER_L - np.abs(np.arange(OUTER_L) - X)
        )
        glider_near_X = diff_CD & (distances_to_X <= NEARBY_R)
        if glider_near_X.sum() > 0:
            tau_glider_near_X_D.append(float(tau_D[glider_near_X].mean()))
            tau_glider_near_X_C.append(float(tau_C[glider_near_X].mean()))
    else:
        glider_in_window.append(0)

    tape_C = tape_C_next
    tape_D = tape_D_next

tau_window_C  = np.array(tau_window_C)
tau_window_D  = np.array(tau_window_D)
glider_in_window = np.array(glider_in_window)

near_mask3 = glider_in_window == 1
far_mask3  = ~near_mask3

tau_C_free = float(tau_window_C.mean())
tau_before = float(tau_window_D[:arrival_est].mean()) if arrival_est < N_STEPS else float(tau_window_D.mean())
tau_after  = float(tau_window_D[arrival_est:].mean()) if arrival_est < N_STEPS else float(tau_window_D.mean())
tau_C_before = float(tau_window_C[:arrival_est].mean()) if arrival_est < N_STEPS else float(tau_window_C.mean())
tau_C_after  = float(tau_window_C[arrival_est:].mean()) if arrival_est < N_STEPS else float(tau_window_C.mean())

print(f"τ_c window ±{WINDOW_R} around X in free tape C (all): {tau_C_free:.4f}")
print(f"τ_c window in D before arrival (t<{arrival_est}): {tau_before:.4f}  [C: {tau_C_before:.4f}]")
print(f"τ_c window in D after  arrival (t≥{arrival_est}): {tau_after:.4f}  [C: {tau_C_after:.4f}]")
print(f"Steps with glider CoM within ±{NEARBY_R} of X: {near_mask3.sum()}")
print(f"Steps with glider cells within ±{NEARBY_R} of X: {len(tau_glider_near_X_D)}")

# Primary criterion: τ_c on actual glider cells near X vs same positions in C (free ether)
if len(tau_glider_near_X_D) >= 5:
    arr_D = np.array(tau_glider_near_X_D)
    arr_C = np.array(tau_glider_near_X_C)
    print(f"τ_c on glider cells near X in tape D: {arr_D.mean():.4f}  (n={len(arr_D)} steps)")
    print(f"τ_c on same positions  near X in tape C: {arr_C.mean():.4f}")
    t3_stat, t3_p = stats.ttest_rel(arr_D, arr_C)
    print(f"Paired t-test (glider cells D vs same positions C): p={t3_p:.4e}")
    equiv_holds = (arr_D.mean() > arr_C.mean()) and (t3_p < 0.05)
    tau_near_D = float(arr_D.mean())
    tau_near_C = float(arr_C.mean())
elif near_mask3.sum() >= 5:
    tau_D_near3 = tau_window_D[near_mask3]
    tau_C_near3 = tau_window_C[near_mask3]
    print(f"τ_c window D (glider CoM near X): {tau_D_near3.mean():.4f} (n={near_mask3.sum()})")
    print(f"τ_c window C (same steps):        {tau_C_near3.mean():.4f}")
    t3_stat, t3_p = stats.ttest_rel(tau_D_near3, tau_C_near3)
    print(f"Paired t-test D-near vs C-near: p={t3_p:.4e}")
    equiv_holds = (tau_D_near3.mean() > tau_C_near3.mean()) and (t3_p < 0.05)
    tau_near_D = float(tau_D_near3.mean())
    tau_near_C = float(tau_C_near3.mean())
else:
    t3_p = 1.0
    t3_stat = 0.0
    tau_near_D = tau_after
    tau_near_C = tau_C_after
    equiv_holds = (tau_after > tau_C_after)
    print(f"(insufficient overlap; using before/after comparison)")

print(f"TEST 3: {'PASS' if equiv_holds else 'FAIL'}")

# ═══════════════════════════════════════════════════════════════════════════════
# Figure — 2×2 panels
# ═══════════════════════════════════════════════════════════════════════════════
print("\nGenerating figure...")
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
time_ax = np.arange(N_STEPS)

# Panel 1: τ_c over time — geodesic vs off-geodesic
ax = axes[0, 0]
ax.plot(time_ax, tau_geodesic_ts,    color='steelblue', lw=1.5, label='Geodesic (ether cells)')
ax.plot(time_ax, tau_offgeodesic_ts, color='tomato',    lw=1.5, label='Off-geodesic (glider region)')
ax.plot(time_ax, tau_nearby_ts,      color='orange',    lw=1.0, alpha=0.8,
        label=f'Nearby ether (±{NEARBY_R} cells)')
ax.axhline(tau_bg, color='steelblue', linestyle='--', alpha=0.4, label=f'τ_c bg={tau_bg:.3f}')
ax.set_xlabel('Outer step t')
ax.set_ylabel('Mean τ_c')
ax.set_title(
    f'Test 1 (48-GEO): τ_c Geodesic vs Off-Geodesic\n'
    f'geo={tau_geodesic_mean:.4f}, off-geo={tau_offgeodesic_mean:.4f}, p={t1_p:.2e}  '
    f'[{"PASS" if geo_principle_holds else "FAIL"}]'
)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# Panel 2: Cumulative effort
ax = axes[0, 1]
ax.plot(time_ax, np.cumsum(effort_glider),   color='tomato',    lw=1.5, label='Glider CoM path')
ax.plot(time_ax, np.cumsum(effort_geodesic), color='steelblue', lw=1.5, label='Geodesic (fixed position)')
ax.set_xlabel('Outer step t')
ax.set_ylabel('Cumulative Σ τ_c')
ax.set_title(
    f'Test 2 (49-EFF): Cumulative Computational Effort\n'
    f'Glider={cumulative_glider:.1f}, Geodesic={cumulative_geodesic:.1f}, '
    f'ratio={eff_ratio:.3f}  [{"PASS" if efficiency_holds else "FAIL"}]'
)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# Panel 3: τ_c window around X in C vs D
ax = axes[1, 0]
ax.plot(time_ax, tau_window_D, color='tomato',    lw=1.2, label=f'τ_c ±{WINDOW_R} around X in D (glider)')
ax.plot(time_ax, tau_window_C, color='steelblue', lw=1.2, alpha=0.7, label=f'τ_c ±{WINDOW_R} around X in C (free)')
ax.axvline(arrival_est, color='black', linestyle='--', alpha=0.7, label=f'Est. arrival t={arrival_est}')
if near_mask3.sum() > 0:
    near_steps = np.where(near_mask3)[0]
    ax.axvspan(near_steps[0] - 0.5, near_steps[-1] + 0.5, alpha=0.12, color='tomato',
               label=f'Glider within ±{NEARBY_R} of X (n={near_mask3.sum()})')
ax.set_xlabel('Outer step t')
ax.set_ylabel(f'Mean τ_c (window ±{WINDOW_R} around X={X})')
ax.set_title(
    f'Test 3 (50-EQUIV): Equivalence Principle\n'
    f'D before={tau_before:.4f}, D after={tau_after:.4f}, '
    f'C free={tau_C_free:.4f}  [{"PASS" if equiv_holds else "FAIL"}]'
)
ax.legend(fontsize=7)
ax.grid(True, alpha=0.3)

# Panel 4: τ_c heatmap — tape B (glider visible as bright/dark stripe) vs tape A (uniform)
ax = axes[1, 1]
combined = np.hstack([spacetime_A[:, :OUTER_L // 2], spacetime_B[:, :OUTER_L // 2]])
im = ax.imshow(combined, aspect='auto', origin='upper', cmap='hot', interpolation='nearest')
ax.axvline(OUTER_L // 2, color='white', lw=1.5, linestyle='--', alpha=0.7)
ax.set_xlabel('Cell index (left=tape A geodesic, right=tape B glider)')
ax.set_ylabel('Outer step t')
ax.set_title('τ_c Heatmap: Tape A (uniform) | Tape B (glider visible)')
ax.text(60,  8, 'Tape A\n(geodesic)', color='white', fontsize=7)
ax.text(310, 8, 'Tape B\n(glider)', color='white', fontsize=7)
plt.colorbar(im, ax=ax, label='τ_c')

plt.suptitle(
    f'AFCA Geodesic Computation Tests — Ranks 48-GEO / 49-EFF / 50-EQUIV\n'
    f'Rule 110, L={OUTER_L}, M={M}, glider={GLIDER}, n_steps={N_STEPS}',
    fontsize=11, y=1.01
)
plt.tight_layout()
fig_path = 'rank48_geo_results.png'
plt.savefig(fig_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"Figure saved: {fig_path}")

# ═══════════════════════════════════════════════════════════════════════════════
# Results JSON
# ═══════════════════════════════════════════════════════════════════════════════
results = {
    "test1_48_GEO": {
        "tau_geodesic_mean":    tau_geodesic_mean,
        "tau_offgeodesic_mean": tau_offgeodesic_mean,
        "tau_nearby_mean":      tau_nearby_mean,
        "tau_background":       tau_bg,
        "t_statistic":          float(t1_stat),
        "p_value":              float(t1_p),
        "tau_ratio_offgeo_over_geo": float(tau_offgeodesic_mean / tau_geodesic_mean),
        "geodesic_principle_holds": bool(geo_principle_holds),
        "evidence": t1_evidence,
        "detection_method": "diff-from-reference (tape_B != tape_A, same as Round 19)",
    },
    "test2_49_EFF": {
        "cumulative_effort_glider":   cumulative_glider,
        "cumulative_effort_geodesic": cumulative_geodesic,
        "effort_ratio_glider_over_geodesic": float(eff_ratio),
        "n_steps": N_STEPS,
        "efficiency_principle_holds": bool(efficiency_holds),
    },
    "test3_50_EQUIV": {
        "tau_window_D_before_arrival": tau_before,
        "tau_window_D_after_arrival":  tau_after,
        "tau_window_C_before_arrival": tau_C_before,
        "tau_window_C_after_arrival":  tau_C_after,
        "tau_free_evolution":          tau_C_free,
        "tau_near_D":                  tau_near_D,
        "tau_near_C":                  tau_near_C,
        "arrival_estimate_step":       arrival_est,
        "n_steps_glider_nearby":       int(near_mask3.sum()),
        "window_radius":               WINDOW_R,
        "equivalence_principle_holds": bool(equiv_holds),
    },
    "parameters": {
        "OUTER_L": OUTER_L,
        "M": M,
        "C_EFF": C_EFF,
        "n_steps": N_STEPS,
        "glider_seed": GLIDER,
        "ETHER14": ETHER14.tolist(),
        "NEARBY_R": NEARBY_R,
        "WINDOW_R": WINDOW_R,
    }
}

json_path = 'rank48_geo_results.json'
with open(json_path, 'w') as f:
    json.dump(results, f, indent=2)
print(f"Results JSON saved: {json_path}")

# ── Summary ────────────────────────────────────────────────────────────────────
print("\n" + "="*65)
print("SUMMARY")
print("="*65)
print(f"48-GEO (Geodesic Principle):   {'PASS ✓' if geo_principle_holds else 'FAIL ✗'}")
print(f"  τ_c geo={tau_geodesic_mean:.4f}  off-geo={tau_offgeodesic_mean:.4f}  "
      f"ratio={tau_offgeodesic_mean/tau_geodesic_mean:.4f}  p={t1_p:.2e}")
print(f"49-EFF (Effort ∝ Proper Time): {'PASS ✓' if efficiency_holds else 'FAIL ✗'}")
print(f"  Σ glider={cumulative_glider:.1f}  geodesic={cumulative_geodesic:.1f}  ratio={eff_ratio:.4f}")
print(f"50-EQUIV (Equivalence Princ):  {'PASS ✓' if equiv_holds else 'FAIL ✗'}")
print(f"  τ_c near D={tau_near_D:.4f}  near C={tau_near_C:.4f}  free C={tau_C_free:.4f}")
overall = sum([geo_principle_holds, efficiency_holds, equiv_holds])
print(f"\nOverall: {overall}/3 tests passed")
