#!/usr/bin/env python3
"""
ppoly_fmdl_contrast.py — f_MDL vs p_poly contrast figures.

Generates three paper-quality figures demonstrating that f_MDL (SM orbit
construction) and p_poly (raw GTE polynomial) are genuinely different objects —
they agree on binary inputs but diverge at SM orbit positions.

Lean certification: p_poly_agrees_fmdl_at_orbit was REFUTED by decide in
Z7InvariantSubsets.lean. Example: at (L=1,C=1,R=5), f_MDL=2 but p_poly=3.

Output figures saved to figures/ subdirectory:
  p49_gen1_fmdl_vs_ppoly.png  — GEN1 ring evolution, f_MDL vs p_poly
  p49_ether_fmdl_vs_ppoly.png — ether + injection, f_MDL vs p_poly
  p49_fmdl_vs_ppoly_table.png — lookup table sparsity comparison (343 cells)

Dependencies: numpy, matplotlib
"""

from __future__ import annotations

import signal
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

TIMEOUT_SECONDS = 300
SCRIPT_DIR = Path(__file__).resolve().parent
FIGURES_DIR = SCRIPT_DIR / "figures"


def _timeout_handler(_signum, _frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ---------------------------------------------------------------------------
# Color map — consistent across all P49 figures
# ---------------------------------------------------------------------------
Z7_COLORS = {
    0: "#000000",  # VAC — black
    1: "#ffffff",  # ether — white
    2: "#ff2222",  # up — red
    3: "#ff8800",  # W — orange
    4: "#ffff00",  # down — yellow
    5: "#00e5ff",  # s — cyan
    6: "#ff00ff",  # electron — magenta
}
Z7_NAMES = {0: "VAC", 1: "ether", 2: "up", 3: "W", 4: "down", 5: "s", 6: "e⁻"}

BG_COLOR = "#0a0a14"

# ---------------------------------------------------------------------------
# f_MDL lookup table — 10 SM orbit neighborhoods + 8 binary Rule 110 entries
# Source: two_layer_chiral_afca_prototype.py lines 105–117 (canonical P41 script)
# ---------------------------------------------------------------------------
_RULE110 = {
    (1, 1, 1): 0, (1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 0,
    (0, 1, 1): 1, (0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 0,
}

_FMDL_ORBIT = {
    (1, 1, 5): 2, (1, 5, 2): 5, (5, 2, 2): 2, (2, 2, 1): 0,
    (2, 1, 1): 2, (2, 2, 5): 5, (2, 5, 2): 6, (5, 2, 0): 5,
    (2, 0, 2): 3, (0, 2, 2): 5,
}
# Merge: Rule 110 entries fill in binary triples not overridden by orbit entries
for _k, _v in _RULE110.items():
    _FMDL_ORBIT.setdefault(_k, _v)
# All other triples default to 0 (vacuum projector)

GEN1 = (1, 5, 2, 2, 1)
GEN2 = (2, 5, 2, 0, 2)
GEN3 = (5, 6, 5, 3, 5)
VAC  = (0, 0, 0, 0, 0)

ETHER14 = np.array([1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0], dtype=np.uint8)


# ---------------------------------------------------------------------------
# Rule functions
# ---------------------------------------------------------------------------

def fmdl(l: int, c: int, r: int) -> int:
    """f_MDL: 18-entry lookup table; default 0 off-orbit (vacuum projector)."""
    return _FMDL_ORBIT.get((l, c, r), 0)


def p_poly(l: int, c: int, r: int) -> int:
    """p(L,C,R) = (C + R - C*R - L*C*R) mod 7 — raw GTE polynomial."""
    return (c + r - c * r - l * c * r) % 7


def step_ring(state: tuple[int, ...], rule_fn) -> tuple[int, ...]:
    """Advance a periodic ring one step under rule_fn (L,C,R) → new value."""
    n = len(state)
    return tuple(rule_fn(state[(i - 1) % n], state[i], state[(i + 1) % n])
                 for i in range(n))


def step_tape(state: np.ndarray, rule_fn) -> np.ndarray:
    """Advance a 1D tape one step under rule_fn with periodic boundaries."""
    n = len(state)
    new = np.zeros(n, dtype=np.int32)
    for i in range(n):
        new[i] = rule_fn(int(state[(i - 1) % n]), int(state[i]), int(state[(i + 1) % n]))
    return new


def evolve_ring(initial: tuple[int, ...], rule_fn, steps: int) -> list[tuple[int, ...]]:
    """Evolve a ring for `steps` time steps, returning list of states (step 0 = initial)."""
    history = [initial]
    s = initial
    for _ in range(steps):
        s = step_ring(s, rule_fn)
        history.append(s)
    return history


def evolve_tape(initial: np.ndarray, rule_fn, steps: int) -> np.ndarray:
    """Evolve a tape for `steps` time steps; returns (steps+1, len) spacetime array."""
    n = len(initial)
    spacetime = np.zeros((steps + 1, n), dtype=np.int32)
    spacetime[0] = initial
    for t in range(steps):
        spacetime[t + 1] = step_tape(spacetime[t], rule_fn)
    return spacetime


# ---------------------------------------------------------------------------
# Spacetime diagram helpers
# ---------------------------------------------------------------------------

def _z7_rgba(val: int) -> list[float]:
    h = Z7_COLORS.get(val, "#888888").lstrip("#")
    return [int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)] + [1.0]


def spacetime_image(history: list[tuple[int, ...]] | np.ndarray) -> np.ndarray:
    """Convert a spacetime array (steps+1, cells) to an RGBA image."""
    arr = np.array(history) if isinstance(history, list) else history
    rows, cols = arr.shape
    img = np.zeros((rows, cols, 4))
    for t in range(rows):
        for x in range(cols):
            img[t, x] = _z7_rgba(int(arr[t, x]))
    return img


def plot_spacetime_panel(ax, img, title, xlabel="cell", ylabel="step",
                         bg=BG_COLOR, labelsize=9):
    ax.set_facecolor(bg)
    ax.imshow(img, aspect="auto", interpolation="nearest", origin="upper")
    ax.set_title(title, color="white", fontsize=10, pad=4)
    ax.set_xlabel(xlabel, color="#aaaaaa", fontsize=labelsize)
    ax.set_ylabel(ylabel, color="#aaaaaa", fontsize=labelsize)
    ax.tick_params(colors="#aaaaaa", labelsize=7)
    for spine in ax.spines.values():
        spine.set_edgecolor("#444444")


# ---------------------------------------------------------------------------
# Color legend patch builder
# ---------------------------------------------------------------------------

def make_legend(ax, values=None):
    if values is None:
        values = list(range(7))
    patches = [mpatches.Patch(color=Z7_COLORS[v],
                              label=f"{v}={Z7_NAMES[v]}",
                              linewidth=0.5 if v == 1 else 0)
               for v in values]
    ax.legend(handles=patches, loc="upper right", fontsize=6,
              facecolor="#1a1a2e", edgecolor="#444444", labelcolor="white",
              framealpha=0.85, ncol=2, handlelength=1.2, handleheight=0.9)


# ---------------------------------------------------------------------------
# Figure 1: GEN1 ring — f_MDL vs p_poly (8 steps)
# ---------------------------------------------------------------------------

def figure1_gen1_contrast():
    steps = 8
    hist_fmdl = evolve_ring(GEN1, fmdl, steps)
    hist_ppoly = evolve_ring(GEN1, p_poly, steps)

    # Diagnostic output
    print("=== GEN1 ring evolution ===")
    print(f"  Initial: {list(GEN1)}")
    for t in range(min(5, steps + 1)):
        tag_f = ""
        if list(hist_fmdl[t]) == list(GEN2):
            tag_f = " = GEN2 ✓"
        elif list(hist_fmdl[t]) == list(GEN3):
            tag_f = " = GEN3 ✓"
        elif list(hist_fmdl[t]) == list(VAC):
            tag_f = " = VAC ✓"
        print(f"  Step {t}: f_MDL={list(hist_fmdl[t])}{tag_f}  |  p_poly={list(hist_ppoly[t])}")

    match1_ppoly = list(hist_ppoly[1]) == list(GEN2)
    print(f"\n  p_poly step1 == GEN2? {match1_ppoly}  (should be False per Lean)")
    print(f"  f_MDL step1 == GEN2? {list(hist_fmdl[1]) == list(GEN2)}  (should be True)")
    print(f"  f_MDL step2 == GEN3? {list(hist_fmdl[2]) == list(GEN3)}")
    print(f"  f_MDL step3 == VAC?  {list(hist_fmdl[3]) == list(VAC)}")

    img_fmdl = spacetime_image(hist_fmdl)
    img_ppoly = spacetime_image(hist_ppoly)

    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    fig.patch.set_facecolor(BG_COLOR)

    plot_spacetime_panel(axes[0], img_fmdl,
                         "f_MDL: SM Orbit (GEN₁→GEN₂→GEN₃→VAC)")
    plot_spacetime_panel(axes[1], img_ppoly,
                         "p_poly: Raw GTE Polynomial (diverges from SM orbit)")

    # Step labels on left panel
    orbit_labels = {0: "GEN₁", 1: "GEN₂", 2: "GEN₃", 3: "VAC"}
    for t, lbl in orbit_labels.items():
        axes[0].annotate(lbl, xy=(-0.15, t / steps), xycoords="axes fraction",
                         color="#dddddd", fontsize=7, va="center", ha="right")

    # Common colorbar / legend
    make_legend(axes[1])

    caption = (
        "Evolution of the GEN₁=[1,5,2,2,1] ring state under two rules over 8 steps.\n"
        "Left: under f_MDL (SM orbit construction), the ring follows GEN₁→GEN₂→GEN₃→VAC in three steps and remains at vacuum.\n"
        "Right: under p_poly (unrestricted GTE polynomial), the same initial state evolves differently —\n"
        "f_MDL and p_poly agree only on binary inputs, not on SM orbit positions."
    )
    fig.text(0.5, 0.01, caption, ha="center", va="bottom", fontsize=7,
             color="#aaaaaa", wrap=True)

    plt.tight_layout(rect=[0, 0.10, 1, 0.97])

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out = FIGURES_DIR / "p49_gen1_fmdl_vs_ppoly.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    print(f"\n  Saved: {out}  ({out.stat().st_size // 1024} KB)")
    return out


# ---------------------------------------------------------------------------
# Figure 2: ether + injection — f_MDL vs p_poly (30 steps, 28 cells)
# ---------------------------------------------------------------------------

def figure2_ether_contrast():
    cells = 28
    steps = 30
    center = cells // 2

    # Build 28-cell ether tape (tile ETHER14 twice)
    ether = np.tile(ETHER14, cells // len(ETHER14) + 1)[:cells].astype(np.int32)

    # Inject Z₇=3 at center
    tape = ether.copy()
    tape[center] = 3

    st_ppoly = evolve_tape(tape, p_poly, steps)
    st_fmdl  = evolve_tape(tape, fmdl, steps)

    print("\n=== Ether + injection (value=3 at center) ===")
    print(f"  Ether tape (28 cells): {list(ether)}")
    print(f"  Injected tape center[{center}] = 3")
    print(f"  p_poly step1, center region [cells {center-2}..{center+2}]: "
          f"{list(st_ppoly[1, center-2:center+3])}")
    print(f"  f_MDL  step1, center region [cells {center-2}..{center+2}]: "
          f"{list(st_fmdl[1, center-2:center+3])}")
    fmdl_c1 = int(st_fmdl[1, center])
    print(f"  f_MDL injected cell after 1 step: {fmdl_c1}  (expect 0 = vacuum drain)")

    img_ppoly = spacetime_image(st_ppoly)
    img_fmdl  = spacetime_image(st_fmdl)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
    fig.patch.set_facecolor(BG_COLOR)

    plot_spacetime_panel(axes[0], img_ppoly,
                         "p_poly: Class 3 Z₇ light cone",
                         xlabel="cell (0–27)", ylabel="step (0–30)")
    plot_spacetime_panel(axes[1], img_fmdl,
                         "f_MDL: perturbation drains to vacuum",
                         xlabel="cell (0–27)", ylabel="step (0–30)")

    # Mark injection point
    for ax in axes:
        ax.axvline(center, color="#ffffff44", linewidth=0.6, linestyle="--")
    axes[0].annotate("injection", xy=(center, 0), xytext=(center + 3, 3),
                     color="white", fontsize=7, arrowprops=dict(arrowstyle="->", color="white", lw=0.7))

    make_legend(axes[1])

    caption = (
        "Response of the ether background to a single-cell Z₇=3 perturbation.\n"
        "Left (p_poly): perturbation generates a Class 3 chaotic light cone spreading at v_max=c.\n"
        "Right (f_MDL): perturbation drains to vacuum within 1–2 steps — f_MDL maps nearly all "
        "non-orbit triples to 0, preserving the ether background.\n"
        "This contrast illustrates why the Z₇ spacetime diagrams (§6) use p_poly, not f_MDL."
    )
    fig.text(0.5, 0.01, caption, ha="center", va="bottom", fontsize=7,
             color="#aaaaaa")

    plt.tight_layout(rect=[0, 0.10, 1, 0.97])

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out = FIGURES_DIR / "p49_ether_fmdl_vs_ppoly.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    print(f"\n  Saved: {out}  ({out.stat().st_size // 1024} KB)")
    return out


# ---------------------------------------------------------------------------
# Figure 3: Lookup table sparsity comparison (343 cells, L×C×R grid)
# ---------------------------------------------------------------------------

def figure3_table_comparison():
    # Build full 7×7×7 output tables
    fmdl_table  = np.zeros((7, 7, 7), dtype=np.int32)
    ppoly_table = np.zeros((7, 7, 7), dtype=np.int32)

    for l in range(7):
        for c in range(7):
            for r in range(7):
                fmdl_table[l, c, r]  = fmdl(l, c, r)
                ppoly_table[l, c, r] = p_poly(l, c, r)

    fmdl_nz  = int((fmdl_table  != 0).sum())
    ppoly_nz = int((ppoly_table != 0).sum())
    print(f"\n=== Lookup table statistics ===")
    print(f"  f_MDL  nonzero: {fmdl_nz}/343 ({100*fmdl_nz/343:.1f}%)")
    print(f"  p_poly nonzero: {ppoly_nz}/343 ({100*ppoly_nz/343:.1f}%)")

    # Flatten for display: show as 7×49 grid (L×(C×R))
    # Reshape: (7_L, 7_C, 7_R) → (7_L, 49_CR)
    fmdl_flat  = fmdl_table.reshape(7, 49)
    ppoly_flat = ppoly_table.reshape(7, 49)

    def to_rgba(arr2d: np.ndarray) -> np.ndarray:
        rows, cols = arr2d.shape
        img = np.zeros((rows, cols, 4))
        for i in range(rows):
            for j in range(cols):
                img[i, j] = _z7_rgba(int(arr2d[i, j]))
        return img

    img_fmdl  = to_rgba(fmdl_flat)
    img_ppoly = to_rgba(ppoly_flat)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.patch.set_facecolor(BG_COLOR)

    for ax, img, title, nz in [
        (axes[0], img_fmdl,  f"f_MDL: {fmdl_nz}/343 nonzero ({100*fmdl_nz/343:.0f}%)\n14 active entries (8 binary + 6 orbit ≠ 0)", fmdl_nz),
        (axes[1], img_ppoly, f"p_poly: {ppoly_nz}/343 nonzero ({100*ppoly_nz/343:.0f}%)\nunconstrained Z₇ polynomial", ppoly_nz),
    ]:
        ax.set_facecolor(BG_COLOR)
        ax.imshow(img, aspect="auto", interpolation="nearest", origin="upper")
        ax.set_title(title, color="white", fontsize=10, pad=5)
        ax.set_xlabel("C×R index (0–48, 7×7 grid)", color="#aaaaaa", fontsize=8)
        ax.set_ylabel("L (0–6)", color="#aaaaaa", fontsize=8)
        ax.set_yticks(range(7))
        ax.set_yticklabels(range(7), color="#aaaaaa", fontsize=7)
        ax.tick_params(colors="#aaaaaa", labelsize=7)
        for spine in ax.spines.values():
            spine.set_edgecolor("#444444")

    # Add grid lines to show C×R structure (every 7 columns)
    for ax in axes:
        for x in range(7, 49, 7):
            ax.axvline(x - 0.5, color="#444444", linewidth=0.4)

    make_legend(axes[1])

    caption = (
        f"Output value (color-coded by Z₇ value) for all 343 = 7³ triples (L, C, R).\n"
        f"Left (f_MDL): only {fmdl_nz}/343 entries are nonzero ({100*fmdl_nz/343:.0f}%); "
        f"all others output VAC=0 (vacuum projector).\n"
        f"Right (p_poly): {ppoly_nz}/343 entries nonzero ({100*ppoly_nz/343:.0f}%) — the raw "
        f"polynomial fills nearly all of Z₇.\n"
        f"The visual sparsity contrast demonstrates that f_MDL is a highly constrained "
        f"orbit-specific rule, not a restriction of p_poly."
    )
    fig.text(0.5, 0.01, caption, ha="center", va="bottom", fontsize=7.5,
             color="#aaaaaa")

    plt.tight_layout(rect=[0, 0.10, 1, 0.97])

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out = FIGURES_DIR / "p49_fmdl_vs_ppoly_table.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    print(f"\n  Saved: {out}  ({out.stat().st_size // 1024} KB)")
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("f_MDL vs p_poly contrast figures")
    print("=" * 60)

    # Verify the key conflict at (L=1, C=1, R=5) cited in Lean
    fmdl_115  = fmdl(1, 1, 5)
    ppoly_115 = p_poly(1, 1, 5)
    print(f"\nKey Lean counterexample: (L=1, C=1, R=5)")
    print(f"  f_MDL(1,1,5)  = {fmdl_115}  (should be 2, per table)")
    print(f"  p_poly(1,1,5) = {ppoly_115}  (should be 3, per Lean refutation)")
    print(f"  Disagreement confirmed: {fmdl_115 != ppoly_115}")

    out1 = figure1_gen1_contrast()
    out2 = figure2_ether_contrast()
    out3 = figure3_table_comparison()

    signal.alarm(0)

    print("\n" + "=" * 60)
    print("All figures generated:")
    print(f"  Figure 1: {out1}")
    print(f"  Figure 2: {out2}")
    print(f"  Figure 3: {out3}")
    print("=" * 60)
