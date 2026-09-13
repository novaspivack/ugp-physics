"""
Generate the five figures for Paper 19 (Cyclotomic-12 Mass Structure)
from data already present in the paper.

Outputs (PNG, 300 DPI) into the same directory as this script:

  fig_tt_vv_residuals.png  -- signed residuals for the 9 charged fermions
  fig_inter_gen.png        -- six beta-free inter-generational identities
  fig_a2_weyl.png          -- A_2 root system + fundamental Weyl chamber
  fig_lean_dep_graph.png   -- DAG of the UgpLean.MassRelations module suite
  fig_vv_null_tests.png    -- triple-null bar chart for SC-JJJ / KKK / LLL

Numbers are taken verbatim from the paper text/tables; the script is
self-contained and uses no UGP runtime.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

OUT_DIR = Path(__file__).resolve().parent
plt.rcParams.update(
    {
        "font.family": "serif",
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.dpi": 300,
    }
)


def fig_tt_vv_residuals() -> None:
    # Verbatim from Table tab:predictions in the paper.
    # m_e, m_mu are inputs; tau from Koide; u,c,t from TT; d,s,b from VV.
    labels = [r"$m_\tau$", r"$m_u$", r"$m_c$", r"$m_t$", r"$m_d$", r"$m_s$", r"$m_b$"]
    relations = ["Koide", "TT", "TT", "TT", "VV", "VV", "VV"]
    residual = [0.006, -0.9, +0.27, -0.35, +0.4, -0.2, -0.17]  # percent
    colors = {"Koide": "#4e79a7", "TT": "#f28e2b", "VV": "#59a14f"}
    bar_colors = [colors[r] for r in relations]

    fig, ax = plt.subplots(figsize=(7.0, 3.5))
    x = np.arange(len(labels))
    bars = ax.bar(x, residual, color=bar_colors, edgecolor="black", linewidth=0.5)

    ax.axhline(0, color="black", linewidth=0.6)
    ax.axhline(1.0, color="grey", linewidth=0.5, linestyle="--", label="$\\pm 1\\%$ band")
    ax.axhline(-1.0, color="grey", linewidth=0.5, linestyle="--")

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Signed residual: $(\\mathrm{predicted}-\\mathrm{PDG})/\\mathrm{PDG}$ [\\%]")
    ax.set_ylim(-1.4, 1.4)
    ax.set_title(
        "Predictions vs.\\ PDG~2022 (charged fermions; two scalar inputs $m_e, m_\\mu$)"
    )

    for rect, val in zip(bars, residual):
        height = rect.get_height()
        ax.text(
            rect.get_x() + rect.get_width() / 2,
            height + (0.05 if height >= 0 else -0.10),
            f"{val:+.2f}\\%",
            ha="center",
            va="bottom" if height >= 0 else "top",
            fontsize=8,
        )

    handles = [
        mpatches.Patch(color=colors[k], label=k) for k in ["Koide", "TT", "VV"]
    ] + [
        plt.Line2D([0], [0], color="grey", linestyle="--", label="$\\pm 1\\%$ band")
    ]
    ax.legend(handles=handles, loc="upper right", framealpha=0.9)
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_tt_vv_residuals.png")
    plt.close(fig)


def fig_inter_gen() -> None:
    # Verbatim from Table tab:inter_gen in the paper.
    rows = [
        (r"$\log(m_c/m_e) - \log(m_u/m_e)$", 5.890, 5.868, +0.37, ""),
        (r"$\log(m_t/m_\tau) - \log(m_c/m_\mu)$", 5.243, 5.250, -0.13, ""),
        (r"$\log(m_t/m_\tau) - \log(m_u/m_e)$", 11.133, 11.118, +0.14, ""),
        (r"$\log(m_c m_e / m_u m_\mu)$", np.pi / 3, 1.044, -0.03, ""),
        (r"$\log(m_t m_\mu / m_c m_\tau)$", np.pi / 3, 1.046, -0.16, ""),
        (r"$\log(m_t m_e / m_u m_\tau)$", 2 * np.pi / 3, 2.090, -0.19, "Gelfond-type"),
    ]
    labels = [r[0] for r in rows]
    residuals = [r[3] for r in rows]
    note = [r[4] for r in rows]

    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    y = np.arange(len(labels))
    bars = ax.barh(
        y, residuals, color=["#76b7b2" if n != "Gelfond-type" else "#e15759" for n in note],
        edgecolor="black", linewidth=0.5,
    )
    ax.axvline(0, color="black", linewidth=0.6)
    ax.axvline(1.0, color="grey", linewidth=0.5, linestyle="--")
    ax.axvline(-1.0, color="grey", linewidth=0.5, linestyle="--")

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("PDG residual [\\%]")
    ax.set_xlim(-1.0, 1.0)
    ax.set_title(
        r"Six $\beta$-free inter-generational TT identities (no free parameters)"
    )

    for bar, val, n in zip(bars, residuals, note):
        ax.text(
            val + (0.03 if val >= 0 else -0.03),
            bar.get_y() + bar.get_height() / 2,
            f"{val:+.2f}\\%" + (f" ({n})" if n else ""),
            va="center",
            ha="left" if val >= 0 else "right",
            fontsize=8,
        )

    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_inter_gen.png")
    plt.close(fig)


def fig_a2_weyl() -> None:
    # A_2 root system: simple roots alpha_1 = (1,0), alpha_2 = (-1/2, sqrt(3)/2).
    # Fundamental weights omega_1, omega_2 dual to (alpha_i^vee).
    # In the standard normalization with simple roots of length 1:
    #   alpha_1 = (1, 0)
    #   alpha_2 = (-1/2, sqrt(3)/2)
    #   omega_1 = (1/2, 1/(2 sqrt(3)))   # = (0.5, sqrt(3)/6)
    #   omega_2 = (0, 1/sqrt(3))
    a1 = np.array([1.0, 0.0])
    a2 = np.array([-0.5, np.sqrt(3) / 2])
    w1 = np.array([0.5, np.sqrt(3) / 6])
    w2 = np.array([0.0, 1.0 / np.sqrt(3)])
    # All six roots of A_2
    roots = [a1, a2, a1 + a2, -a1, -a2, -(a1 + a2)]

    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    ax.set_aspect("equal")

    # Fundamental Weyl chamber: between the two walls perpendicular to the
    # simple roots (i.e. the cone spanned by omega_1 and omega_2).
    chamber = plt.Polygon(
        [(0, 0), (1.4 * w1[0], 1.4 * w1[1]), (1.4 * w2[0], 1.4 * w2[1])],
        closed=True,
        facecolor="#fff2cc",
        edgecolor="#bf9000",
        linewidth=0.5,
        alpha=0.7,
        label="Fundamental Weyl chamber",
    )
    ax.add_patch(chamber)

    for r, lbl in zip(
        roots,
        [r"$\alpha_1$", r"$\alpha_2$", r"$\alpha_1+\alpha_2$", "", "", ""],
    ):
        ax.annotate(
            "",
            xy=r,
            xytext=(0, 0),
            arrowprops=dict(arrowstyle="->", color="#3d85c6", lw=1.5),
        )
        if lbl:
            ax.text(1.07 * r[0], 1.07 * r[1], lbl, color="#0b5394", fontsize=11)

    for w, lbl in [(w1, r"$\omega_1$"), (w2, r"$\omega_2$")]:
        ax.annotate(
            "",
            xy=w,
            xytext=(0, 0),
            arrowprops=dict(arrowstyle="->", color="#cc0000", lw=1.5, linestyle="--"),
        )
        ax.text(1.07 * w[0] + 0.03, 1.07 * w[1] + 0.02, lbl, color="#990000", fontsize=11)

    # Mark the pi/6 angle between alpha_1 and omega_1.
    theta = np.linspace(0, np.pi / 6, 50)
    ax.plot(0.30 * np.cos(theta), 0.30 * np.sin(theta), color="#674ea7", lw=1.4)
    ax.text(0.36, 0.07, r"$\pi/6$", color="#351c75", fontsize=11)

    # Origin and axes
    ax.axhline(0, color="grey", lw=0.4)
    ax.axvline(0, color="grey", lw=0.4)
    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-1.1, 1.1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(
        r"$A_2$ root system: $\alpha=\pi/6$ as the bisector of the fundamental Weyl chamber"
    )

    # Custom legend
    ax.legend(
        handles=[
            plt.Line2D([0], [0], color="#3d85c6", lw=1.5, label=r"Simple roots $\alpha_i$"),
            plt.Line2D(
                [0], [0], color="#cc0000", lw=1.5, linestyle="--",
                label=r"Fundamental weights $\omega_i$",
            ),
            mpatches.Patch(facecolor="#fff2cc", edgecolor="#bf9000", label="Fundamental Weyl chamber"),
        ],
        loc="lower right",
        framealpha=0.95,
    )
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_a2_weyl.png")
    plt.close(fig)


def fig_lean_dep_graph() -> None:
    # DAG of UgpLean.MassRelations modules; layout by hand for clarity.
    # Layered top-down by import depth.
    nodes = {
        "SU3FlavorCartan":   (0.0, 4.0),
        "Z2OrbifoldDepth":   (-2.5, 4.0),
        "FroggattNielsen":   (2.5, 4.0),
        "BinaryCascade":     (-2.5, 2.6),
        "CartanFlavonPotential": (0.0, 2.6),
        "HeavyFermionTower": (2.5, 2.6),
        "DownRational":      (1.5, 1.2),
        "KoideClosedForm":   (-1.7, 1.2),
        "KoideNewtonFlow":   (-3.7, 1.2),
        "PhysicalMasses":    (0.0, -0.2),
    }
    # imports: child -> [parents]
    edges = [
        ("BinaryCascade", "SU3FlavorCartan"),
        ("CartanFlavonPotential", "SU3FlavorCartan"),
        ("CartanFlavonPotential", "Z2OrbifoldDepth"),
        ("HeavyFermionTower", "FroggattNielsen"),
        ("DownRational", "BinaryCascade"),
        ("DownRational", "HeavyFermionTower"),
        ("KoideClosedForm", "SU3FlavorCartan"),
        ("KoideNewtonFlow", "KoideClosedForm"),
        ("PhysicalMasses", "KoideClosedForm"),
        ("PhysicalMasses", "BinaryCascade"),
        ("PhysicalMasses", "DownRational"),
    ]

    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    ax.set_aspect("equal")

    box_w, box_h = 1.95, 0.55
    for name, (x, y) in nodes.items():
        is_capstone = name == "PhysicalMasses"
        is_external = name in ("KoideClosedForm", "KoideNewtonFlow")
        face = "#ffe599" if is_capstone else ("#e8f0fe" if is_external else "#cfe2f3")
        edge = "#bf9000" if is_capstone else ("#1c4587" if is_external else "#073763")
        ax.add_patch(
            mpatches.FancyBboxPatch(
                (x - box_w / 2, y - box_h / 2),
                box_w,
                box_h,
                boxstyle="round,pad=0.05,rounding_size=0.10",
                facecolor=face,
                edgecolor=edge,
                linewidth=1.2,
            )
        )
        ax.text(x, y, name, ha="center", va="center", fontsize=9, family="monospace")

    for child, parent in edges:
        cx, cy = nodes[child]
        px, py = nodes[parent]
        ax.annotate(
            "",
            xy=(cx, cy + box_h / 2),
            xytext=(px, py - box_h / 2),
            arrowprops=dict(arrowstyle="->", color="#444", lw=0.8),
        )

    legend_handles = [
        mpatches.Patch(facecolor="#ffe599", edgecolor="#bf9000", label="Capstone (this paper)"),
        mpatches.Patch(facecolor="#cfe2f3", edgecolor="#073763", label="MassRelations modules (this paper)"),
        mpatches.Patch(facecolor="#e8f0fe", edgecolor="#1c4587", label="Companion (Koide paper)"),
    ]
    ax.legend(handles=legend_handles, loc="lower left", framealpha=0.95)

    ax.set_xlim(-5.2, 5.0)
    ax.set_ylim(-1.4, 5.0)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title("UgpLean.MassRelations: module dependency graph (zero sorry)")

    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_lean_dep_graph.png")
    plt.close(fig)


def fig_vv_null_tests() -> None:
    # Verbatim from Section 5 of the paper.
    tests = ["SC-JJJ\nGUT-rep basis", "SC-KKK\nFN integer charges", "SC-LLL\nDiscrete-flavor"]
    rates = [54.3, np.nan, 39.8]  # percent triple-null rate at 1e-3 tolerance
    note = ["", "n/a (analytical\nobstruction)", ""]
    gate = 1.0  # 1 % structural-significance gate

    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    x = np.arange(len(tests))
    bars = ax.bar(
        x,
        [r if not np.isnan(r) else 0 for r in rates],
        color=["#4e79a7", "#bdbdbd", "#4e79a7"],
        edgecolor="black",
        linewidth=0.5,
        zorder=2,
    )
    ax.axhline(gate, color="#e15759", linestyle="--", linewidth=1.2, zorder=3,
               label=f"Structural-significance gate = {gate:.0f}\\%")

    for bar, val, n in zip(bars, rates, note):
        if np.isnan(val):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                3,
                n,
                ha="center",
                va="bottom",
                fontsize=9,
                color="#666",
            )
        else:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                val + 1.4,
                f"{val:.1f}\\%",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

    ax.set_xticks(x)
    ax.set_xticklabels(tests)
    ax.set_ylabel("Triple-null rate at $10^{-3}$ tolerance [\\%]")
    ax.set_ylim(0, 65)
    ax.set_title(
        r"VV coefficient values $(13/9,\ -7/6,\ -5/14)$: three null-discipline tests"
    )
    ax.grid(axis="y", alpha=0.3, zorder=1)
    ax.legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_vv_null_tests.png")
    plt.close(fig)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig_tt_vv_residuals()
    fig_inter_gen()
    fig_a2_weyl()
    fig_lean_dep_graph()
    fig_vv_null_tests()
    print(f"Wrote 5 figures to {OUT_DIR}")


if __name__ == "__main__":
    main()
