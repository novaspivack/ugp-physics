#!/usr/bin/env python3
"""Assemble multi-panel figures from raw screenshots of the live Phi_MDL
kink-dynamics visualization (visualizations/phimdl_kink_dynamics/) into the
composite PNGs used by the "Exact Multi-Kink Dynamics and the Definitive
Particle Characterization" section of gte_complete_theory.tex.

Each output figure is a single flattened PNG (this paper's existing figure
convention has no subfigure/subcaption package -- see
scripts/uwca_rule110_sidebyside.png for the precedent): a row or grid of
per-frame panels, each cropped to the app's main view (sidebar and header
removed) and labeled with its simulation time.

Reproduction: the raw screenshots are captured via browser automation
against a local server of visualizations/phimdl_kink_dynamics/ (see that
directory's README.md for how to run it); this script only performs the
crop/resize/label/grid composition once the raw PNGs exist in
`scripts/kink_viz_raw/`.
"""

import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "kink_viz_raw")

# Crop box removing the app's left control sidebar and top header bar,
# leaving only the field/domain view, at the raw screenshot resolution
# (3410x1868, a 2x-class devicePixelRatio capture of the 1024-wide app).
CROP_BOX_1D = (595, 100, 3410, 100 + 1400)  # field strip + curve + history
CROP_BOX_2D3D = (595, 100, 3410, 1868)      # full remaining view

# Second capture session (random-IC coarsening figure) used a narrower
# browser viewport (1972x1868 raw); same top-crop offset (header height is
# viewport-independent), sidebar boundary scaled proportionally.
CROP_BOX_2D3D_NARROW = (537, 100, 1972, 1868)

LABEL_H = 60
PANEL_W = 560
FONT_SIZE = 26
BG = (10, 12, 18)
FG = (235, 235, 235)


def _font():
    for path in (
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ):
        if os.path.exists(path):
            return ImageFont.truetype(path, FONT_SIZE)
    return ImageFont.load_default()


def load_panel(filename, crop_box, panel_w=PANEL_W):
    im = Image.open(os.path.join(RAW_DIR, filename)).convert("RGB")
    im = im.crop(crop_box)
    scale = panel_w / im.width
    im = im.resize((panel_w, round(im.height * scale)), Image.LANCZOS)
    return im


def make_row(panels_and_labels, out_name, panel_w=PANEL_W):
    """panels_and_labels: list of (PIL.Image, label_str)."""
    panel_h = max(im.height for im, _ in panels_and_labels)
    n = len(panels_and_labels)
    gap = 8
    total_w = n * panel_w + (n - 1) * gap
    total_h = panel_h + LABEL_H
    canvas = Image.new("RGB", (total_w, total_h), BG)
    draw = ImageDraw.Draw(canvas)
    font = _font()
    x = 0
    for im, label in panels_and_labels:
        canvas.paste(im, (x, LABEL_H))
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((x + (panel_w - tw) // 2, 14), label, fill=FG, font=font)
        x += panel_w + gap
    out_path = os.path.join(HERE, out_name)
    canvas.save(out_path)
    print(f"wrote {out_path}  ({total_w}x{total_h})")


def make_grid(panels_and_labels, ncols, out_name, panel_w=PANEL_W):
    n = len(panels_and_labels)
    nrows = (n + ncols - 1) // ncols
    panel_h = max(im.height for im, _ in panels_and_labels)
    gap = 8
    total_w = ncols * panel_w + (ncols - 1) * gap
    total_h = nrows * (panel_h + LABEL_H) + (nrows - 1) * gap
    canvas = Image.new("RGB", (total_w, total_h), BG)
    draw = ImageDraw.Draw(canvas)
    font = _font()
    for i, (im, label) in enumerate(panels_and_labels):
        row, col = divmod(i, ncols)
        x = col * (panel_w + gap)
        y = row * (panel_h + LABEL_H + gap)
        canvas.paste(im, (x, y + LABEL_H))
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((x + (panel_w - tw) // 2, y + 14), label, fill=FG, font=font)
    out_path = os.path.join(HERE, out_name)
    canvas.save(out_path)
    print(f"wrote {out_path}  ({total_w}x{total_h})")


def main():
    # Figure: 1D pure-sector kink-antikink elastic pass-through
    frames = [
        ("fig1_frame_a_t0.png", "t = 0.00 fm/c"),
        ("fig1_frame_b_t18.png", "t = 2.00 fm/c"),
        ("fig1_frame_c_t37.png", "t = 4.16 fm/c"),
        ("fig1_frame_d_t56.png", "t = 6.22 fm/c"),
        ("fig1_frame_e_t90.png", "t = 9.99 fm/c"),
    ]
    make_row(
        [(load_panel(f, CROP_BOX_1D, panel_w=460), lbl) for f, lbl in frames],
        "fig_kink_1d_pure_pass_through.png",
        panel_w=460,
    )

    # Figure: 1D perturbed-sector capture into a decaying oscillating bion
    frames = [
        ("fig2_frame_a_t0.png", "t = 0.00 fm/c"),
        ("fig2_frame_b_t270.png", "t = 29.98 fm/c"),
        ("fig2_frame_c_t1200.png", "t = 133.26 fm/c"),
    ]
    make_row(
        [(load_panel(f, CROP_BOX_1D, panel_w=560), lbl) for f, lbl in frames],
        "fig_kink_1d_perturbed_capture.png",
        panel_w=560,
    )

    # Figure: 2D many-particle gas evolution
    frames = [
        ("fig3_frame_a_t0.png", "t = 0.00 fm/c"),
        ("fig3_frame_b_t1.png", "t = 0.11 fm/c"),
        ("fig3_frame_c_t3.png", "t = 0.33 fm/c"),
        ("fig3_frame_d_t6.png", "t = 0.67 fm/c"),
        ("fig3_frame_e_t15.png", "t = 1.67 fm/c"),
    ]
    make_row(
        [(load_panel(f, CROP_BOX_2D3D, panel_w=460), lbl) for f, lbl in frames],
        "fig_kink_2d_many_particle_gas.png",
        panel_w=460,
    )

    # Figure: isolated single-elementary-kink bubble decay
    frames = [
        ("fig4_bubble_t0.png", "t = 0.00 fm/c, A = 8.01%"),
        ("fig4_bubble_t0.5.png", "t = 0.50 fm/c, A = 5.45%"),
        ("fig4_bubble_t1.0.png", "t = 1.00 fm/c, A = 2.23%"),
        ("fig4_bubble_t1.4.png", "t = 1.40 fm/c, A = 0%"),
    ]
    make_row(
        [(load_panel(f, CROP_BOX_2D3D, panel_w=460), lbl) for f, lbl in frames],
        "fig_kink_2d_bubble_decay.png",
        panel_w=460,
    )

    # Figure: 2D triple junction + illustrative proton cluster
    frames = [
        ("fig4_junction_t0.png", "triple junction, t = 0.00 fm/c"),
        ("fig4_junction_t2.5.png", "triple junction, t = 0.28 fm/c"),
        ("fig4_proton_t0.png", "proton (uud), t = 0.00 fm/c"),
        ("fig4_proton_t6.png", "proton (uud), t = 0.67 fm/c"),
    ]
    make_grid(
        [(load_panel(f, CROP_BOX_2D3D, panel_w=560), lbl) for f, lbl in frames],
        ncols=2,
        out_name="fig_kink_2d_junction_proton.png",
        panel_w=560,
    )

    # Figure: 2D coarsening cascade from a genuinely random (unselected)
    # initial condition, "random (self-organizing)" preset -- distinct from
    # the curated 8-particle gas above.
    frames = [
        ("fig_random_frame_a_t0.png", "t = 0.00 fm/c"),
        ("fig_random_frame_b_t033.png", "t = 0.33 fm/c"),
        ("fig_random_frame_c_t133.png", "t = 1.33 fm/c"),
        ("fig_random_frame_d_t533.png", "t = 5.33 fm/c"),
        ("fig_random_frame_e_t1133.png", "t = 11.33 fm/c"),
        ("fig_random_frame_f_t2465.png", "t = 24.65 fm/c"),
    ]
    make_grid(
        [(load_panel(f, CROP_BOX_2D3D_NARROW, panel_w=460), lbl) for f, lbl in frames],
        ncols=3,
        out_name="fig_kink_2d_random_coarsening.png",
        panel_w=460,
    )

    # Figure: 3D extended-structure renders (wall + triple junction)
    frames = [
        ("fig5_wall_lepton_angle1.png", "single wall, far side w=4"),
        ("fig5_wall_upquark_angle2.png", "single wall, far side w=2"),
        ("fig5_junction_context.png", "triple junction, w=2,3,4"),
    ]
    make_row(
        [(load_panel(f, CROP_BOX_2D3D, panel_w=460), lbl) for f, lbl in frames],
        "fig_kink_3d_extended_structure.png",
        panel_w=460,
    )


if __name__ == "__main__":
    main()
