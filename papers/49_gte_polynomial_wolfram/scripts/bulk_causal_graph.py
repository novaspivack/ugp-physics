#!/usr/bin/env python3
"""
bulk_causal_graph.py — Combined three-tape DPP bulk causal graph.

Computes and visualizes the causal dependency graph of the full three-tape DPP
bulk dynamics: events (cell, tape, time) with BOTH within-tape and cross-tape
(gravitational) causal edges explicitly rendered.

Key distinction from the WolframModel encoding in wolfram_model_causal_graph.wl:
  That script uses WolframModel with independent tape rules → three disconnected
  fractal binary trees (no cross-tape edges). This reflects that DPP coupling is
  synchronic (shared clock), not embedded in WolframModel hyperedge rewriting.

  This script directly encodes the physical causal structure:
    - Within-tape edges: (j±1 mod 5, α, t) → (j, α, t+1) via p(L,C,R) mod 7
    - Cross-tape edges:  (j, β, t) → (j, α, t+1) for β ≠ α via gravitational
      sourcing p(wx, wy, wz)/6

This makes visible the 3+1D causal connectivity that distinguishes the coupled
three-tape bulk from three independent 1D systems.

Output figures:
  p49_bulk_causal_3d.png         — Full 3D causal graph (within + cross-tape)
  p49_bulk_causal_cross_tape.png — Cross-tape edges only (gravitational links)
  p49_bulk_causal_slices.png     — Time-slice causal structure (3 subplots)
  p49_causal_comparison.png      — Independent trees vs. coupled bulk

GEN orbit (Lean-certified, CatAL):
  GEN1 = [1,5,2,2,1], GEN2 = [2,5,2,0,2], GEN3 = [5,6,5,3,5], VAC = [0,0,0,0,0]
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
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

TIMEOUT_SECONDS = 300
SCRIPT_DIR = Path(__file__).resolve().parent
FIGURES_DIR = SCRIPT_DIR / "figures"

# Z7 color map
Z7_COLORS = {
    0: "#111111",  # VAC
    1: "#f8f8f8",  # ether (white)
    2: "#ff2222",  # up-quark
    3: "#ff8800",  # W-boson
    4: "#ffff00",  # down-quark
    5: "#00e5ff",  # strange / νR
    6: "#ff00ff",  # electron
}
Z7_NAMES = {0: "VAC", 1: "ether", 2: "u", 3: "W", 4: "d", 5: "s/νR", 6: "e⁻"}

# GEN orbit (t=0..3)
GEN_ORBIT = [
    [1, 5, 2, 2, 1],  # t=0: GEN1
    [2, 5, 2, 0, 2],  # t=1: GEN2
    [5, 6, 5, 3, 5],  # t=2: GEN3
    [0, 0, 0, 0, 0],  # t=3: VAC
]
ORBIT_LABELS = ["GEN₁", "GEN₂", "GEN₃", "VAC"]

N_CELLS = 5
N_TAPES = 3
N_STEPS = 4  # t = 0, 1, 2, 3

TAPE_COLORS = ["#ff5555", "#55ff99", "#5599ff"]  # x, y, z
TAPE_NAMES  = ["x-tape", "y-tape", "z-tape"]

BG_COLOR = "#0a0a14"


def _timeout_handler(_signum, _frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)


# ---------------------------------------------------------------------------
# Event and causal edge computation
# ---------------------------------------------------------------------------

def event_id(cell: int, tape: int, step: int) -> int:
    """Linearized event index: 0 .. N_CELLS*N_TAPES*N_STEPS - 1."""
    return step * (N_CELLS * N_TAPES) + tape * N_CELLS + cell


def event_coords(cell: int, tape: int, step: int) -> tuple[float, float, float]:
    """3D position: x=cell, y=tape, z=step."""
    return float(cell), float(tape), float(step)


def get_orbit_value(cell: int, tape: int, step: int) -> int:
    """Z7 value at event (cell, tape, step); all tapes identical (symmetric orbit)."""
    return GEN_ORBIT[step][cell]


def compute_causal_edges() -> tuple[list, list, int, int]:
    """
    Returns (within_tape_edges, cross_tape_edges, n_within, n_cross).

    For each target event (j, α, t+1) with t ∈ {0,1,2}:
      Within-tape: (j-1 mod N, α, t) → (j, α, t+1)
                   (j,         α, t) → (j, α, t+1)
                   (j+1 mod N, α, t) → (j, α, t+1)
      Cross-tape:  (j, β, t) → (j, α, t+1)  for each β ≠ α
    """
    within_edges: list[tuple[int, int, int, int, int, int]] = []
    cross_edges:  list[tuple[int, int, int, int, int, int]] = []

    for t in range(N_STEPS - 1):
        for alpha in range(N_TAPES):
            for j in range(N_CELLS):
                # Within-tape edges: left, center, right neighbors
                for dj in (-1, 0, 1):
                    src_cell = (j + dj) % N_CELLS
                    within_edges.append((src_cell, alpha, t, j, alpha, t + 1))
                # Cross-tape edges
                for beta in range(N_TAPES):
                    if beta != alpha:
                        cross_edges.append((j, beta, t, j, alpha, t + 1))

    return within_edges, cross_edges, len(within_edges), len(cross_edges)


# ---------------------------------------------------------------------------
# Connectivity check
# ---------------------------------------------------------------------------

def is_connected(within_edges, cross_edges) -> bool:
    """Check if the combined causal graph is connected (ignoring edge direction)."""
    from collections import defaultdict, deque

    adj: dict[tuple, set] = defaultdict(set)
    for sc, st, ss, dc, dt, ds in within_edges + cross_edges:
        src = (sc, st, ss)
        dst = (dc, dt, ds)
        adj[src].add(dst)
        adj[dst].add(src)

    all_events = {(c, t, s) for s in range(N_STEPS) for t in range(N_TAPES) for c in range(N_CELLS)}
    start = next(iter(all_events))
    visited = {start}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for nb in adj[node]:
            if nb not in visited:
                visited.add(nb)
                queue.append(nb)
    return len(visited) == len(all_events)


# ---------------------------------------------------------------------------
# Figure 1: Full 3D causal graph
# ---------------------------------------------------------------------------

def figure1_full_3d_causal_graph(within_edges, cross_edges):
    """Full 3D causal graph: blue=within-tape, red=cross-tape edges."""
    fig = plt.figure(figsize=(14, 14), facecolor=BG_COLOR, dpi=200)
    ax = fig.add_subplot(111, projection="3d", facecolor=BG_COLOR)
    fig.patch.set_facecolor(BG_COLOR)

    # --- Draw edges first (behind nodes) ---
    # Within-tape edges (solid blue)
    for sc, st, ss, dc, dt, ds in within_edges:
        x0, y0, z0 = event_coords(sc, st, ss)
        x1, y1, z1 = event_coords(dc, dt, ds)
        ax.plot([x0, x1], [y0, y1], [z0, z1],
                color="#3366ff", alpha=0.22, linewidth=0.6, zorder=1)

    # Cross-tape edges (dashed red/orange)
    for sc, st, ss, dc, dt, ds in cross_edges:
        x0, y0, z0 = event_coords(sc, st, ss)
        x1, y1, z1 = event_coords(dc, dt, ds)
        ax.plot([x0, x1], [y0, y1], [z0, z1],
                color="#ff4400", alpha=0.35, linewidth=0.8,
                linestyle="--", zorder=2)

    # --- Draw nodes ---
    for step in range(N_STEPS):
        for tape in range(N_TAPES):
            xs, ys, zs, cs, sizes = [], [], [], [], []
            for cell in range(N_CELLS):
                val = get_orbit_value(cell, tape, step)
                xs.append(float(cell))
                ys.append(float(tape))
                zs.append(float(step))
                cs.append(Z7_COLORS[val])
                sizes.append(160 if val > 0 else 80)
            ax.scatter(xs, ys, zs, c=cs, s=sizes,
                       edgecolors=TAPE_COLORS[tape], linewidths=1.2,
                       zorder=10, alpha=0.95, depthshade=False)
            # Value labels
            for cell in range(N_CELLS):
                val = get_orbit_value(cell, tape, step)
                ax.text(float(cell), float(tape), float(step) + 0.08,
                        str(val), fontsize=6, ha="center", va="bottom",
                        color=TAPE_COLORS[tape], fontweight="bold", zorder=11)

    # --- Axis labels ---
    ax.set_xlabel("Cell position (j)", color="#aaaaaa", fontsize=9, labelpad=8)
    ax.set_ylabel("Tape (x/y/z)", color="#aaaaaa", fontsize=9, labelpad=8)
    ax.set_zlabel("Orbit step (t)", color="#aaaaaa", fontsize=9, labelpad=8)

    ax.set_xticks(range(N_CELLS))
    ax.set_xticklabels([f"j={i}" for i in range(N_CELLS)], fontsize=6.5, color="#888888")
    ax.set_yticks(range(N_TAPES))
    ax.set_yticklabels(["x", "y", "z"], fontsize=8, color="#888888")
    ax.set_zticks(range(N_STEPS))
    ax.set_zticklabels(ORBIT_LABELS, fontsize=7.5, color="#bbbbbb")

    ax.xaxis.pane.fill = ax.yaxis.pane.fill = ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor("#1a1a2e")
    ax.yaxis.pane.set_edgecolor("#1a1a2e")
    ax.zaxis.pane.set_edgecolor("#1a1a2e")
    ax.grid(True, color="#1e1e3a", alpha=0.4, linewidth=0.4)
    ax.tick_params(colors="#555566", labelsize=6)
    ax.view_init(elev=25, azim=-50)

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor="#3366ff", edgecolor="none", label="Within-tape edges (p mod 7 local rule)"),
        mpatches.Patch(facecolor="#ff4400", edgecolor="none", label="Cross-tape edges (gravitational coupling)"),
        mpatches.Patch(facecolor=TAPE_COLORS[0], edgecolor="none", label="x-tape"),
        mpatches.Patch(facecolor=TAPE_COLORS[1], edgecolor="none", label="y-tape"),
        mpatches.Patch(facecolor=TAPE_COLORS[2], edgecolor="none", label="z-tape"),
    ]
    ax.legend(handles=legend_elements, loc="upper left",
              fontsize=8, framealpha=0.6,
              facecolor="#111122", edgecolor="#334455", labelcolor="white",
              bbox_to_anchor=(0.0, 0.98))

    ax.set_title(
        "Three-Tape DPP Bulk Causal Graph: GEN₁³ → VAC³\n"
        "(blue = within-tape, red = cross-tape gravitational coupling)",
        color="white", fontsize=12, fontweight="bold", pad=12
    )

    # Z7 sector legend
    for i, (val, name) in enumerate(Z7_NAMES.items()):
        ax.text2D(0.82, 0.80 - i * 0.055,
                  f"■ {val} = {name}",
                  transform=ax.transAxes, fontsize=7.5,
                  color=Z7_COLORS[val] if val != 0 else "#666666",
                  fontweight="bold")
    ax.text2D(0.82, 0.82, "Z₇ sectors:", transform=ax.transAxes,
              fontsize=8, color="#cccccc", fontweight="bold")

    out_path = FIGURES_DIR / "p49_bulk_causal_3d.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight",
                facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)
    size = out_path.stat().st_size
    print(f"Figure 1 saved: {out_path.name} ({size:,} bytes)")
    return out_path


# ---------------------------------------------------------------------------
# Figure 2: Cross-tape edges only
# ---------------------------------------------------------------------------

def figure2_cross_tape_only(cross_edges):
    """Cross-tape gravitational coupling edges only."""
    fig = plt.figure(figsize=(13, 13), facecolor=BG_COLOR, dpi=200)
    ax = fig.add_subplot(111, projection="3d", facecolor=BG_COLOR)
    fig.patch.set_facecolor(BG_COLOR)

    # Draw cross-tape edges with arrows
    for sc, st, ss, dc, dt, ds in cross_edges:
        x0, y0, z0 = event_coords(sc, st, ss)
        x1, y1, z1 = event_coords(dc, dt, ds)
        ax.plot([x0, x1], [y0, y1], [z0, z1],
                color="#ff6600", alpha=0.45, linewidth=1.0,
                linestyle="--", zorder=2)
        # Arrow tip
        ax.quiver(x0, y0, z0, x1 - x0, y1 - y0, z1 - z0,
                  color="#ff6600", alpha=0.5, length=0.9,
                  arrow_length_ratio=0.15, linewidth=0.5, zorder=3)

    # Draw nodes
    for step in range(N_STEPS):
        for tape in range(N_TAPES):
            xs, ys, zs, cs, sizes = [], [], [], [], []
            for cell in range(N_CELLS):
                val = get_orbit_value(cell, tape, step)
                xs.append(float(cell))
                ys.append(float(tape))
                zs.append(float(step))
                cs.append(Z7_COLORS[val])
                sizes.append(140 if val > 0 else 60)
            ax.scatter(xs, ys, zs, c=cs, s=sizes,
                       edgecolors=TAPE_COLORS[tape], linewidths=1.2,
                       zorder=10, alpha=0.90, depthshade=False)

    ax.set_xlabel("Cell position (j)", color="#aaaaaa", fontsize=9, labelpad=8)
    ax.set_ylabel("Tape (x/y/z)", color="#aaaaaa", fontsize=9, labelpad=8)
    ax.set_zlabel("Orbit step (t)", color="#aaaaaa", fontsize=9, labelpad=8)
    ax.set_xticks(range(N_CELLS))
    ax.set_xticklabels([f"j={i}" for i in range(N_CELLS)], fontsize=6.5, color="#888888")
    ax.set_yticks(range(N_TAPES))
    ax.set_yticklabels(["x", "y", "z"], fontsize=8, color="#888888")
    ax.set_zticks(range(N_STEPS))
    ax.set_zticklabels(ORBIT_LABELS, fontsize=7.5, color="#bbbbbb")
    ax.xaxis.pane.fill = ax.yaxis.pane.fill = ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor("#1a1a2e")
    ax.yaxis.pane.set_edgecolor("#1a1a2e")
    ax.zaxis.pane.set_edgecolor("#1a1a2e")
    ax.grid(True, color="#1e1e3a", alpha=0.4, linewidth=0.4)
    ax.tick_params(colors="#555566", labelsize=6)
    ax.view_init(elev=25, azim=-45)

    ax.set_title(
        "Three-Tape DPP: Cross-Tape Gravitational Causal Links Only\n"
        "(j, β, t) → (j, α, t+1) for β ≠ α — the 3+1D coupling that connects the tapes",
        color="white", fontsize=11, fontweight="bold", pad=12
    )

    legend_elements = [
        mpatches.Patch(facecolor="#ff6600", edgecolor="none",
                       label="Cross-tape coupling (j, β, t) → (j, α, t+1)"),
        mpatches.Patch(facecolor=TAPE_COLORS[0], edgecolor="none", label="x-tape"),
        mpatches.Patch(facecolor=TAPE_COLORS[1], edgecolor="none", label="y-tape"),
        mpatches.Patch(facecolor=TAPE_COLORS[2], edgecolor="none", label="z-tape"),
    ]
    ax.legend(handles=legend_elements, loc="upper left",
              fontsize=8, framealpha=0.6,
              facecolor="#111122", edgecolor="#334455", labelcolor="white")

    out_path = FIGURES_DIR / "p49_bulk_causal_cross_tape.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight",
                facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)
    size = out_path.stat().st_size
    print(f"Figure 2 saved: {out_path.name} ({size:,} bytes)")
    return out_path


# ---------------------------------------------------------------------------
# Figure 3: Time-slice causal structure
# ---------------------------------------------------------------------------

def figure3_time_slices(within_edges, cross_edges):
    """Three subplots: t=0→1, t=1→2, t=2→3 causal slices in 2D."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 7), facecolor=BG_COLOR)
    fig.patch.set_facecolor(BG_COLOR)

    src_step_transitions = [(0, 1), (1, 2), (2, 3)]

    for ax_idx, (t_src, t_dst) in enumerate(src_step_transitions):
        ax = axes[ax_idx]
        ax.set_facecolor(BG_COLOR)

        # Draw nodes at t_src (source row, y=1) and t_dst (destination row, y=0)
        y_src, y_dst = 1.0, 0.0
        node_radius = 0.18

        # Source nodes (t_src)
        for tape in range(N_TAPES):
            for cell in range(N_CELLS):
                val = get_orbit_value(cell, tape, t_src)
                x = cell + tape * 6.0  # 3 tapes spread horizontally
                col = Z7_COLORS[val]
                circ = plt.Circle((x, y_src), node_radius,
                                  facecolor=col, edgecolor=TAPE_COLORS[tape],
                                  linewidth=1.8, zorder=10)
                ax.add_patch(circ)
                label_col = "#000000" if val in (1, 4) else "#ffffff"
                ax.text(x, y_src, str(val), ha="center", va="center",
                        fontsize=8.5, color=label_col, fontweight="bold", zorder=11)
                ax.text(x, y_src + 0.28, f"c{cell}", ha="center", va="bottom",
                        fontsize=6.5, color=TAPE_COLORS[tape])

        # Destination nodes (t_dst)
        for tape in range(N_TAPES):
            for cell in range(N_CELLS):
                val = get_orbit_value(cell, tape, t_dst)
                x = cell + tape * 6.0
                col = Z7_COLORS[val]
                circ = plt.Circle((x, y_dst), node_radius,
                                  facecolor=col, edgecolor=TAPE_COLORS[tape],
                                  linewidth=1.8, zorder=10)
                ax.add_patch(circ)
                label_col = "#000000" if val in (1, 4) else "#ffffff"
                ax.text(x, y_dst, str(val), ha="center", va="center",
                        fontsize=8.5, color=label_col, fontweight="bold", zorder=11)

        # Draw within-tape edges for this slice
        slice_within = [(sc, st, ss, dc, dt, ds) for sc, st, ss, dc, dt, ds in within_edges
                        if ss == t_src and ds == t_dst]
        for sc, st, ss, dc, dt, ds in slice_within:
            x_src = sc + st * 6.0
            x_dst = dc + dt * 6.0
            ax.annotate("",
                        xy=(x_dst, y_dst + node_radius + 0.01),
                        xytext=(x_src, y_src - node_radius - 0.01),
                        arrowprops=dict(
                            arrowstyle="-|>",
                            color="#3366ff",
                            alpha=0.45,
                            lw=0.9,
                            connectionstyle="arc3,rad=0.05",
                        ),
                        zorder=5)

        # Draw cross-tape edges for this slice
        slice_cross = [(sc, st, ss, dc, dt, ds) for sc, st, ss, dc, dt, ds in cross_edges
                       if ss == t_src and ds == t_dst]
        for sc, st, ss, dc, dt, ds in slice_cross:
            x_src = sc + st * 6.0
            x_dst = dc + dt * 6.0
            ax.annotate("",
                        xy=(x_dst, y_dst + node_radius + 0.01),
                        xytext=(x_src, y_src - node_radius - 0.01),
                        arrowprops=dict(
                            arrowstyle="-|>",
                            color="#ff4400",
                            alpha=0.5,
                            lw=0.8,
                            linestyle="dashed",
                            connectionstyle="arc3,rad=0.15",
                        ),
                        zorder=4)

        # Tape labels
        for tape, (tc, tname) in enumerate(zip(TAPE_COLORS, TAPE_NAMES)):
            tape_cx = 2.0 + tape * 6.0
            ax.text(tape_cx, y_src + 0.55, tname, ha="center", va="bottom",
                    fontsize=9, color=tc, fontweight="bold")

        # Row labels
        ax.text(-0.8, y_src, ORBIT_LABELS[t_src], ha="right", va="center",
                fontsize=10, color="#cccccc", fontweight="bold")
        ax.text(-0.8, y_dst, ORBIT_LABELS[t_dst], ha="right", va="center",
                fontsize=10, color="#cccccc", fontweight="bold")

        ax.set_xlim(-1.2, 16.5)
        ax.set_ylim(-0.55, 1.55)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(f"Slice t={t_src}→{t_dst}\n({ORBIT_LABELS[t_src]}→{ORBIT_LABELS[t_dst]})",
                     color="white", fontsize=10, fontweight="bold")

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor="#3366ff", edgecolor="none", label="Within-tape (p mod 7 local)"),
        mpatches.Patch(facecolor="#ff4400", edgecolor="none", label="Cross-tape (gravitational coupling)"),
    ]
    for tc, tn in zip(TAPE_COLORS, TAPE_NAMES):
        legend_elements.append(mpatches.Patch(facecolor=tc, edgecolor="none", label=tn))
    fig.legend(handles=legend_elements, loc="lower center", ncol=5,
               fontsize=9, framealpha=0.6, facecolor="#111122",
               edgecolor="#334455", labelcolor="white",
               bbox_to_anchor=(0.5, 0.01))

    fig.suptitle(
        "Three-Tape DPP Bulk: Time-Slice Causal Structure\n"
        "Each slice shows causal edges from one orbit step to the next",
        color="white", fontsize=13, fontweight="bold", y=1.01
    )
    plt.tight_layout(rect=[0, 0.08, 1, 0.99])

    out_path = FIGURES_DIR / "p49_bulk_causal_slices.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight",
                facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)
    size = out_path.stat().st_size
    print(f"Figure 3 saved: {out_path.name} ({size:,} bytes)")
    return out_path


# ---------------------------------------------------------------------------
# Figure 4: Comparison — independent trees vs. coupled bulk
# ---------------------------------------------------------------------------

def figure4_comparison(within_edges, cross_edges):
    """Left=independent trees (no cross-tape), Right=coupled bulk (with cross-tape)."""
    fig = plt.figure(figsize=(22, 10), facecolor=BG_COLOR)
    fig.patch.set_facecolor(BG_COLOR)

    # ---- Left panel: three independent trees (no cross-tape edges) ----
    ax_l = fig.add_subplot(121, projection="3d", facecolor=BG_COLOR)

    # Within-tape edges only
    for sc, st, ss, dc, dt, ds in within_edges:
        x0, y0, z0 = event_coords(sc, st, ss)
        x1, y1, z1 = event_coords(dc, dt, ds)
        ax_l.plot([x0, x1], [y0, y1], [z0, z1],
                  color="#3366ff", alpha=0.30, linewidth=0.7, zorder=1)

    # Draw nodes
    for step in range(N_STEPS):
        for tape in range(N_TAPES):
            xs, ys, zs, cs, sizes = [], [], [], [], []
            for cell in range(N_CELLS):
                val = get_orbit_value(cell, tape, step)
                xs.append(float(cell))
                ys.append(float(tape))
                zs.append(float(step))
                cs.append(Z7_COLORS[val])
                sizes.append(130 if val > 0 else 60)
            ax_l.scatter(xs, ys, zs, c=cs, s=sizes,
                         edgecolors=TAPE_COLORS[tape], linewidths=1.0,
                         zorder=10, depthshade=False)

    ax_l.set_xlabel("Cell (j)", color="#888888", fontsize=8, labelpad=6)
    ax_l.set_ylabel("Tape", color="#888888", fontsize=8, labelpad=6)
    ax_l.set_zlabel("Orbit step", color="#888888", fontsize=8, labelpad=6)
    ax_l.set_xticks(range(N_CELLS))
    ax_l.set_xticklabels([str(i) for i in range(N_CELLS)], fontsize=6, color="#666666")
    ax_l.set_yticks(range(N_TAPES))
    ax_l.set_yticklabels(["x", "y", "z"], fontsize=7, color="#666666")
    ax_l.set_zticks(range(N_STEPS))
    ax_l.set_zticklabels(ORBIT_LABELS, fontsize=6.5, color="#999999")
    ax_l.xaxis.pane.fill = ax_l.yaxis.pane.fill = ax_l.zaxis.pane.fill = False
    ax_l.xaxis.pane.set_edgecolor("#1a1a2e")
    ax_l.yaxis.pane.set_edgecolor("#1a1a2e")
    ax_l.zaxis.pane.set_edgecolor("#1a1a2e")
    ax_l.grid(True, color="#1e1e3a", alpha=0.4, linewidth=0.4)
    ax_l.tick_params(colors="#444455", labelsize=6)
    ax_l.view_init(elev=25, azim=-50)
    ax_l.set_title(
        "Three INDEPENDENT Causal Trees\n(WolframModel structure — no cross-tape edges)\n"
        "3 disconnected components, purely 1D+1",
        color="#aaaaaa", fontsize=10, fontweight="bold", pad=10
    )

    # Independent label
    n_within = len(within_edges)
    ax_l.text2D(0.05, 0.05,
                f"{n_within} within-tape edges\n0 cross-tape edges\n3 components (disconnected)",
                transform=ax_l.transAxes, fontsize=9, color="#3366ff",
                bbox=dict(facecolor="#111122", alpha=0.7, boxstyle="round,pad=0.4",
                          edgecolor="#3366ff"))

    # ---- Right panel: coupled bulk (within + cross-tape) ----
    ax_r = fig.add_subplot(122, projection="3d", facecolor=BG_COLOR)

    # Within-tape
    for sc, st, ss, dc, dt, ds in within_edges:
        x0, y0, z0 = event_coords(sc, st, ss)
        x1, y1, z1 = event_coords(dc, dt, ds)
        ax_r.plot([x0, x1], [y0, y1], [z0, z1],
                  color="#3366ff", alpha=0.22, linewidth=0.6, zorder=1)

    # Cross-tape
    for sc, st, ss, dc, dt, ds in cross_edges:
        x0, y0, z0 = event_coords(sc, st, ss)
        x1, y1, z1 = event_coords(dc, dt, ds)
        ax_r.plot([x0, x1], [y0, y1], [z0, z1],
                  color="#ff4400", alpha=0.40, linewidth=0.8,
                  linestyle="--", zorder=2)

    # Draw nodes
    for step in range(N_STEPS):
        for tape in range(N_TAPES):
            xs, ys, zs, cs, sizes = [], [], [], [], []
            for cell in range(N_CELLS):
                val = get_orbit_value(cell, tape, step)
                xs.append(float(cell))
                ys.append(float(tape))
                zs.append(float(step))
                cs.append(Z7_COLORS[val])
                sizes.append(130 if val > 0 else 60)
            ax_r.scatter(xs, ys, zs, c=cs, s=sizes,
                         edgecolors=TAPE_COLORS[tape], linewidths=1.0,
                         zorder=10, depthshade=False)

    ax_r.set_xlabel("Cell (j)", color="#888888", fontsize=8, labelpad=6)
    ax_r.set_ylabel("Tape", color="#888888", fontsize=8, labelpad=6)
    ax_r.set_zlabel("Orbit step", color="#888888", fontsize=8, labelpad=6)
    ax_r.set_xticks(range(N_CELLS))
    ax_r.set_xticklabels([str(i) for i in range(N_CELLS)], fontsize=6, color="#666666")
    ax_r.set_yticks(range(N_TAPES))
    ax_r.set_yticklabels(["x", "y", "z"], fontsize=7, color="#666666")
    ax_r.set_zticks(range(N_STEPS))
    ax_r.set_zticklabels(ORBIT_LABELS, fontsize=6.5, color="#999999")
    ax_r.xaxis.pane.fill = ax_r.yaxis.pane.fill = ax_r.zaxis.pane.fill = False
    ax_r.xaxis.pane.set_edgecolor("#1a1a2e")
    ax_r.yaxis.pane.set_edgecolor("#1a1a2e")
    ax_r.zaxis.pane.set_edgecolor("#1a1a2e")
    ax_r.grid(True, color="#1e1e3a", alpha=0.4, linewidth=0.4)
    ax_r.tick_params(colors="#444455", labelsize=6)
    ax_r.view_init(elev=25, azim=-50)
    ax_r.set_title(
        "Combined DPP Bulk Causal Graph\n(this session — within + cross-tape edges)\n"
        "1 connected component, 3+1D",
        color="white", fontsize=10, fontweight="bold", pad=10
    )

    n_cross = len(cross_edges)
    frac = n_cross / (n_within + n_cross)
    ax_r.text2D(0.05, 0.05,
                f"{n_within} within-tape edges (blue)\n{n_cross} cross-tape edges (red)\n"
                f"1 component (connected)\nCross-tape fraction: {frac:.1%}",
                transform=ax_r.transAxes, fontsize=9, color="#ff6600",
                bbox=dict(facecolor="#111122", alpha=0.7, boxstyle="round,pad=0.4",
                          edgecolor="#ff4400"))

    fig.suptitle(
        "Independent vs. Coupled: How DPP Cross-Tape Coupling Changes the Causal Structure",
        color="white", fontsize=13, fontweight="bold", y=1.01
    )
    plt.tight_layout(rect=[0, 0, 1, 0.99])

    out_path = FIGURES_DIR / "p49_causal_comparison.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight",
                facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)
    size = out_path.stat().st_size
    print(f"Figure 4 saved: {out_path.name} ({size:,} bytes)")
    return out_path


# ---------------------------------------------------------------------------
# WolframModel encoding attempt
# ---------------------------------------------------------------------------

def check_wolfram_available() -> bool:
    """Check if wolframscript / SetReplace is available."""
    import subprocess
    result = subprocess.run(
        ["wolframscript", "-code",
         'Needs["SetReplace`"]; Print["Available"]'],
        capture_output=True, text=True, timeout=30
    )
    return "Available" in result.stdout


def attempt_wolfram_encoding() -> str:
    """Try to encode the combined bulk as a WolframModel hyperedge rule."""
    import subprocess

    wl_code = r"""
Needs["SetReplace`"];
(* Combined three-tape DPP causal graph as hyperedges *)
(* Each event: {cell, tape, step} *)
(* Within-tape rule: {c1,a,t},{c2,a,t},{c3,a,t} -> {c2,a,t+1} *)
(* Cross-tape rule:  {c,0,t},{c,1,t},{c,2,t} -> {c,0,t+1},{c,1,t+1},{c,2,t+1} *)

(* Encode GEN orbit as initial state *)
genOrbit = {{1,5,2,2,1},{2,5,2,0,2},{5,6,5,3,5},{0,0,0,0,0}};
(* events: {cell, tape, step} *)
initEdges = Flatten[Table[{c, a, 0}, {c, 0, 4}, {a, 0, 2}], 1];
Print["Init edges count: ", Length[initEdges]];

(* Define within-tape transition: 3 neighbors -> center cell next step *)
withinRule = {{x_,a_,t_},{y_,a_,t_},{z_,a_,t_}} :> {{y, a, t+1}};
(* Cross-tape: same cell, all tapes at time t -> all tapes at t+1 *)
crossRule = {{c_,0,t_},{c_,1,t_},{c_,2,t_}} :> {{c,0,t+1},{c,1,t+1},{c,2,t+1}};

Print["WolframModel encoding: within-tape and cross-tape rules defined"];
Print["WithinRule: ", withinRule];
Print["CrossRule: ", crossRule];
"""
    result = subprocess.run(
        ["wolframscript", "-code", wl_code],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0:
        return f"WolframModel encoding attempted: {result.stdout.strip()}"
    else:
        return f"WolframModel encoding failed: {result.stderr[:200]}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    print("=" * 65)
    print("Three-tape DPP combined bulk causal graph")
    print("=" * 65)

    # Step 1 & 2: Compute causal edges
    print("\n--- Computing causal edges ---")
    within_edges, cross_edges, n_within, n_cross = compute_causal_edges()
    n_total = n_within + n_cross
    frac_cross = n_cross / n_total
    print(f"  Within-tape edges: {n_within}")
    print(f"  Cross-tape edges:  {n_cross}")
    print(f"  Total edges:       {n_total}")
    print(f"  Cross-tape fraction (gravitational coupling): {frac_cross:.4f} = {frac_cross:.1%}")

    # Step 2b: Connectivity
    print("\n--- Checking connectivity ---")
    connected = is_connected(within_edges, cross_edges)
    print(f"  Combined graph connected: {connected}")
    # Check without cross-tape
    connected_within_only = is_connected(within_edges, [])
    print(f"  Within-tape-only connected: {connected_within_only} (expected False — 3 components)")

    # Steps 3: Visualizations
    print(f"\n--- Figure 1: Full 3D causal graph --- [{time.time()-t0:.1f}s]")
    p1 = figure1_full_3d_causal_graph(within_edges, cross_edges)

    print(f"\n--- Figure 2: Cross-tape edges only --- [{time.time()-t0:.1f}s]")
    p2 = figure2_cross_tape_only(cross_edges)

    print(f"\n--- Figure 3: Time-slice causal structure --- [{time.time()-t0:.1f}s]")
    p3 = figure3_time_slices(within_edges, cross_edges)

    print(f"\n--- Figure 4: Comparison independent vs. coupled --- [{time.time()-t0:.1f}s]")
    p4 = figure4_comparison(within_edges, cross_edges)

    # Step 5: WolframModel attempt
    print(f"\n--- Step 5: WolframModel encoding attempt --- [{time.time()-t0:.1f}s]")
    try:
        wolfram_available = check_wolfram_available()
        if wolfram_available:
            wolfram_result = attempt_wolfram_encoding()
            print(f"  {wolfram_result}")
        else:
            print("  WolframModel/SetReplace not available — Python matplotlib output sufficient.")
    except Exception as e:
        print(f"  WolframModel check failed: {e}")

    signal.alarm(0)

    # Final report
    print("\n" + "=" * 65)
    print("RESULTS SUMMARY")
    print("=" * 65)
    print(f"\nEvent space: {N_CELLS} cells × {N_TAPES} tapes × {N_STEPS} steps = {N_CELLS*N_TAPES*N_STEPS} events")
    print(f"\nCausal edge counts:")
    print(f"  Within-tape edges: {n_within}")
    print(f"  Cross-tape edges:  {n_cross}")
    print(f"  Total:             {n_total}")
    print(f"  Cross-tape fraction: {frac_cross:.4f} ({frac_cross:.1%})")
    print(f"\nConnectivity:")
    print(f"  Combined graph (within+cross): {'CONNECTED ✓' if connected else 'DISCONNECTED ✗'}")
    print(f"  Within-tape only:              {'CONNECTED' if connected_within_only else 'DISCONNECTED (3 components)'}")
    print(f"\nKey finding: Cross-tape coupling CONNECTS the three tapes into a single")
    print(f"  causal structure — this is the mechanism that makes the system 3+1D")
    print(f"  rather than three independent 1+1D systems.")
    print(f"\nGenerated figures:")
    for path in [p1, p2, p3, p4]:
        size = path.stat().st_size
        print(f"  {path.name}: {size:,} bytes ({size//1024} KB)")
    print(f"\nTotal elapsed: {time.time()-t0:.1f}s")
    print("=" * 65)

    return {
        "n_within": n_within,
        "n_cross": n_cross,
        "n_total": n_total,
        "frac_cross": frac_cross,
        "connected": connected,
        "connected_within_only": connected_within_only,
        "figures": [p1, p2, p3, p4],
    }


if __name__ == "__main__":
    main()
