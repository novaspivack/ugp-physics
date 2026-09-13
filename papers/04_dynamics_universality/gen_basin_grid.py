"""
Generate a clean basin-assignment grid figure to replace the uninformative
solid-red seed_partition_heatmap.png.

Data reconstructed from ugp_dynamics_universality.tex:
  - 4 canonical seeds × 3 law policies × 2 window sizes = 24 trajectories
  - 22/24 classified correctly; 2 exceptions = lucas-policy variants of seed (1,73,823)
  - Basin A: α* ≈ -0.0850;  Basin B: α* ≈ +0.0754;  Basin C: α* ≈ +0.2644
  - Seeds: Lepton (1,73,823)→A, Mirror→A, Off-res1 (2,89,1597)→C, Off-res2 (3,97,2203)→B
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

OUT = Path(__file__).resolve().parent / "figures" / "seed_partition_heatmap.png"

# Basin color palette
colors = {"A": "#aec6e8", "B": "#b5d7a8", "C": "#f4a582", "?": "#d9d9d9"}
basin_alpha = {"A": "−0.085", "B": "+0.075", "C": "+0.264"}

# Seeds (rows) and conditions (columns: policy × window)
seeds = [
    "(1, 73, 823)\n[Lepton Seed]",
    "(1, 73, 823)\n[Mirror]",
    "(2, 89, 1597)",
    "(3, 97, 2203)",
]
policies = ["mersenne-fib", "mersenne-lucas", "repunit-fib"]
windows  = ["w=8", "w=15"]

# Basin assignments: rows = seeds, cols = policy × window
# Entries: "A", "B", "C", or ("A","?") for the two exceptions
# The two exceptions are lucas-policy variants of seed (1,73,823): both windows
assignments = [
    # mersenne-fib / w=8   w=15   mersenne-lucas / w=8   w=15   repunit-fib / w=8   w=15
    ["A",              "A",        "?",                   "?",     "A",               "A"  ],  # (1,73,823)
    ["A",              "A",        "A",                   "A",     "A",               "A"  ],  # Mirror
    ["C",              "C",        "C",                   "C",     "C",               "C"  ],  # (2,89,1597)
    ["B",              "B",        "B",                   "B",     "B",               "B"  ],  # (3,97,2203)
]
# "?" = misclassified (α_geo=0.088, closest to A but in A/B border)
note_label = {"?": "A*"}

# Build column labels
col_labels = []
for p in policies:
    for w in windows:
        col_labels.append(f"{p}\n{w}")

nrows, ncols = len(seeds), len(col_labels)

fig, ax = plt.subplots(figsize=(10, 4))
ax.set_xlim(-0.5, ncols - 0.5)
ax.set_ylim(-0.5, nrows - 0.5)
ax.invert_yaxis()

for r, row_asgn in enumerate(assignments):
    for c, basin in enumerate(row_asgn):
        display = note_label.get(basin, basin)
        color   = colors.get(basin, colors["?"])
        rect = plt.Rectangle((c - 0.5, r - 0.5), 1, 1, color=color, ec="white", lw=1.5)
        ax.add_patch(rect)
        ax.text(c, r, display, ha="center", va="center",
                fontsize=11, fontweight="bold",
                color="#333333" if basin != "?" else "#8B0000")

# Axes labels
ax.set_xticks(range(ncols))
ax.set_xticklabels(col_labels, fontsize=8.5, multialignment="center")
ax.set_yticks(range(nrows))
ax.set_yticklabels(seeds, fontsize=9)
ax.tick_params(length=0)
ax.set_xlabel("Law policy × Window size", labelpad=8, fontsize=10)
ax.set_ylabel("Canonical seed", labelpad=8, fontsize=10)
ax.set_title("Basin assignment per canonical seed × (policy, window)\n"
             "22/24 trajectories correctly classified; 2 exceptions marked A*",
             fontsize=10, pad=10)

# Vertical separators between policy groups
for x in [1.5, 3.5]:
    ax.axvline(x, color="gray", lw=1.0, linestyle="--", alpha=0.6)

# Legend
patches = [
    mpatches.Patch(facecolor=colors["A"], edgecolor="#555", label="Basin A  (α*≈−0.085)"),
    mpatches.Patch(facecolor=colors["B"], edgecolor="#555", label="Basin B  (α*≈+0.075)"),
    mpatches.Patch(facecolor=colors["C"], edgecolor="#555", label="Basin C  (α*≈+0.264)"),
    mpatches.Patch(facecolor=colors["?"], edgecolor="#8B0000", label="A* = misclassified (α_geo=0.088)"),
]
ax.legend(handles=patches, loc="lower right", fontsize=8, framealpha=0.9,
          bbox_to_anchor=(1.0, -0.38), ncol=2)

plt.tight_layout()
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print(f"Saved → {OUT}")
