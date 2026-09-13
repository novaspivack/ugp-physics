#!/usr/bin/env python3
"""
UGP ridge geometry and canonical GTE orbit — monograph figure generator.

Derived from the earlier `visualize_ugp_gte.py` prototype; this repo copy is authoritative for the JMP paper.

This copy lives next to the PNGs it writes for ugp_math_foundations.tex:
  - ugp_gte_visualization_paper.png  — four-panel overview (print-friendly)
  - ugp_gte_c1_field_paper.png       — (b₁,q₁) capacity field + 3D surface

Definitions:
  Ridge: R_n = 2^n − 16; UGP-1: s=7, g=13, t=20; divisor pairs b₂q₂ = R_n
  with b₂, q₂ ≥ 16; b₁ = b₂ + q₂ + s; q₁ = q₂ − g; c₁ = b₁q₁ + t.
  Green / red highlights mark c₁ prime ("prime-lock") at sampled divisor pairs.

Run from this directory:
  python visualize_ugp_gte_monograph.py
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 — registers 3d projection

OUT_DIR = Path(__file__).resolve().parent

UGP_S = 7
UGP_G = 13
UGP_T = 20
STRICT_RIDGE_MIN = 16


@dataclass(frozen=True)
class PlotTheme:
    fig_face: str
    ax_face: str
    text: str
    label: str
    tick: str
    grid: str
    legend_face: str
    legend_edge: str


THEME_PAPER = PlotTheme(
    fig_face="#fafafa",
    ax_face="#ffffff",
    text="#1a1a1a",
    label="#333333",
    tick="#444444",
    grid="#cccccc",
    legend_face="#f5f5f5",
    legend_edge="#bbbbbb",
)


def ridge(n: int) -> int:
    return (1 << n) - 16


def b1_from_pair(b2: int, q2: int) -> int:
    return b2 + q2 + UGP_S


def q1_from_q2(q2: int) -> int:
    return q2 - UGP_G


def c1_from_pair(b1: int, q1: int) -> int:
    return b1 * q1 + UGP_T


def _divisors(r: int) -> list[int]:
    if r <= 0:
        return []
    out = []
    for d in range(1, int(math.sqrt(r)) + 1):
        if r % d == 0:
            out.append(d)
            if d != r // d:
                out.append(r // d)
    return sorted(out)


def divisor_pairs(r: int) -> list[tuple[int, int]]:
    out = []
    for b2 in _divisors(r):
        if b2 < STRICT_RIDGE_MIN:
            continue
        q2 = r // b2
        if q2 >= STRICT_RIDGE_MIN:
            out.append((b2, q2))
    return out


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for d in range(2, int(math.sqrt(n)) + 1):
        if n % d == 0:
            return False
    return True


GTE_CANONICAL_ORBIT: list[tuple[int, int, int, str]] = [
    (1, 73, 823, "Lepton seed"),
    (9, 42, 1023, "Gen-2"),
    (5, 275, 65535, "Gen-3 Mersenne-like"),
]


def b1q1_ridge_locus(
    R: int,
    *,
    n_points: int = 500,
) -> tuple[np.ndarray, np.ndarray]:
    t_lo = float(STRICT_RIDGE_MIN)
    t_hi = float(R // STRICT_RIDGE_MIN)
    if t_hi < t_lo:
        return np.array([]), np.array([])
    ts = np.linspace(t_lo, t_hi, n_points)
    b2s = R / ts
    b1s = b2s + ts + UGP_S
    q1s = ts - UGP_G
    return b1s, q1s


_RIDGE_LINE = ["#0077b6", "#0096c7", "#2a9d8f", "#e9c46a", "#9b59b6", "#d62828"]
_SCATTER_COLORS = ["#d62828", "#9b59b6", "#2a9d8f", "#e9c46a"]


def plot_c1_b1q1_field(out_path: Path, theme: PlotTheme) -> None:
    fig, (ax_field, ax_surface) = plt.subplots(
        1,
        2,
        figsize=(16, 7),
        facecolor=theme.fig_face,
        gridspec_kw={"width_ratios": [1.15, 1.0]},
    )

    b1_lo, b1_hi = 35.0, 520.0
    q1_lo, q1_hi = 2.5, 360.0
    nb = 220
    b1g = np.linspace(b1_lo, b1_hi, nb)
    q1g = np.linspace(q1_lo, q1_hi, nb)
    B1, Q1 = np.meshgrid(b1g, q1g)
    C1 = B1 * Q1 + UGP_T

    ax_field.set_facecolor(theme.ax_face)
    c1_floor = 80.0
    Cplot = np.ma.masked_where(C1 <= 0, np.maximum(C1, c1_floor))

    cf = ax_field.contourf(
        B1,
        Q1,
        Cplot,
        levels=64,
        cmap="plasma",
        norm=LogNorm(vmin=c1_floor, vmax=float(np.nanmax(Cplot))),
    )
    cb = fig.colorbar(cf, ax=ax_field, shrink=0.85, pad=0.02)
    cb.set_label(r"$c_1 = b_1 q_1 + 20$ (log scale)", color=theme.label)
    cb.ax.tick_params(colors=theme.tick)

    ridge_levels = [10, 11, 12, 13, 14, 16]
    for j, n in enumerate(ridge_levels):
        R = ridge(n)
        if R <= 0:
            continue
        b1s, q1s = b1q1_ridge_locus(R)
        if b1s.size == 0:
            continue
        col = _RIDGE_LINE[j % len(_RIDGE_LINE)]
        ax_field.plot(
            b1s,
            q1s,
            color=col,
            lw=2.2,
            label=rf"$n={n}$, $R={R}$",
            zorder=4,
        )

        for b2, q2 in divisor_pairs(R):
            b1 = b1_from_pair(b2, q2)
            q1_i = q1_from_q2(q2)
            if q1_i <= 0:
                continue
            c1 = c1_from_pair(b1, q1_i)
            prim = is_prime(c1)
            ax_field.scatter(
                b1,
                q1_i,
                s=55,
                c="#2d6a4f" if prim else "#6c757d",
                edgecolors=theme.text,
                linewidths=0.8,
                zorder=5,
            )

    c_ref = 823.0
    ax_field.contour(
        B1,
        Q1,
        C1,
        levels=[c_ref],
        colors=[theme.text],
        linewidths=1.2,
        linestyles="--",
        zorder=3,
    )
    ax_field.annotate(
        rf"$c_1 = {c_ref:.0f}$ (Lepton seed)",
        xy=(73, 11),
        fontsize=8,
        color=theme.text,
        alpha=0.95,
    )

    ax_field.set_xlim(b1_lo, b1_hi)
    ax_field.set_ylim(q1_lo, q1_hi)
    ax_field.set_xlabel(r"$b_1$ (ladder)", color=theme.label, fontsize=10)
    ax_field.set_ylabel(r"$q_1$ (quotient)", color=theme.label, fontsize=10)
    ax_field.set_title(
        r"UGP capacity field $c_1 = b_1 q_1 + 20$"
        + "\nColored curves: ridge locus $b_2 q_2 = R_n$; dots: divisor pairs "
        + "(dark green: $c_1$ prime)",
        color=theme.text,
        fontsize=10,
    )
    ax_field.tick_params(colors=theme.tick)
    ax_field.grid(True, alpha=theme.ax_face == "#ffffff" and 0.35 or 0.2, color=theme.grid)
    ax_field.legend(
        facecolor=theme.legend_face,
        edgecolor=theme.legend_edge,
        labelcolor=theme.text,
        fontsize=8,
        loc="upper right",
    )

    ax_surface.remove()
    ax_surface = fig.add_subplot(1, 2, 2, projection="3d")
    ax_surface.set_facecolor(theme.ax_face)
    subsample = slice(None, None, 3)
    Bs = B1[subsample, subsample]
    Qs = Q1[subsample, subsample]
    Zs = Bs * Qs + UGP_T
    ax_surface.plot_surface(
        Bs,
        Qs,
        Zs,
        cmap="plasma",
        norm=LogNorm(vmin=c1_floor, vmax=float(np.nanmax(Zs))),
        edgecolor="none",
        alpha=0.92,
        rstride=1,
        cstride=1,
    )

    for j, n in enumerate([10, 12, 14, 16]):
        R = ridge(n)
        b1s, q1s = b1q1_ridge_locus(R, n_points=120)
        if b1s.size == 0:
            continue
        zridge = b1s * q1s + UGP_T
        col = _RIDGE_LINE[j % len(_RIDGE_LINE)]
        ax_surface.plot(
            b1s,
            q1s,
            zridge,
            color=col,
            lw=2.5,
        )

    ax_surface.set_xlabel(r"$b_1$", color=theme.label, fontsize=8)
    ax_surface.set_ylabel(r"$q_1$", color=theme.label, fontsize=8)
    ax_surface.set_zlabel(r"$c_1$", color=theme.label, fontsize=8)
    ax_surface.set_title(
        r"Same field as surface $z = b_1 q_1 + 20$"
        + "\nRidge loci climb with $n$",
        color=theme.text,
        fontsize=10,
    )
    ax_surface.tick_params(colors=theme.tick, labelsize=7)
    ax_surface.xaxis.pane.fill = False
    ax_surface.yaxis.pane.fill = False
    ax_surface.zaxis.pane.fill = False
    ax_surface.xaxis.pane.set_edgecolor(theme.grid)
    ax_surface.yaxis.pane.set_edgecolor(theme.grid)
    ax_surface.zaxis.pane.set_edgecolor(theme.grid)

    fig.suptitle(
        r"UGP in $(b_1,q_1)$ coordinates — sieve selects integer points on colored curves",
        fontsize=12,
        color=theme.text,
        y=1.02,
    )
    fig.patch.set_facecolor(theme.fig_face)
    fig.tight_layout()
    fig.savefig(
        out_path,
        dpi=200,
        bbox_inches="tight",
        facecolor=theme.fig_face,
        edgecolor="none",
    )
    plt.close(fig)
    print(f"Wrote {out_path}")


def plot_four_panel(out_path: Path, theme: PlotTheme) -> None:
    fig = plt.figure(figsize=(14, 10), facecolor=theme.fig_face)
    fig.suptitle(
        r"UGP ridges (hyperbola slices) and GTE orbit (triple space)"
        + "\n"
        + r"$R_n = 2^n-16$; $(b_2,q_2)$ on $b_2 q_2=R_n$; "
        + r"$c_1=b_1 q_1+20$ with $b_1=b_2+q_2+7$, $q_1=q_2-13$",
        fontsize=11,
        color=theme.text,
        y=0.98,
    )

    ax1 = fig.add_subplot(2, 2, 1)
    ax1.set_facecolor(theme.ax_face)
    ns = list(range(5, 23))
    Rvals = [ridge(n) for n in ns]
    ax1.semilogy(ns, Rvals, "o-", color=_RIDGE_LINE[0], lw=2, ms=5)
    ax1.set_xlabel("Ridge level $n$", color=theme.label)
    ax1.set_ylabel(r"$R_n = 2^n - 16$", color=theme.label)
    ax1.set_title("Ridge magnitude (exponential in $n$)", color=theme.text, fontsize=10)
    ax1.tick_params(colors=theme.tick)
    ax1.grid(True, alpha=0.35, color=theme.grid)

    ax2 = fig.add_subplot(2, 2, 2)
    ax2.set_facecolor(theme.ax_face)
    for j, n in enumerate([10, 12, 14, 16]):
        R = ridge(n)
        pairs = divisor_pairs(R)
        bs = [p[0] for p in pairs]
        qs = [p[1] for p in pairs]
        ccol = _SCATTER_COLORS[j % len(_SCATTER_COLORS)]
        ax2.scatter(bs, qs, s=40, c=ccol, label=rf"$n={n}$, $R={R}$", zorder=3)
        xs = [R / y for y in range(STRICT_RIDGE_MIN, min(300, R // STRICT_RIDGE_MIN) + 1)]
        ys = [R / x for x in xs]
        ax2.plot(xs, ys, "--", color=ccol, alpha=0.45, lw=1)

    ax2.set_xlabel(r"$b_2$ (ridge divisor)", color=theme.label)
    ax2.set_ylabel(r"$q_2$ (paired divisor)", color=theme.label)
    ax2.set_title(r"Each ridge = discrete points on $b_2 q_2 = R_n$", color=theme.text, fontsize=10)
    ax2.legend(
        facecolor=theme.legend_face,
        edgecolor=theme.legend_edge,
        labelcolor=theme.text,
        fontsize=8,
    )
    ax2.tick_params(colors=theme.tick)
    ax2.set_xlim(0, 280)
    ax2.set_ylim(0, 280)
    ax2.grid(True, alpha=0.35, color=theme.grid)
    ax2.set_aspect("equal", adjustable="box")

    ax3 = fig.add_subplot(2, 2, 3, projection="3d")
    ax3.set_facecolor(theme.ax_face)
    bx, qy, zn, cz = [], [], [], []
    for n in range(5, 19):
        R = ridge(n)
        if R <= 0:
            continue
        for b2, q2 in divisor_pairs(R):
            b1 = b1_from_pair(b2, q2)
            q1 = q1_from_q2(q2)
            if q1 <= 0:
                continue
            c1 = c1_from_pair(b1, q1)
            if c1 > 5_000_000:
                continue
            bx.append(b2)
            qy.append(q2)
            zn.append(n)
            cz.append(1 if is_prime(c1) else 0)
    sc = ax3.scatter(bx, qy, zn, c=cz, cmap="coolwarm", alpha=0.85, depthshade=True)
    ax3.set_xlabel(r"$b_2$", color=theme.label, fontsize=8)
    ax3.set_ylabel(r"$q_2$", color=theme.label, fontsize=8)
    ax3.set_zlabel(r"$n$ (ridge)", color=theme.label, fontsize=8)
    ax3.set_title(r"Stacked ridges: $c_1$ prime (red) vs composite (blue)", color=theme.text, fontsize=10)
    ax3.tick_params(colors=theme.tick, labelsize=7)
    ax3.xaxis.pane.fill = False
    ax3.yaxis.pane.fill = False
    ax3.zaxis.pane.fill = False
    for a in (ax3.xaxis, ax3.yaxis, ax3.zaxis):
        a.pane.set_edgecolor(theme.grid)
    cbar = fig.colorbar(sc, ax=ax3, shrink=0.5, pad=0.12)
    cbar.ax.set_title(r"$c_1$ prime", color=theme.text, fontsize=8)
    cbar.ax.tick_params(colors=theme.tick)

    ax4 = fig.add_subplot(2, 2, 4, projection="3d")
    ax4.set_facecolor(theme.ax_face)
    orbit = GTE_CANONICAL_ORBIT
    aseq = [t[0] for t in orbit]
    bseq = [t[1] for t in orbit]
    cseq = [t[2] for t in orbit]
    ax4.plot(aseq, bseq, cseq, color=_RIDGE_LINE[0], lw=2, marker="o", ms=8, zorder=3)
    for (a, b, c, lab), col in zip(orbit, _SCATTER_COLORS):
        ax4.plot([a], [b], [c], linestyle="", marker="o", color=col, markersize=10, zorder=4)
        ax4.text(
            float(a),
            float(b),
            float(c),
            f"  {lab}\n  ({a},{b},{c})",
            color=theme.text,
            fontsize=7,
        )
    ax4.set_xlabel(r"$a$ (phase leg)", color=theme.label, fontsize=8)
    ax4.set_ylabel(r"$b$ (ladder)", color=theme.label, fontsize=8)
    ax4.set_zlabel(r"$c$ (capacity)", color=theme.label, fontsize=8)
    ax4.set_title(r"Canonical GTE orbit in triple space $\mathbb{R}^3$", color=theme.text, fontsize=10)
    ax4.tick_params(colors=theme.tick, labelsize=7)
    ax4.xaxis.pane.fill = False
    ax4.yaxis.pane.fill = False
    ax4.zaxis.pane.fill = False
    for a in (ax4.xaxis, ax4.yaxis, ax4.zaxis):
        a.pane.set_edgecolor(theme.grid)

    fig.patch.set_facecolor(theme.fig_face)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(
        out_path,
        dpi=200,
        facecolor=theme.fig_face,
        edgecolor="none",
    )
    plt.close(fig)
    print(f"Wrote {out_path}")


def main() -> None:
    plot_four_panel(OUT_DIR / "ugp_gte_visualization_paper.png", THEME_PAPER)
    plot_c1_b1q1_field(OUT_DIR / "ugp_gte_c1_field_paper.png", THEME_PAPER)


if __name__ == "__main__":
    main()
