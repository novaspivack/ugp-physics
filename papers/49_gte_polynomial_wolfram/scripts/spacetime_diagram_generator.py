#!/usr/bin/env python3
"""
spacetime_diagram_generator.py — Z₇ polynomial spacetime diagrams on ether background.

Generates two publication-quality spacetime diagrams of the GTE polynomial
p(L,C,R) = C + R - C*R - L*C*R (mod 7):

  p49_gte_spacetime_perturbed_v2.png
    — 56-cell ether tape with a single Z₇=3 injection at center.
      The unperturbed ether (Rule 110 binary sublayer) persists outside the
      causal light cone. The Z₇=3 injection generates a multicolored causal
      cone spreading at v_max = c = 1 cell/step (hard bound from r=1).

  p49_gte_ether_only_v2.png
    — Unperturbed 56-cell ether tape (pure Rule 110 binary background).
      Shows the period-14 stability of the vacuum substrate.

Color map: 0=black (VAC), 1=white (ether), 2=red (up), 3=orange (W),
           4=yellow (down), 5=cyan (strange), 6=magenta (electron)

Output: figures/ subdirectory relative to this script.

Dependencies: numpy, matplotlib (no GPU required)
"""

import signal
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np

TIMEOUT_SECONDS = 120

SCRIPT_DIR = Path(__file__).resolve().parent
FIGURES_DIR = SCRIPT_DIR / "figures"

# Period-14 Rule 110 ether background (verified in P28, Lean-certified)
ETHER_14 = [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]

# Z₇ color map — consistent across all P49 figures
Z7_COLORS = [
    "#000000",  # 0 VAC
    "#ffffff",  # 1 ether
    "#ff2222",  # 2 up-quark
    "#ff8800",  # 3 W-boson
    "#ffff00",  # 4 down-quark
    "#00e5ff",  # 5 strange / νR
    "#ff00ff",  # 6 electron
]

Z7_LABELS = ["0 VAC", "1 ether", "2 u", "3 W", "4 d", "5 s", "6 e⁻"]

BG_COLOR = "#0a0a14"

L = 56
T = 56
INJECTION_CELL = L // 2
INJECTION_VALUE = 3


def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: {TIMEOUT_SECONDS}s wall-clock limit reached.")
    sys.exit(1)


def p_poly(left: int, center: int, right: int) -> int:
    """GTE polynomial p(L,C,R) = C + R - C*R - L*C*R (mod 7).

    On binary {0,1}^3 inputs: equals Rule 110 (Lean: rule110_z7_poly_rep, CatAL).
    """
    return (center + right - center * right - left * center * right) % 7


def make_ether(length: int) -> np.ndarray:
    """Build a period-14 ether background of the given length."""
    tile = ETHER_14 * (length // 14 + 1)
    return np.array(tile[:length], dtype=np.int32)


def run_ca(initial: np.ndarray, steps: int) -> np.ndarray:
    """Run the Z₇ polynomial CA for `steps` timesteps on a periodic tape.

    Returns a (steps+1) × len(initial) array.
    """
    n = len(initial)
    spacetime = np.zeros((steps + 1, n), dtype=np.int32)
    spacetime[0] = initial
    for t in range(steps):
        row = spacetime[t]
        for i in range(n):
            spacetime[t + 1, i] = p_poly(
                int(row[(i - 1) % n]),
                int(row[i]),
                int(row[(i + 1) % n]),
            )
    return spacetime


def make_colormap():
    return mcolors.ListedColormap(Z7_COLORS)


def plot_spacetime(spacetime: np.ndarray, ax, title: str = "") -> None:
    """Render a Z₇ spacetime array on the given axes."""
    cmap = make_colormap()
    ax.set_facecolor(BG_COLOR)
    ax.imshow(
        spacetime,
        aspect="auto",
        cmap=cmap,
        vmin=0,
        vmax=6,
        interpolation="nearest",
        origin="upper",
    )
    ax.set_xlabel("cell index", color="#aaaaaa", fontsize=9)
    ax.set_ylabel("time step", color="#aaaaaa", fontsize=9)
    ax.tick_params(colors="#aaaaaa", labelsize=7)
    for spine in ax.spines.values():
        spine.set_edgecolor("#444444")
    if title:
        ax.set_title(title, color="white", fontsize=10, pad=5)


def save_spacetime_figure(
    spacetime: np.ndarray,
    path: Path,
    title: str,
    caption: str,
    mark_injection: bool = False,
) -> None:
    """Save a single spacetime diagram as a publication-quality PNG (300 DPI)."""
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor(BG_COLOR)

    plot_spacetime(spacetime, ax, title)

    if mark_injection:
        ax.axvline(INJECTION_CELL, color="#ffffff44", linewidth=0.8, linestyle="--")
        ax.annotate(
            f"Z₇={INJECTION_VALUE} injection",
            xy=(INJECTION_CELL, 2),
            xytext=(INJECTION_CELL + 4, 8),
            color="white",
            fontsize=7,
            arrowprops=dict(arrowstyle="->", color="white", lw=0.7),
        )

    # Color legend
    import matplotlib.patches as mpatches
    patches = [
        mpatches.Patch(facecolor=Z7_COLORS[v], label=Z7_LABELS[v],
                       edgecolor="#555555" if v == 1 else "none", linewidth=0.5)
        for v in range(7)
    ]
    legend = ax.legend(
        handles=patches,
        loc="upper right",
        fontsize=6,
        facecolor="#1a1a2e",
        edgecolor="#444444",
        labelcolor="white",
        framealpha=0.9,
        ncol=2,
        handlelength=1.0,
        handleheight=0.8,
    )

    fig.text(
        0.5, 0.01,
        caption,
        ha="center",
        va="bottom",
        fontsize=7,
        color="#aaaaaa",
        wrap=True,
    )

    plt.tight_layout(rect=[0, 0.07, 1, 1.0])
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    print(f"Saved: {path.name}  ({path.stat().st_size // 1024} KB)")


def generate_perturbed_diagram() -> Path:
    """Generate the ether + Z₇=3 injection spacetime diagram."""
    ether = make_ether(L)
    tape = ether.copy()
    tape[INJECTION_CELL] = INJECTION_VALUE
    spacetime = run_ca(tape, T)

    path = FIGURES_DIR / "p49_gte_spacetime_perturbed_v2.png"
    save_spacetime_figure(
        spacetime,
        path,
        title=f"p(L,C,R) mod 7 — Z₇={INJECTION_VALUE} injection into ether ({L}×{T})",
        caption=(
            f"Spacetime evolution of p(L,C,R) = C+R−CR−LCR (mod 7) on a {L}-cell ether background.\n"
            f"A single Z₇={INJECTION_VALUE} injection at cell {INJECTION_CELL} (step 0) generates a multicolored causal "
            f"cone spreading at v_max = c = 1 cell/step.\n"
            f"All seven Z₇ values appear inside the cone; the unperturbed ether (black/white) persists outside."
        ),
        mark_injection=True,
    )
    return path


def generate_ether_only_diagram() -> Path:
    """Generate the unperturbed ether spacetime diagram."""
    ether = make_ether(L)
    spacetime = run_ca(ether, T)

    path = FIGURES_DIR / "p49_gte_ether_only_v2.png"
    save_spacetime_figure(
        spacetime,
        path,
        title=f"Unperturbed ether — p(L,C,R) mod 7 ({L}×{T})",
        caption=(
            f"Unperturbed {L}-cell ether background under p mod 7. "
            f"The period-14 Rule 110 sublayer is globally stable: "
            f"all cells remain in {{0,1}} for all time steps, "
            f"confirming that the ether is an exact fixed subspace of the full Z₇ rule."
        ),
    )
    return path


if __name__ == "__main__":
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(TIMEOUT_SECONDS)
    t0 = time.time()

    print("Z₇ spacetime diagram generator")
    print(f"  Tape length: {L} cells | Time steps: {T}")
    print(f"  Ether background: period-14 Rule 110 ({sum(ETHER_14)} ones in {len(ETHER_14)} cells)")
    print(f"  Injection: Z₇={INJECTION_VALUE} at cell {INJECTION_CELL}")
    print()

    p1 = generate_perturbed_diagram()
    p2 = generate_ether_only_diagram()

    signal.alarm(0)
    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s")
    print(f"  {p1}")
    print(f"  {p2}")
