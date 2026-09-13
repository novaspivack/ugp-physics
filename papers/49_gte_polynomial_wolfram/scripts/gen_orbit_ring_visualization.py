#!/usr/bin/env python3
"""
gen_orbit_ring_visualization.py — Four-state GEN orbit ring visualization.

Generates the orbit ring figure showing the three-generation orbit:
  GEN1 → GEN2 → GEN3 → VAC (under f_MDL on a 5-cell periodic ring)

Each orbit state is drawn as a ring of 5 nodes, color-coded by Z₇ winding value.
The four rings are arranged in a 2×2 grid with arrows indicating the orbit progression.

This is the Lean-certified three-generation orbit (CatAL):
  fmdl_z7_three_generation_orbit — UgpLean/Universality/CUP3DUniqueness.lean

Orbit values (Lean-certified, zero sorry):
  GEN1 = [1, 5, 2, 2, 1]   — first generation (up-type)
  GEN2 = [2, 5, 2, 0, 2]   — second generation (charm-type)
  GEN3 = [5, 6, 5, 3, 5]   — third generation (top-type)
  VAC  = [0, 0, 0, 0, 0]   — vacuum (no excitation)

Output: figures/p49_gte_orbit_rings_v2.png

Dependencies: numpy, matplotlib
"""

import signal
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

TIMEOUT_SECONDS = 60

SCRIPT_DIR = Path(__file__).resolve().parent
FIGURES_DIR = SCRIPT_DIR / "figures"

# GEN orbit (Lean-certified, CatAL, zero sorry)
GEN1 = [1, 5, 2, 2, 1]
GEN2 = [2, 5, 2, 0, 2]
GEN3 = [5, 6, 5, 3, 5]
VAC  = [0, 0, 0, 0, 0]

# Z₇ color map — consistent across all P49 figures
Z7_COLORS = {
    0: "#000000",  # VAC — black
    1: "#ffffff",  # ether — white
    2: "#ff2222",  # up-quark — red
    3: "#ff8800",  # W-boson — orange
    4: "#ffff00",  # down-quark — yellow
    5: "#00e5ff",  # strange — cyan
    6: "#ff00ff",  # electron — magenta
}
Z7_NAMES = {0: "VAC", 1: "ether", 2: "u", 3: "W", 4: "d", 5: "s", 6: "e⁻"}

BG_COLOR = "#0a0a14"
RING_BG  = "#0f0f24"


def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)


def draw_orbit_ring(ax, values: list, label: str, gen_label: str) -> None:
    """Draw a ring of 5 nodes on the given axes.

    Nodes are placed on a circle, colored by their Z₇ value.
    """
    n = len(values)
    ax.set_facecolor(RING_BG)
    ax.set_aspect("equal")
    ax.axis("off")

    # Node positions on unit circle
    angles = [2 * np.pi * i / n - np.pi / 2 for i in range(n)]
    xs = [0.85 * np.cos(a) for a in angles]
    ys = [0.85 * np.sin(a) for a in angles]

    # Draw ring connections
    for i in range(n):
        j = (i + 1) % n
        ax.plot(
            [xs[i], xs[j]], [ys[i], ys[j]],
            color="#444466", linewidth=1.5, zorder=1,
        )

    # Draw nodes
    node_radius = 0.18
    for i, (x, y, v) in enumerate(zip(xs, ys, values)):
        color = Z7_COLORS[v]
        edge_color = "#aaaaaa" if v == 0 else ("#555555" if v == 1 else color)
        circle = plt.Circle(
            (x, y), node_radius,
            facecolor=color,
            edgecolor=edge_color,
            linewidth=1.5,
            zorder=2,
        )
        ax.add_patch(circle)

        # Value label inside node
        text_color = "#cccccc" if v in (0, 2, 3, 4, 5, 6) else "#000000"
        if v == 1:
            text_color = "#000000"
        ax.text(
            x, y, str(v),
            ha="center", va="center",
            fontsize=9, fontweight="bold",
            color=text_color, zorder=3,
        )

        # Sector name below node
        ax.text(
            x, y - node_radius - 0.08, Z7_NAMES[v],
            ha="center", va="top",
            fontsize=5.5, color="#999999", zorder=3,
        )

    # Generation label above ring
    ax.text(
        0, 1.08, gen_label,
        ha="center", va="bottom",
        fontsize=11, fontweight="bold", color="white",
    )

    # Winding sum annotation
    winding = sum(values) % 7
    ax.text(
        0, -1.12, f"Σ mod 7 = {winding}",
        ha="center", va="top",
        fontsize=7, color="#888888",
    )

    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.3, 1.3)


def draw_orbit_arrow(fig, ax_from, ax_to, label: str = "") -> None:
    """Draw an arrow between two ring axes using figure coordinates."""
    # Use transFigure to draw connecting arrows
    from matplotlib.patches import FancyArrowPatch
    bbox_from = ax_from.get_position()
    bbox_to   = ax_to.get_position()
    x0 = bbox_from.x1
    y0 = (bbox_from.y0 + bbox_from.y1) / 2
    x1 = bbox_to.x0
    y1 = (bbox_to.y0 + bbox_to.y1) / 2
    fig.patches.append(
        FancyArrowPatch(
            (x0, y0), (x1, y1),
            transform=fig.transFigure,
            arrowstyle="->",
            color="#dddddd",
            lw=1.5,
            mutation_scale=15,
        )
    )


def generate_orbit_ring_figure() -> Path:
    """Generate and save the four-ring orbit visualization."""
    orbits = [
        (GEN1, "GEN₁ = [1,5,2,2,1]"),
        (GEN2, "GEN₂ = [2,5,2,0,2]"),
        (GEN3, "GEN₃ = [5,6,5,3,5]"),
        (VAC,  "VAC  = [0,0,0,0,0]"),
    ]

    fig, axes = plt.subplots(1, 4, figsize=(16, 5))
    fig.patch.set_facecolor(BG_COLOR)

    for ax, (values, label) in zip(axes, orbits):
        draw_orbit_ring(ax, values, label, label)

    # Draw arrows between rings using figure coordinates
    for i in range(3):
        draw_orbit_arrow(fig, axes[i], axes[i + 1])

    # Main title
    fig.suptitle(
        "GTE Three-Generation Orbit under f_MDL (5-cell periodic ring)",
        color="white", fontsize=13, y=1.02,
    )

    # Caption
    fig.text(
        0.5, -0.05,
        "Orbit GEN₁→GEN₂→GEN₃→VAC under f_MDL on a 5-cell periodic ring.\n"
        "Node color encodes Z₇ winding value. Each orbit state maps exactly to the next in three f_MDL steps.\n"
        "Lean-certified zero sorry: fmdl_z7_three_generation_orbit (CatAL, UgpLean/Universality/CUP3DUniqueness.lean).",
        ha="center", va="top",
        fontsize=7.5, color="#aaaaaa",
    )

    # Z₇ legend
    legend_patches = [
        mpatches.Patch(facecolor=Z7_COLORS[v], label=f"{v}={Z7_NAMES[v]}",
                       edgecolor="#555555" if v in (0, 1) else Z7_COLORS[v], linewidth=0.5)
        for v in range(7)
    ]
    fig.legend(
        handles=legend_patches,
        loc="lower center",
        ncol=7,
        fontsize=7,
        facecolor="#1a1a2e",
        edgecolor="#444444",
        labelcolor="white",
        framealpha=0.9,
        bbox_to_anchor=(0.5, -0.15),
    )

    plt.tight_layout(rect=[0, 0.0, 1, 1.0])

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / "p49_gte_orbit_rings_v2.png"
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    print(f"Saved: {path.name}  ({path.stat().st_size // 1024} KB)")
    return path


if __name__ == "__main__":
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(TIMEOUT_SECONDS)
    t0 = time.time()

    print("GEN orbit ring visualization")
    print(f"  GEN1: {GEN1}")
    print(f"  GEN2: {GEN2}")
    print(f"  GEN3: {GEN3}")
    print(f"  VAC:  {VAC}")
    print()

    path = generate_orbit_ring_figure()

    signal.alarm(0)
    print(f"\nDone in {time.time() - t0:.1f}s")
    print(f"  {path}")
