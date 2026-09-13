#!/usr/bin/env python3
"""
three_tape_dpp_visualization.py — Three-tape DPP visualization suite.

Generates five paper-quality figures illustrating the three-tape DPP architecture:
  Figure 1: Three-tape DPP orbit v3 (improved 3D ring layout)
  Figure 2: Generation orbit 3D spacetime
  Figure 3: DPP clock coupling diagram (schematic)
  Figure 4: Three-tape causal layered graph
  Figure 5: Combined headline figure (single tape spacetime + three-tape orbit)

GTE context:
  - Three parallel Z7 tapes (x, y, z) sharing a common outer clock tau_c^out
  - Each tape runs: GEN1 -> GEN2 -> GEN3 -> VAC in 3 steps
  - Cross-tape coupling: p(wx, wy, wz) = 0 at ether, nonzero at generation positions
  - DPP (Dimensional Protocol Principle, CatAL): shared clock -> 3+1D spacetime

GEN orbit values:
  GEN1 = [1, 5, 2, 2, 1]
  GEN2 = [2, 5, 2, 0, 2]
  GEN3 = [5, 6, 5, 3, 5]
  VAC  = [0, 0, 0, 0, 0]
"""

from __future__ import annotations

import signal
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Circle, FancyArrow
from matplotlib.collections import LineCollection
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Line3DCollection
import numpy as np

TIMEOUT_SECONDS = 300
SCRIPT_DIR = Path(__file__).resolve().parent
FIGURES_DIR = SCRIPT_DIR / "figures"

# Z7 color map: 0=vacuum(black), 1=ether(white), 2=up(red), 3=W(orange), 4=down(yellow), 5=s(cyan), 6=electron(magenta)
Z7_COLORS = {
    0: "#000000",
    1: "#ffffff",
    2: "#ff2222",
    3: "#ff8800",
    4: "#ffff00",
    5: "#00e5ff",
    6: "#ff00ff",
}
Z7_NAMES = {
    0: "VAC",
    1: "ether",
    2: "up",
    3: "W",
    4: "down",
    5: "s",
    6: "e⁻",
}

# GEN orbit
GEN1 = [1, 5, 2, 2, 1]
GEN2 = [2, 5, 2, 0, 2]
GEN3 = [5, 6, 5, 3, 5]
VAC  = [0, 0, 0, 0, 0]

ORBIT = [GEN1, GEN2, GEN3, VAC]
ORBIT_LABELS = ["GEN₁", "GEN₂", "GEN₃", "VAC"]
ORBIT_STEP_LABELS = [
    "GEN₁=[1,5,2,2,1]",
    "GEN₂=[2,5,2,0,2]",
    "GEN₃=[5,6,5,3,5]",
    "VAC=[0,0,0,0,0]",
]
TAPE_COLORS = ["#ff4444", "#44ff88", "#4488ff"]  # x=red, y=green, z=blue
TAPE_LABELS = ["x-tape", "y-tape", "z-tape"]

BG_COLOR = "#0a0a14"
DARK_BG = "#0d0d1a"


def _timeout_handler(_signum, _frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Saving partial results.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)


# ---------------------------------------------------------------------------
# Helper: draw a colored node with Z7 value
# ---------------------------------------------------------------------------
def z7_node_color(val: int) -> str:
    return Z7_COLORS.get(val, "#888888")


# ---------------------------------------------------------------------------
# Figure 1: Three-tape DPP orbit v3 (improved 3D ring layout)
# ---------------------------------------------------------------------------
def figure1_three_tape_dpp_v3():
    """Three colored rings showing GEN1→GEN2→GEN3→VAC for x/y/z tapes in 3D."""
    fig = plt.figure(figsize=(12, 12), facecolor=BG_COLOR)
    ax = fig.add_subplot(111, projection="3d", facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    fig.patch.set_facecolor(BG_COLOR)

    # Orbit steps: 4 positions along orbit axis
    n_steps = 4
    n_cells = 5

    # Three tapes arranged in 3D:
    # x-tape: plane z=0, sweeping from y=-2 to y=2
    # y-tape: plane x=0, sweeping from z=-2 to z=2
    # z-tape: plane y=0, sweeping from x=-2 to x=2

    # Place tapes at three orientations; orbit "time" runs along a shared axis
    # t axis = diagonal out from origin for visual separation

    # We place the three tapes as vertical columns in a triangular arrangement
    # Tape 0 (x): centered at (0, 0, 0), orbit goes up in z
    # Tape 1 (y): centered at (3, 0, 0), orbit goes up in z
    # Tape 2 (z): centered at (1.5, 2.6, 0), orbit goes up in z
    # Within each tape: 5 cells arranged in a ring at each orbit level

    tape_centers = [
        np.array([0.0, 0.0]),
        np.array([4.0, 0.0]),
        np.array([2.0, 3.46]),
    ]

    ring_radius = 0.8
    orbit_z_positions = [-3.0, -1.0, 1.0, 3.0]
    n_orbit_levels = 4

    node_size = 120
    all_node_positions = {}  # (tape, orbit_step, cell) -> (x,y,z)

    # Draw cells as colored spheres at each orbit level
    for t_idx, (tc, t_color) in enumerate(zip(tape_centers, TAPE_COLORS)):
        for o_idx, (orbit_state, o_label) in enumerate(zip(ORBIT, ORBIT_LABELS)):
            z_level = orbit_z_positions[o_idx]

            # Draw ring of 5 nodes
            angles = np.linspace(0, 2 * np.pi, n_cells, endpoint=False)
            for c_idx, (angle, val) in enumerate(zip(angles, orbit_state)):
                x = tc[0] + ring_radius * np.cos(angle)
                y = tc[1] + ring_radius * np.sin(angle)
                z = z_level
                all_node_positions[(t_idx, o_idx, c_idx)] = (x, y, z)

                node_col = z7_node_color(val)
                ax.scatter(x, y, z, c=node_col, s=node_size,
                           edgecolors=t_color, linewidths=1.5,
                           zorder=10, alpha=0.95)
                # Label the Z7 value
                ax.text(x, y, z + 0.15, str(val), fontsize=5.5,
                        ha="center", va="bottom", color=t_color,
                        fontweight="bold", zorder=11)

            # Draw ring outline
            ring_angles = np.linspace(0, 2 * np.pi, 60)
            rx = tc[0] + ring_radius * np.cos(ring_angles)
            ry = tc[1] + ring_radius * np.sin(ring_angles)
            rz = np.full_like(rx, z_level)
            ax.plot(rx, ry, rz, color=t_color, alpha=0.35, linewidth=1.0, linestyle="--")

            # Orbit step label
            if t_idx == 0:
                ax.text(tc[0] - ring_radius - 0.3, tc[1], z_level,
                        o_label, fontsize=9, color="#cccccc",
                        ha="right", va="center", fontweight="bold")

    # Draw within-tape orbit progression arrows (GEN1→GEN2→GEN3→VAC)
    for t_idx, (tc, t_color) in enumerate(zip(tape_centers, TAPE_COLORS)):
        for o_idx in range(n_orbit_levels - 1):
            z0 = orbit_z_positions[o_idx]
            z1 = orbit_z_positions[o_idx + 1]
            # Arrow from center of orbit ring at z0 to z1
            cx, cy = tc[0], tc[1]
            ax.quiver(cx, cy, z0, 0, 0, z1 - z0,
                      color=t_color, alpha=0.8, linewidth=2.0,
                      arrow_length_ratio=0.25, length=1.0)

    # Draw cross-tape DPP coupling arrows (at each orbit level)
    dpp_color = "#aaaaaa"
    dpp_alpha = 0.4
    for o_idx in range(n_orbit_levels):
        z_level = orbit_z_positions[o_idx]
        # Connect tape 0 -> tape 1 -> tape 2 -> tape 0
        connections = [(0, 1), (1, 2), (2, 0)]
        for src, dst in connections:
            src_c = tape_centers[src]
            dst_c = tape_centers[dst]
            # Midpoint arrow
            mx = (src_c[0] + dst_c[0]) / 2
            my = (src_c[1] + dst_c[1]) / 2
            dx = dst_c[0] - src_c[0]
            dy = dst_c[1] - src_c[1]
            ax.plot([src_c[0], dst_c[0]], [src_c[1], dst_c[1]], [z_level, z_level],
                    color=dpp_color, alpha=dpp_alpha, linewidth=0.8,
                    linestyle=":", zorder=5)

    # Tape identity labels
    for t_idx, (tc, t_color, t_label) in enumerate(zip(tape_centers, TAPE_COLORS, TAPE_LABELS)):
        ax.text(tc[0], tc[1], orbit_z_positions[-1] + 0.9, t_label,
                fontsize=11, color=t_color, ha="center", va="bottom",
                fontweight="bold", zorder=20)

    # DPP coupling legend
    ax.text2D(0.05, 0.08,
              "─── within-tape orbit progression\n"
              "···  cross-tape DPP coupling (τ_c^out)\n"
              "●    Z₇ cell value (color = sector)",
              transform=ax.transAxes,
              fontsize=8, color="#aaaaaa",
              va="bottom", ha="left",
              bbox=dict(facecolor="#111122", alpha=0.7, boxstyle="round,pad=0.4", edgecolor="#445566"))

    # Z7 color legend
    legend_x = 0.78
    legend_y = 0.08
    for val in range(7):
        rect = mpatches.Patch(facecolor=Z7_COLORS[val], edgecolor="#666666",
                              linewidth=0.8, label=f"{val} = {Z7_NAMES[val]}")
    ax.text2D(legend_x, legend_y + 0.30, "Z₇ sectors:", transform=ax.transAxes,
              fontsize=8, color="#cccccc", fontweight="bold")
    for val in range(7):
        ax.text2D(legend_x, legend_y + 0.25 - val * 0.035,
                  f"  ■ {val} = {Z7_NAMES[val]}",
                  transform=ax.transAxes, fontsize=7.5,
                  color=Z7_COLORS[val] if val != 0 else "#888888",
                  fontweight="bold" if val > 0 else "normal")

    ax.set_title("Three-Tape DPP: GEN₁³ → GEN₂³ → GEN₃³ → VAC³",
                 color="white", fontsize=14, fontweight="bold", pad=10)

    ax.set_xlabel("x", color="#888888", fontsize=8)
    ax.set_ylabel("y", color="#888888", fontsize=8)
    ax.set_zlabel("orbit step (τ)", color="#888888", fontsize=8)
    ax.tick_params(colors="#555566", labelsize=6)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor("#1a1a2e")
    ax.yaxis.pane.set_edgecolor("#1a1a2e")
    ax.zaxis.pane.set_edgecolor("#1a1a2e")
    ax.grid(True, color="#1e1e3a", alpha=0.5, linewidth=0.5)

    ax.view_init(elev=22, azim=-55)

    out_path = FIGURES_DIR / "p49_three_tape_dpp_v3.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight",
                facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)
    size = out_path.stat().st_size
    print(f"Figure 1 saved: {out_path} ({size:,} bytes)")
    return out_path


# ---------------------------------------------------------------------------
# Figure 2: Generation orbit spacetime 3D
# ---------------------------------------------------------------------------
def figure2_three_tape_orbit_3d():
    """3D spacetime: x=cell_position, y=time_step, z=tape_index."""
    fig = plt.figure(figsize=(13, 10), facecolor=BG_COLOR)
    ax = fig.add_subplot(111, projection="3d", facecolor=BG_COLOR)
    fig.patch.set_facecolor(BG_COLOR)

    # axes: x=cell_position (0-4), y=orbit_step (0=GEN1,...,3=VAC), z=tape (0,1,2)
    n_cells = 5
    n_steps = 4
    n_tapes = 3

    # Scatter: each point is (cell, step, tape) with color = Z7 value
    for tape_idx in range(n_tapes):
        for step_idx, orbit_state in enumerate(ORBIT):
            for cell_idx, val in enumerate(orbit_state):
                x = float(cell_idx)
                y = float(step_idx)
                z = float(tape_idx)
                col = z7_node_color(val)
                edge_col = TAPE_COLORS[tape_idx]

                size = 200 + val * 40  # larger sphere for higher Z7 values
                ax.scatter(x, y, z, c=col, s=size,
                           edgecolors=edge_col, linewidths=1.8,
                           zorder=10, alpha=0.92)

                # Value label
                if val > 0:
                    ax.text(x, y, z + 0.08, str(val), fontsize=7,
                            ha="center", va="bottom",
                            color=col if val != 1 else "#aaaaaa",
                            fontweight="bold", zorder=11)

    # Connect cells within same tape+step (ring connections)
    for tape_idx in range(n_tapes):
        for step_idx, orbit_state in enumerate(ORBIT):
            for cell_idx in range(n_cells):
                x0, y0, z0 = float(cell_idx), float(step_idx), float(tape_idx)
                x1, y1, z1 = float((cell_idx + 1) % n_cells), float(step_idx), float(tape_idx)
                ax.plot([x0, x1], [y0, y1], [z0, z1],
                        color=TAPE_COLORS[tape_idx], alpha=0.25, linewidth=0.8, linestyle="--")

    # Connect each cell through orbit time (within tape)
    for tape_idx in range(n_tapes):
        for cell_idx in range(n_cells):
            for step_idx in range(n_steps - 1):
                x = float(cell_idx)
                y0 = float(step_idx)
                y1 = float(step_idx + 1)
                z = float(tape_idx)
                ax.plot([x, x], [y0, y1], [z, z],
                        color=TAPE_COLORS[tape_idx], alpha=0.6, linewidth=1.2)

    # Cross-tape DPP coupling edges (same cell, same step, different tape) 
    for step_idx in range(n_steps):
        for cell_idx in range(n_cells):
            for ta, tb in [(0, 1), (1, 2)]:
                x = float(cell_idx)
                y = float(step_idx)
                ax.plot([x, x], [y, y], [float(ta), float(tb)],
                        color="#ffffff", alpha=0.18, linewidth=0.7, linestyle=":")

    # Axis labels and tick overrides
    ax.set_xlabel("cell position (i)", color="#99aacc", fontsize=10, labelpad=8)
    ax.set_ylabel("orbit step (τ)", color="#99aacc", fontsize=10, labelpad=8)
    ax.set_zlabel("tape (dim)", color="#99aacc", fontsize=10, labelpad=8)

    ax.set_xticks(range(n_cells))
    ax.set_xticklabels([str(i) for i in range(n_cells)], fontsize=8, color="#778899")
    ax.set_yticks(range(n_steps))
    ax.set_yticklabels(ORBIT_LABELS, fontsize=8, color="#778899")
    ax.set_zticks(range(n_tapes))
    ax.set_zticklabels(TAPE_LABELS, fontsize=9, color="#778899")

    ax.tick_params(colors="#556677", labelsize=7)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor("#1a1a2e")
    ax.yaxis.pane.set_edgecolor("#1a1a2e")
    ax.zaxis.pane.set_edgecolor("#1a1a2e")
    ax.grid(True, color="#1e1e3a", alpha=0.4, linewidth=0.5)
    ax.view_init(elev=20, azim=40)

    ax.set_title("Three-Tape GEN Orbit: Z₇ Spacetime (cell × orbit-step × tape)",
                 color="white", fontsize=13, fontweight="bold", pad=12)

    # Z7 legend
    for val in range(7):
        ax.text2D(0.02, 0.78 - val * 0.045, f"■ {val}: {Z7_NAMES[val]}",
                  transform=ax.transAxes, fontsize=8,
                  color=Z7_COLORS[val] if val != 0 else "#666666",
                  fontweight="bold" if val > 0 else "normal")

    out_path = FIGURES_DIR / "p49_three_tape_orbit_3d.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight",
                facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)
    size = out_path.stat().st_size
    print(f"Figure 2 saved: {out_path} ({size:,} bytes)")
    return out_path


# ---------------------------------------------------------------------------
# Figure 3: DPP clock coupling diagram (schematic)
# ---------------------------------------------------------------------------
def figure3_dpp_clock_diagram():
    """Clean schematic: three tapes sharing tau_c^out, each with tau_c^in."""
    fig, ax = plt.subplots(figsize=(12, 8), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.set_xlim(-0.5, 11)
    ax.set_ylim(-1.0, 8.5)
    ax.axis("off")

    # Layout:
    # Shared outer clock at top center
    # Three tape boxes in a row
    # DPP coupling arrows from shared clock to each tape
    # Within each tape: inner clock -> outer clock

    shared_clock_pos = (5.0, 7.5)
    tape_positions = [(1.5, 3.5), (5.0, 3.5), (8.5, 3.5)]

    box_w, box_h = 2.2, 2.8
    inner_clock_pos = [(tp[0], tp[1] - 0.7) for tp in tape_positions]
    outer_clock_pos = [(tp[0], tp[1] + 0.5) for tp in tape_positions]

    def draw_box(ax, cx, cy, w, h, color, label, sublabel=None, alpha=0.85):
        rect = FancyBboxPatch(
            (cx - w / 2, cy - h / 2), w, h,
            boxstyle="round,pad=0.12",
            facecolor="#111128", edgecolor=color,
            linewidth=2.0, alpha=alpha, zorder=5
        )
        ax.add_patch(rect)
        ax.text(cx, cy + 0.3, label, ha="center", va="center",
                fontsize=13, color=color, fontweight="bold", zorder=10)
        if sublabel:
            ax.text(cx, cy - 0.25, sublabel, ha="center", va="center",
                    fontsize=9, color="#aaaacc", zorder=10)

    def draw_clock(ax, cx, cy, color, label, r=0.45):
        circle = Circle((cx, cy), r, facecolor="#0d0d22", edgecolor=color,
                         linewidth=2.0, zorder=8)
        ax.add_patch(circle)
        # Clock hands
        ax.plot([cx, cx], [cy, cy + r * 0.7], color=color, linewidth=1.5, zorder=9)
        ax.plot([cx, cx + r * 0.5], [cy, cy], color=color, linewidth=1.5, zorder=9)
        ax.text(cx, cy - r - 0.15, label, ha="center", va="top",
                fontsize=9, color=color, fontweight="bold", zorder=10)

    def draw_arrow(ax, x0, y0, x1, y1, color, label=None, linestyle="-"):
        dx, dy = x1 - x0, y1 - y0
        ax.annotate("",
                    xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(
                        arrowstyle="-|>",
                        color=color,
                        lw=2.0,
                        connectionstyle="arc3,rad=0.0",
                    ),
                    zorder=6)
        if label:
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            ax.text(mx + 0.15, my, label, ha="left", va="center",
                    fontsize=8, color=color, fontstyle="italic", zorder=11)

    # Draw shared outer clock
    draw_clock(ax, shared_clock_pos[0], shared_clock_pos[1], "#ffffff",
               "τ_c^out (shared)", r=0.6)
    ax.text(shared_clock_pos[0], shared_clock_pos[1] + 1.0,
            "Shared Outer Clock", ha="center", va="bottom",
            fontsize=12, color="#ccddff", fontweight="bold")
    ax.text(shared_clock_pos[0], shared_clock_pos[1] + 0.75,
            "(Dimensional Protocol Principle)", ha="center", va="bottom",
            fontsize=9, color="#8899bb", fontstyle="italic")

    # Draw three tape boxes
    for t_idx, (tp, t_color, t_label) in enumerate(zip(tape_positions, TAPE_COLORS, TAPE_LABELS)):
        # Main tape box
        draw_box(ax, tp[0], tp[1], box_w, box_h, t_color, t_label,
                 sublabel=f"Z₇ CA: p(L,C,R)")

        # Inner clock
        draw_clock(ax, tp[0], tp[1] - 1.0, t_color, "τ_c^in", r=0.30)

        # Arrow: inner clock -> outer clock (within tape)
        ax.annotate("",
                    xy=(tp[0], tp[1] - 0.3), xytext=(tp[0], tp[1] - 0.68),
                    arrowprops=dict(arrowstyle="-|>", color=t_color, lw=1.5),
                    zorder=6)

        # Arrow: shared clock -> this tape's outer position
        ax.annotate("",
                    xy=(tp[0], tp[1] + box_h / 2 + 0.1),
                    xytext=(shared_clock_pos[0], shared_clock_pos[1] - 0.65),
                    arrowprops=dict(
                        arrowstyle="-|>",
                        color="#ffffff",
                        lw=1.8,
                        linestyle="dashed",
                        connectionstyle=f"arc3,rad={0.2 * (t_idx - 1):.2f}",
                    ),
                    zorder=6)

        # GEN orbit annotation below tape box
        ax.text(tp[0], tp[1] - box_h / 2 - 0.5,
                "GEN₁→GEN₂→GEN₃→VAC",
                ha="center", va="top",
                fontsize=8.5, color=t_color, fontstyle="italic")

    # DPP coupling annotation
    ax.annotate("",
                xy=(tape_positions[1][0] - box_w / 2 - 0.05, tape_positions[1][1]),
                xytext=(tape_positions[0][0] + box_w / 2 + 0.05, tape_positions[0][1]),
                arrowprops=dict(arrowstyle="<->", color="#888888", lw=1.5, linestyle="dotted"),
                zorder=6)
    ax.annotate("",
                xy=(tape_positions[2][0] - box_w / 2 - 0.05, tape_positions[2][1]),
                xytext=(tape_positions[1][0] + box_w / 2 + 0.05, tape_positions[1][1]),
                arrowprops=dict(arrowstyle="<->", color="#888888", lw=1.5, linestyle="dotted"),
                zorder=6)

    # Cross-tape coupling label
    ax.text(5.0, 3.5, "p(wₓ,w_y,w_z)/6\ncross-tape coupling",
            ha="center", va="center", fontsize=7.5,
            color="#888888", fontstyle="italic",
            bbox=dict(facecolor=BG_COLOR, alpha=0.8, boxstyle="round,pad=0.3",
                      edgecolor="#444466"))

    # Key identity box at bottom
    identity_text = (
        "Shared τ_c^out  ⟹  3 spatial dims + 1 time dim  (3+1D)\n"
        "Ricci-flat vacuum: p(1,1,1) = 0    |    Gravitationally active: p(w,w,w) ≠ 0  for w = gen. value\n"
        "DPP (Dimensional Protocol Principle, CatAL) — Lean-certified: three_tape_gorard_vacuum_ricci_flat"
    )
    ax.text(5.0, -0.7, identity_text, ha="center", va="center",
            fontsize=8, color="#aabbcc",
            bbox=dict(facecolor="#0d1120", alpha=0.9, boxstyle="round,pad=0.5",
                      edgecolor="#334466"))

    ax.set_title("DPP Architecture: Three Z₇ Tapes with Shared Clock → 3+1D",
                 fontsize=15, color="white", fontweight="bold", pad=15)

    out_path = FIGURES_DIR / "p49_dpp_clock_diagram.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight",
                facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)
    size = out_path.stat().st_size
    print(f"Figure 3 saved: {out_path} ({size:,} bytes)")
    return out_path


# ---------------------------------------------------------------------------
# Figure 4: Three-tape causal layered graph
# ---------------------------------------------------------------------------
def figure4_three_tape_causal_layered():
    """Time-layered causal graph for three tapes side by side with DPP connections."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 10), facecolor=BG_COLOR)
    fig.patch.set_facecolor(BG_COLOR)

    n_cells = 5
    n_steps = 4
    x_spread = 1.2  # horizontal spread between cells

    # Compute causal connections: cell i at step t connects to affected cells at step t+1
    # Under the GTE rule p(L,C,R), cell i+1 at t+1 depends on cells i-1, i, i+1 at t
    # So causal parents of cell j at step t+1 are cells j-1, j, j+1 at step t

    def causal_parents(j, n):
        """Returns list of cell indices at step t that causally affect cell j at t+1."""
        return [(j - 1) % n, j, (j + 1) % n]

    # For each tape, draw the layered graph
    for t_idx, (ax, t_color, t_label) in enumerate(zip(axes, TAPE_COLORS, TAPE_LABELS)):
        ax.set_facecolor(BG_COLOR)
        ax.set_xlim(-0.5, (n_cells - 1) * x_spread + 0.5)
        ax.set_ylim(-0.5, n_steps + 0.3)
        ax.axis("off")

        # Draw nodes and causal edges
        for step_idx, orbit_state in enumerate(ORBIT):
            y = float(n_steps - 1 - step_idx)  # top = GEN1, bottom = VAC
            for cell_idx, val in enumerate(orbit_state):
                x = cell_idx * x_spread
                # Draw node
                col = z7_node_color(val)
                circle = Circle((x, y), 0.25, facecolor=col,
                                 edgecolor=t_color, linewidth=1.5, zorder=10)
                ax.add_patch(circle)
                # Value label
                label_color = "#000000" if val in (1, 4) else "#ffffff"
                ax.text(x, y, str(val), ha="center", va="center",
                        fontsize=9, color=label_color, fontweight="bold", zorder=11)

            # Draw causal edges from this step to next
            if step_idx < n_steps - 1:
                y_next = float(n_steps - 2 - step_idx)
                for j in range(n_cells):
                    x_dst = j * x_spread
                    for parent in causal_parents(j, n_cells):
                        x_src = parent * x_spread
                        ax.annotate("",
                                    xy=(x_dst, y_next + 0.27),
                                    xytext=(x_src, y - 0.27),
                                    arrowprops=dict(
                                        arrowstyle="-|>",
                                        color=t_color,
                                        alpha=0.35,
                                        lw=0.9,
                                        connectionstyle="arc3,rad=0.0",
                                    ),
                                    zorder=5)

        # Step labels on left
        for step_idx, label in enumerate(ORBIT_LABELS):
            y = float(n_steps - 1 - step_idx)
            ax.text(-0.45, y, label, ha="right", va="center",
                    fontsize=9, color="#cccccc", fontweight="bold")

        # Cell index labels at bottom
        for cell_idx in range(n_cells):
            x = cell_idx * x_spread
            ax.text(x, -0.4, f"c{cell_idx}", ha="center", va="top",
                    fontsize=8, color="#778899")

        ax.set_title(t_label, color=t_color, fontsize=13, fontweight="bold", pad=4)

    # Add DPP cross-tape coupling indicators between sub-panels
    # (text annotation at the top of the figure)
    fig.text(0.5, 0.96,
             "Three-Tape GEN Orbit Causal Graph  (arrows = causal influence under p mod 7)",
             ha="center", va="top", fontsize=14, color="white", fontweight="bold")
    fig.text(0.5, 0.92,
             "Cross-tape DPP coupling: τ_c^out shared  ←→  all three tapes evolve in lockstep",
             ha="center", va="top", fontsize=10, color="#aabbcc", fontstyle="italic")

    # Draw cross-tape DPP bridge lines in figure space (between panels)
    # Subtle horizontal lines connecting the three panels at each orbit step
    for step_idx in range(n_steps):
        y_frac = 0.15 + step_idx * 0.18  # rough vertical position in figure
        fig.add_artist(plt.Line2D(
            [0.38, 0.62], [y_frac, y_frac],
            transform=fig.transFigure,
            color="#555588", linewidth=0.8, linestyle=":",
            alpha=0.6
        ))
        fig.add_artist(plt.Line2D(
            [0.62, 0.93], [y_frac, y_frac],
            transform=fig.transFigure,
            color="#555588", linewidth=0.8, linestyle=":",
            alpha=0.6
        ))

    plt.tight_layout(rect=[0, 0, 1, 0.90])

    out_path = FIGURES_DIR / "p49_three_tape_causal_layered.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight",
                facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)
    size = out_path.stat().st_size
    print(f"Figure 4 saved: {out_path} ({size:,} bytes)")
    return out_path


# ---------------------------------------------------------------------------
# Figure 5: Combined headline figure for the paper
# ---------------------------------------------------------------------------
def figure5_combined_headline():
    """Two-panel: left=single-tape spacetime (loaded from file), right=three-tape DPP orbit."""
    fig = plt.figure(figsize=(18, 9), facecolor=BG_COLOR)
    fig.patch.set_facecolor(BG_COLOR)

    # Left panel: load existing spacetime image
    left_path = FIGURES_DIR / "p49_gte_spacetime_perturbed_v2.png"
    ax_left = fig.add_subplot(1, 2, 1)
    ax_left.set_facecolor(BG_COLOR)

    if left_path.exists():
        img = plt.imread(str(left_path))
        ax_left.imshow(img, interpolation="lanczos")
    else:
        # Fallback: generate a simple spacetime diagram
        ax_left.set_facecolor(BG_COLOR)
        ax_left.text(0.5, 0.5, "Z₇ Spacetime\n(ether background +\nGEN orbit injection)",
                     ha="center", va="center", transform=ax_left.transAxes,
                     fontsize=14, color="white")

    ax_left.axis("off")
    ax_left.set_title("(a) Single-Tape: Z₇ Spacetime Diagram",
                      color="white", fontsize=12, fontweight="bold", pad=6)

    # Right panel: three-tape DPP orbit (3D matplotlib)
    ax_right = fig.add_subplot(1, 2, 2, projection="3d")
    ax_right.set_facecolor(BG_COLOR)

    tape_centers = [
        np.array([0.0, 0.0]),
        np.array([4.0, 0.0]),
        np.array([2.0, 3.46]),
    ]
    ring_radius = 0.9
    orbit_z_positions = [-3.0, -1.0, 1.0, 3.0]
    n_cells = 5
    node_size = 100

    for t_idx, (tc, t_color) in enumerate(zip(tape_centers, TAPE_COLORS)):
        for o_idx, (orbit_state, o_label) in enumerate(zip(ORBIT, ORBIT_LABELS)):
            z_level = orbit_z_positions[o_idx]
            angles = np.linspace(0, 2 * np.pi, n_cells, endpoint=False)
            for c_idx, (angle, val) in enumerate(zip(angles, orbit_state)):
                x = tc[0] + ring_radius * np.cos(angle)
                y = tc[1] + ring_radius * np.sin(angle)
                z = z_level
                node_col = z7_node_color(val)
                ax_right.scatter(x, y, z, c=node_col, s=node_size,
                                  edgecolors=t_color, linewidths=1.5, zorder=10, alpha=0.92)
                if val > 0:
                    ax_right.text(x, y, z + 0.12, str(val), fontsize=5,
                                   ha="center", va="bottom", color=t_color,
                                   fontweight="bold", zorder=11)

            # Ring outline
            ring_angles = np.linspace(0, 2 * np.pi, 60)
            rx = tc[0] + ring_radius * np.cos(ring_angles)
            ry = tc[1] + ring_radius * np.sin(ring_angles)
            rz = np.full_like(rx, z_level)
            ax_right.plot(rx, ry, rz, color=t_color, alpha=0.3, linewidth=0.8, linestyle="--")

        # Tape orbit arrow
        for o_idx in range(3):
            z0 = orbit_z_positions[o_idx]
            z1 = orbit_z_positions[o_idx + 1]
            ax_right.quiver(tc[0], tc[1], z0, 0, 0, z1 - z0,
                             color=t_color, alpha=0.75, linewidth=1.5,
                             arrow_length_ratio=0.25, length=1.0)

        # Tape label
        ax_right.text(tc[0], tc[1], orbit_z_positions[-1] + 0.7,
                       TAPE_LABELS[t_idx], fontsize=9.5, color=t_color,
                       ha="center", va="bottom", fontweight="bold", zorder=20)

    # Cross-tape DPP coupling
    for o_idx in range(4):
        z_level = orbit_z_positions[o_idx]
        for src, dst in [(0, 1), (1, 2), (2, 0)]:
            sc, dc = tape_centers[src], tape_centers[dst]
            ax_right.plot([sc[0], dc[0]], [sc[1], dc[1]], [z_level, z_level],
                           color="#888888", alpha=0.25, linewidth=0.7, linestyle=":")

    ax_right.set_title("(b) Three-Tape DPP: GEN₁³→GEN₂³→GEN₃³→VAC³",
                       color="white", fontsize=12, fontweight="bold", pad=6)
    ax_right.set_xlabel("x", color="#888888", fontsize=7)
    ax_right.set_ylabel("y", color="#888888", fontsize=7)
    ax_right.set_zlabel("orbit step τ", color="#888888", fontsize=7)
    ax_right.tick_params(colors="#555566", labelsize=5)
    ax_right.xaxis.pane.fill = False
    ax_right.yaxis.pane.fill = False
    ax_right.zaxis.pane.fill = False
    ax_right.xaxis.pane.set_edgecolor("#1a1a2e")
    ax_right.yaxis.pane.set_edgecolor("#1a1a2e")
    ax_right.zaxis.pane.set_edgecolor("#1a1a2e")
    ax_right.grid(True, color="#1e1e3a", alpha=0.4, linewidth=0.5)
    ax_right.view_init(elev=22, azim=-55)

    fig.suptitle(
        "GTE Z₇ CA: From Single-Tape Rule 110 to Three-Tape 3+1D Spacetime (DPP)",
        color="white", fontsize=14, fontweight="bold", y=0.99
    )

    plt.tight_layout(rect=[0, 0, 1, 0.97])

    out_path = FIGURES_DIR / "p49_paper_fig2_combined.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight",
                facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)
    size = out_path.stat().st_size
    print(f"Figure 5 saved: {out_path} ({size:,} bytes)")
    return out_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    print("=" * 60)
    print("Three-tape DPP visualization suite")
    print("=" * 60)

    results = []

    print("\n--- Figure 1: Three-tape DPP orbit v3 ---")
    p = figure1_three_tape_dpp_v3()
    results.append(p)

    print(f"\n--- Figure 2: Generation orbit 3D spacetime --- [{time.time()-t0:.1f}s]")
    p = figure2_three_tape_orbit_3d()
    results.append(p)

    print(f"\n--- Figure 3: DPP clock coupling diagram --- [{time.time()-t0:.1f}s]")
    p = figure3_dpp_clock_diagram()
    results.append(p)

    print(f"\n--- Figure 4: Three-tape causal layered graph --- [{time.time()-t0:.1f}s]")
    p = figure4_three_tape_causal_layered()
    results.append(p)

    print(f"\n--- Figure 5: Combined headline figure --- [{time.time()-t0:.1f}s]")
    p = figure5_combined_headline()
    results.append(p)

    signal.alarm(0)

    print("\n" + "=" * 60)
    print("All figures generated:")
    for path in results:
        size = path.stat().st_size
        print(f"  {path.name}: {size:,} bytes ({size // 1024} KB)")
    print(f"Total elapsed: {time.time()-t0:.1f}s")
    print("=" * 60)

    return results


if __name__ == "__main__":
    main()
