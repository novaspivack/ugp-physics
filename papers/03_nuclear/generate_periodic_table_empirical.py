#!/usr/bin/env python3
"""
generate_periodic_table_empirical.py
======================================
Generate the UGP-GTE Extended Periodic Table of Elements (Z=1-160).

Design:
  Z=1-118:   Empirical stability from NUBASE2020 (not GTE model predictions).
             This is the correct scientific approach for known elements.
  Z=119-160: GTE analytical law predictions, clearly labeled Category D
             (speculative extrapolation beyond training domain).

The GTE stability classifier is not used for Z=1-118 because the smooth
6-term analytical law cannot resolve discrete nuclear-structure anomalies
(e.g., why Tc and Pm have no stable isotopes despite high binding energy).
Empirical data is available and correct for all known elements; the model
is only invoked where empirical data is absent (Z>118).

Five stability categories (consistent 1-My threshold):
  Green    — Stable: ≥1 truly stable isotope
  Amber    — Primordial: all isotopes radioactive, t½ > 1 Gy (Bi, Th, U)
  Tomato   — Long-lived radioactive: t½ > 1 My, no stable isotopes
             (Tc: Tc-97 4.2 My; Np: 2.1 My; Pu: 80.8 My; Cm: 15.6 My)
  Dark red — Radioactive: t½ < 1 My, all isotopes (Pm, Po-Og excl. above)
  Purple   — GTE-predicted hypothetical: Z=119-160 (Category D)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import pandas as pd
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from nubase_stability_lookup import (
    NUBASE_STABILITY, STABLE, PRIMORDIAL, LONG_LIVED, RADIOACTIVE,
)

# ── Color palette ──────────────────────────────────────────────────────────────
C_STABLE     = '#27ae60'   # forest green
C_PRIMORDIAL = '#e67e22'   # amber       (Bi, Th, U)
C_LONG_LIVED = '#c0392b'   # tomato red  (Tc, Np, Pu, Cm)
C_RADIOACTIVE= '#7b241c'   # dark red    (Pm, Po-Og exc above)
C_PREDICTED  = '#7d3c98'   # purple      (Z=119-160)
C_EMPTY      = '#eaeded'   # light grey  (placeholders)
C_EDGE       = '#95a5a6'   # grey edge

CAT_COLOR = {
    STABLE: C_STABLE, PRIMORDIAL: C_PRIMORDIAL,
    LONG_LIVED: C_LONG_LIVED, RADIOACTIVE: C_RADIOACTIVE,
}

# ── Element data ───────────────────────────────────────────────────────────────
SYMBOLS = {
    1:'H',2:'He',3:'Li',4:'Be',5:'B',6:'C',7:'N',8:'O',9:'F',10:'Ne',
    11:'Na',12:'Mg',13:'Al',14:'Si',15:'P',16:'S',17:'Cl',18:'Ar',
    19:'K',20:'Ca',21:'Sc',22:'Ti',23:'V',24:'Cr',25:'Mn',26:'Fe',
    27:'Co',28:'Ni',29:'Cu',30:'Zn',31:'Ga',32:'Ge',33:'As',34:'Se',
    35:'Br',36:'Kr',37:'Rb',38:'Sr',39:'Y',40:'Zr',41:'Nb',42:'Mo',
    43:'Tc',44:'Ru',45:'Rh',46:'Pd',47:'Ag',48:'Cd',49:'In',50:'Sn',
    51:'Sb',52:'Te',53:'I',54:'Xe',55:'Cs',56:'Ba',57:'La',58:'Ce',
    59:'Pr',60:'Nd',61:'Pm',62:'Sm',63:'Eu',64:'Gd',65:'Tb',66:'Dy',
    67:'Ho',68:'Er',69:'Tm',70:'Yb',71:'Lu',72:'Hf',73:'Ta',74:'W',
    75:'Re',76:'Os',77:'Ir',78:'Pt',79:'Au',80:'Hg',81:'Tl',82:'Pb',
    83:'Bi',84:'Po',85:'At',86:'Rn',87:'Fr',88:'Ra',89:'Ac',90:'Th',
    91:'Pa',92:'U',93:'Np',94:'Pu',95:'Am',96:'Cm',97:'Bk',98:'Cf',
    99:'Es',100:'Fm',101:'Md',102:'No',103:'Lr',104:'Rf',105:'Db',
    106:'Sg',107:'Bh',108:'Hs',109:'Mt',110:'Ds',111:'Rg',112:'Cn',
    113:'Nh',114:'Fl',115:'Mc',116:'Lv',117:'Ts',118:'Og',
}
for Z in range(119, 161):
    SYMBOLS[Z] = f'E{Z}'

# ── Standard periodic table positions: (period, group) ────────────────────────
# f-block elements stored as ('Ln', index) or ('An', index)
POS = {}

def _build_positions():
    p = {}
    # Period 1
    p[1]=(1,1);  p[2]=(1,18)
    # Period 2
    p[3]=(2,1);  p[4]=(2,2)
    for Z,g in zip(range(5,11),range(13,19)): p[Z]=(2,g)
    # Period 3
    p[11]=(3,1); p[12]=(3,2)
    for Z,g in zip(range(13,19),range(13,19)): p[Z]=(3,g)
    # Period 4
    p[19]=(4,1); p[20]=(4,2)
    for Z,g in zip(range(21,31),range(3,13)): p[Z]=(4,g)
    for Z,g in zip(range(31,37),range(13,19)): p[Z]=(4,g)
    # Period 5
    p[37]=(5,1); p[38]=(5,2)
    for Z,g in zip(range(39,49),range(3,13)): p[Z]=(5,g)
    for Z,g in zip(range(49,55),range(13,19)): p[Z]=(5,g)
    # Period 6 — main block (La-Lu in f-row)
    p[55]=(6,1); p[56]=(6,2)
    for i,Z in enumerate(range(57,72)): p[Z]=('Ln',i)   # La-Lu
    for Z,g in zip(range(72,81),range(4,13)): p[Z]=(6,g)
    for Z,g in zip(range(81,87),range(13,19)): p[Z]=(6,g)
    # Period 7 — main block (Ac-Lr in f-row)
    p[87]=(7,1); p[88]=(7,2)
    for i,Z in enumerate(range(89,104)): p[Z]=('An',i)  # Ac-Lr
    for Z,g in zip(range(104,113),range(4,13)): p[Z]=(7,g)
    for Z,g in zip(range(113,119),range(13,19)): p[Z]=(7,g)
    return p

POS = _build_positions()

# ── Load GTE BE/A for Z=119-160 ───────────────────────────────────────────────
def load_gte_be():
    csv = os.path.join(os.path.dirname(__file__), 'periodic_table_data.csv')
    df  = pd.read_csv(csv)
    return {int(r.Z): float(r.Binding_Energy_Per_Nucleon) for _, r in df.iterrows()}

# ── Drawing ────────────────────────────────────────────────────────────────────
def draw_cell(ax, cx, cy, sym, Z, color, fs_sym=7.0, fs_z=4.8):
    W, H = 0.92, 0.86
    ax.add_patch(FancyBboxPatch(
        (cx-W/2, cy-H/2), W, H,
        boxstyle='round,pad=0.05', linewidth=0.35,
        edgecolor=C_EDGE, facecolor=color, zorder=2))
    ax.text(cx, cy+0.12, sym, ha='center', va='center',
            fontsize=fs_sym, fontweight='bold', color='white', zorder=3)
    ax.text(cx, cy-0.22, str(Z), ha='center', va='center',
            fontsize=fs_z, color='white', alpha=0.88, zorder=3)

def draw_placeholder(ax, cx, cy, label):
    W, H = 0.92, 0.86
    ax.add_patch(FancyBboxPatch(
        (cx-W/2, cy-H/2), W, H,
        boxstyle='round,pad=0.05', linewidth=0.35,
        edgecolor='#bdc3c7', facecolor='#d5d8dc', alpha=0.5, zorder=2))
    ax.text(cx, cy, label, ha='center', va='center',
            fontsize=4.5, color='#7f8c8d', style='italic', zorder=3)


def generate(out_path=None):
    gte_be = load_gte_be()

    # Canvas: wider to give room for legend
    fig, ax = plt.subplots(figsize=(30, 18))
    ax.set_aspect('equal')
    ax.axis('off')

    # Coordinate system: group 1-18 → x=1-18; period 1-7 → y=9.5 down to 3.5
    # f-block rows at y=2.3 (Ln) and y=1.3 (An)
    # Predicted block at y=-0.3 down
    ax.set_xlim(-0.5, 24.5)
    ax.set_ylim(-7.5, 11.0)

    period_y = {1:9.5, 2:8.5, 3:7.5, 4:6.5, 5:5.5, 6:4.5, 7:3.5}

    # ── Main table (Z=1-118) ──────────────────────────────────────────────────
    for Z in range(1, 119):
        pos = POS.get(Z)
        if pos is None:
            continue
        color = CAT_COLOR[NUBASE_STABILITY[Z]]
        sym   = SYMBOLS[Z]

        if isinstance(pos[0], int):
            period, group = pos
            cx = float(group); cy = period_y[period]
            draw_cell(ax, cx, cy, sym, Z, color)
        elif pos[0] == 'Ln':
            cx = pos[1] + 3.0; cy = 2.3   # lanthanide row
            draw_cell(ax, cx, cy, sym, Z, color)
        elif pos[0] == 'An':
            cx = pos[1] + 3.0; cy = 1.3   # actinide row
            draw_cell(ax, cx, cy, sym, Z, color)

    # f-block connector placeholders in main table
    draw_placeholder(ax, 3.0, period_y[6], 'La–Lu\n57–71')
    draw_placeholder(ax, 3.0, period_y[7], 'Ac–Lr\n89–103')

    # f-block row labels
    for label, cy in [('Lanthanides (f-block)', 2.3), ('Actinides (f-block)', 1.3)]:
        ax.text(2.35, cy, label, ha='right', va='center',
                fontsize=5.5, color='#5d6d7e', style='italic')

    # ── Predicted elements Z=119-160 ──────────────────────────────────────────
    pred_block_label_y = 0.0
    pred_cols = 11    # elements per row
    pred_row_h = 1.05
    pred_start_x = 3.0
    pred_start_y = -0.5

    ax.text(pred_start_x - 0.6, pred_start_y + 0.45,
            'GTE-Predicted Hypothetical Elements\nZ=119–160  [Category D: speculative]',
            ha='left', va='top', fontsize=7.5, color='#5b2c6f',
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#f4ecf7',
                      edgecolor='#7d3c98', alpha=0.85, linewidth=0.7))

    for i, Z in enumerate(range(119, 161)):
        row = i // pred_cols
        col = i % pred_cols
        cx = pred_start_x + col * 1.00
        cy = pred_start_y - (row + 0.9) * pred_row_h
        be  = gte_be.get(Z, 6.0)
        # Shade by BE/A: higher BE/A → slightly more saturated
        alpha = 0.60 + min(0.35, max(0, (be - 5.0) / 6.0 * 0.35))
        ax.add_patch(FancyBboxPatch(
            (cx-0.46, cy-0.40), 0.92, 0.80,
            boxstyle='round,pad=0.04', linewidth=0.5,
            edgecolor='#6c3483', facecolor=C_PREDICTED, alpha=alpha, zorder=2))
        ax.text(cx, cy+0.10, SYMBOLS[Z], ha='center', va='center',
                fontsize=5.5, fontweight='bold', color='white', zorder=3)
        ax.text(cx, cy-0.20, str(Z), ha='center', va='center',
                fontsize=4.0, color='white', alpha=0.85, zorder=3)

    # ── Legend ─────────────────────────────────────────────────────────────────
    lx, ly = 19.7, 9.2
    ax.text(lx + 0.35, ly + 0.45, 'Stability (NUBASE2020)',
            ha='center', va='bottom', fontsize=8.0, fontweight='bold',
            color='#1a252f')

    legend_items = [
        (C_STABLE,
         'Stable',
         '≥1 stable isotope\n'
         '(Z=1–82 excl. Tc, Pm)'),
        (C_PRIMORDIAL,
         'Primordial',
         'All isotopes radioactive,\n'
         't½ > 1 Gy\n'
         'Bi (2×10¹⁹ y), Th (14 Gy), U (4.5 Gy)'),
        (C_LONG_LIVED,
         'Long-lived radioactive',
         'No stable isotopes; t½ > 1 My\n'
         'Tc (4.2 My), Np (2.1 My),\n'
         'Pu (80.8 My), Cm (15.6 My)'),
        (C_RADIOACTIVE,
         'Radioactive',
         'All isotopes; t½ < 1 My\n'
         'Pm (17.7 y), Po–Og\n'
         '(excl. Th, U, Np, Pu, Cm)'),
        (C_PREDICTED,
         'GTE-predicted (Z=119–160)',
         'Hypothetical; GTE extrapolation\n'
         'beyond training domain\n'
         '[Category D: speculative]'),
    ]

    box_h = 0.55
    gap   = 0.25
    for i, (color, title, detail) in enumerate(legend_items):
        item_top = ly - i * (box_h * 3 + gap)
        bx, by = lx, item_top - box_h
        ax.add_patch(FancyBboxPatch(
            (bx - 0.05, by - 0.05), 0.72, box_h * 1.1 + 0.10,
            boxstyle='round,pad=0.05', facecolor=color,
            edgecolor='white', linewidth=0.5, zorder=4))
        ax.text(bx + 0.72 + 0.12, by + box_h * 0.55,
                f'$\\mathbf{{{title}}}$\n{detail}',
                ha='left', va='center', fontsize=5.5,
                color='#2c3e50', linespacing=1.35)

    # ── Period labels ──────────────────────────────────────────────────────────
    for p, y in period_y.items():
        ax.text(0.35, y, str(p), ha='center', va='center',
                fontsize=6.0, color='#7f8c8d', fontweight='bold')
    ax.text(0.35, 2.3,  'f', ha='center', va='center',
            fontsize=5.5, color='#aab7b8', style='italic')
    ax.text(0.35, 1.3,  'f', ha='center', va='center',
            fontsize=5.5, color='#aab7b8', style='italic')

    # ── Group labels ───────────────────────────────────────────────────────────
    for g in range(1, 19):
        ax.text(float(g), 10.1, str(g), ha='center', va='center',
                fontsize=5.5, color='#7f8c8d')

    # ── Title ──────────────────────────────────────────────────────────────────
    ax.text(9.5, 10.65,
            'UGP-GTE Extended Periodic Table of Elements (Z=1–160)',
            ha='center', va='center', fontsize=15, fontweight='bold',
            color='#1a252f')
    ax.text(9.5, 10.25,
            'Z=1–118: Empirical stability (NUBASE2020)  |  '
            'Z=119–160: GTE analytical law predictions (Category D — speculative)',
            ha='center', va='center', fontsize=7.5, color='#5d6d7e',
            style='italic')

    # ── Disclosure note ────────────────────────────────────────────────────────
    ax.text(0.0, -6.8,
            'Note: Stability colors for Z=1–118 are based on empirical NUBASE2020 data, not GTE model predictions.\n'
            'The smooth GTE analytical stability law cannot resolve certain discrete nuclear-structure anomalies\n'
            '(e.g., the absence of stable isotopes in Tc and Pm) and is therefore not used for known elements.\n'
            'Predictions for Z=119–160 are GTE extrapolations beyond the training domain; they carry\n'
            'Category D (speculative) status and should not be interpreted as physical predictions.',
            ha='left', va='bottom', fontsize=5.8, color='#7f8c8d',
            style='italic',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#fdfefe',
                      edgecolor='#bdc3c7', linewidth=0.5, alpha=0.92))

    plt.tight_layout(pad=0.3)
    if out_path is None:
        out_path = os.path.join(os.path.dirname(__file__), 'periodic_table.png')
    plt.savefig(out_path, dpi=220, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f'Saved: {out_path}')
    return out_path


if __name__ == '__main__':
    generate()
