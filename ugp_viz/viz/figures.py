"""
Matplotlib figure routines for VIZLAB.

All figures are written to disk in publication-quality PNG (DPI 150+).
Functions accept already-computed NumPy arrays so the same code can be
called from the CLI, GUI, or experiment runner.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib
matplotlib.use("Agg")  # safe default; GUI re-imports may override
import matplotlib.pyplot as plt
import numpy as np


def _save(fig, filename: str | Path, dpi: int = 150) -> Path:
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_spacetime(
    spacetime: np.ndarray,
    filename: str | Path,
    *,
    title: str = "Spacetime",
    cmap: str = "binary",
    xlabel: str = "Cell position",
    ylabel: str = "Time step",
    dpi: int = 150,
) -> Path:
    """Binary CA spacetime diagram (rows = time, cols = position)."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(spacetime, cmap=cmap, aspect="auto", interpolation="nearest",
              origin="upper")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    return _save(fig, filename, dpi=dpi)


def plot_tau_c_heatmap(
    tau_spacetime: np.ndarray,
    filename: str | Path,
    *,
    title: str = "tau_c heatmap",
    dpi: int = 150,
) -> Path:
    """Hot colormap of tau_c (bright = slow clock = matter)."""
    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(tau_spacetime, cmap="hot", aspect="auto",
                   interpolation="nearest", origin="upper")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("tau_c (inner steps)")
    ax.set_xlabel("Cell position")
    ax.set_ylabel("Time step")
    ax.set_title(title)
    return _save(fig, filename, dpi=dpi)


def plot_tau_c_with_trajectory(
    tau_spacetime: np.ndarray,
    com_positions: Sequence[float],
    filename: str | Path,
    *,
    title: str = "tau_c heatmap with CoM",
    dpi: int = 150,
) -> Path:
    fig, ax = plt.subplots(figsize=(12, 8))
    im = ax.imshow(tau_spacetime, cmap="hot", aspect="auto",
                   interpolation="nearest", origin="upper")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("tau_c (inner steps)")
    valid = [(t, x) for t, x in enumerate(com_positions) if x is not None and not np.isnan(x)]
    if valid:
        ts, xs = zip(*valid)
        ax.plot(xs, ts, color="cyan", linewidth=1.5, alpha=0.85, label="CoM")
        ax.legend(loc="upper right", fontsize=9)
    ax.set_xlabel("Cell position")
    ax.set_ylabel("Time step")
    ax.set_title(title)
    return _save(fig, filename, dpi=dpi)


def plot_tau_c_excess(
    tau_glider: np.ndarray,
    tau_ether: np.ndarray,
    mask: np.ndarray | None,
    filename: str | Path,
    *,
    com_positions: Sequence[float] | None = None,
    title: str = "tau_c excess (glider - ether)",
    dpi: int = 150,
) -> Path:
    excess = tau_glider.astype(np.float32) - tau_ether.astype(np.float32)
    if mask is not None:
        excess = np.where(mask, excess, np.nan)
    fig, ax = plt.subplots(figsize=(12, 8))
    unmasked = excess[~np.isnan(excess)]
    vmax = float(np.percentile(np.abs(unmasked), 97)) if unmasked.size else 1.0
    vmax = max(vmax, 0.5)
    im = ax.imshow(excess, cmap="RdBu_r", aspect="auto",
                   interpolation="nearest", origin="upper",
                   vmin=-vmax, vmax=vmax)
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("tau_c(glider) - tau_c(ether)")
    ax.set_facecolor("white")
    if com_positions:
        valid = [(t, x) for t, x in enumerate(com_positions)
                 if x is not None and not np.isnan(x)]
        if valid:
            ts, xs = zip(*valid)
            ax.plot(xs, ts, color="cyan", linewidth=2.0,
                    alpha=0.9, label="CoM")
            ax.legend(loc="upper right", fontsize=10)
    ax.set_xlabel("Cell position")
    ax.set_ylabel("Time step")
    ax.set_title(title)
    return _save(fig, filename, dpi=dpi)


def plot_clock_speed_comparison(
    tau_ether: np.ndarray,
    tau_glider: np.ndarray,
    filename: str | Path,
    *,
    com_positions: Sequence[float] | None = None,
    title: str = "Clock speed: vacuum baseline vs matter dilation",
    dpi: int = 150,
) -> Path:
    tau_ether_mean = float(tau_ether.mean())
    dev_e = (tau_ether - tau_ether_mean) / max(tau_ether_mean, 1e-6)
    dev_g = (tau_glider - tau_ether_mean) / max(tau_ether_mean, 1e-6)
    vmax = float(np.percentile(np.abs(dev_g), 97))
    vmax = max(vmax, 1e-3)
    fig, axes = plt.subplots(1, 2, figsize=(20, 8))
    im0 = axes[0].imshow(dev_e, cmap="RdBu_r", aspect="auto",
                         interpolation="nearest", origin="upper",
                         vmin=-vmax, vmax=vmax)
    fig.colorbar(im0, ax=axes[0]).set_label("(tau - tau_ether)/tau_ether")
    axes[0].set_title("Ether baseline")
    axes[0].set_xlabel("Cell")
    axes[0].set_ylabel("Time")
    im1 = axes[1].imshow(dev_g, cmap="RdBu_r", aspect="auto",
                         interpolation="nearest", origin="upper",
                         vmin=-vmax, vmax=vmax)
    fig.colorbar(im1, ax=axes[1]).set_label("(tau - tau_ether)/tau_ether")
    axes[1].set_title("Matter run")
    axes[1].set_xlabel("Cell")
    if com_positions:
        valid = [(t, x) for t, x in enumerate(com_positions)
                 if x is not None and not np.isnan(x)]
        if valid:
            ts, xs = zip(*valid)
            axes[1].plot(xs, ts, color="cyan", linewidth=2.0,
                         alpha=0.9, label="CoM")
            axes[1].legend(loc="upper right", fontsize=10)
    fig.suptitle(title)
    fig.tight_layout()
    return _save(fig, filename, dpi=dpi)


def plot_field_1d(
    field: np.ndarray,
    filename: str | Path,
    *,
    label: str = "phi",
    title: str = "Field profile",
    dpi: int = 150,
    extra_curves: dict[str, np.ndarray] | None = None,
) -> Path:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(field, label=label, color="C0", linewidth=1.5)
    if extra_curves:
        for name, arr in extra_curves.items():
            ax.plot(arr, label=name, linewidth=1.0, alpha=0.85)
    ax.set_xlabel("Cell position")
    ax.set_ylabel("Field amplitude")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=9)
    return _save(fig, filename, dpi=dpi)


def plot_field_3d_slice(
    slice_2d: np.ndarray,
    filename: str | Path,
    *,
    axis: int = 2,
    index: int = 0,
    title: str | None = None,
    cmap: str = "viridis",
    dpi: int = 150,
    field_name: str = "phi",
) -> Path:
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(slice_2d.T, cmap=cmap, origin="lower", aspect="auto")
    fig.colorbar(im, ax=ax).set_label(field_name)
    axnames = ("x", "y", "z")
    plane = "".join(c for i, c in enumerate(axnames) if i != axis)
    ax.set_title(title or f"{field_name} slice @ {axnames[axis]}={index}")
    ax.set_xlabel(plane[0])
    ax.set_ylabel(plane[1])
    return _save(fig, filename, dpi=dpi)


def plot_field_3d_three_slice(
    volume: np.ndarray,
    filename: str | Path,
    *,
    centers: tuple[int, int, int] | None = None,
    title: str = "3D field — three axis-aligned slices",
    cmap: str = "viridis",
    dpi: int = 150,
    field_name: str = "phi",
) -> Path:
    Nx, Ny, Nz = volume.shape
    cx, cy, cz = centers or (Nx // 2, Ny // 2, Nz // 2)
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    vmin = float(volume.min())
    vmax = float(volume.max())
    if vmin == vmax:
        vmax = vmin + 1e-9
    im0 = axes[0].imshow(volume[cx, :, :].T, cmap=cmap, origin="lower",
                         vmin=vmin, vmax=vmax)
    axes[0].set_title(f"YZ @ x={cx}")
    axes[0].set_xlabel("y"); axes[0].set_ylabel("z")
    im1 = axes[1].imshow(volume[:, cy, :].T, cmap=cmap, origin="lower",
                         vmin=vmin, vmax=vmax)
    axes[1].set_title(f"XZ @ y={cy}")
    axes[1].set_xlabel("x"); axes[1].set_ylabel("z")
    im2 = axes[2].imshow(volume[:, :, cz].T, cmap=cmap, origin="lower",
                         vmin=vmin, vmax=vmax)
    axes[2].set_title(f"XY @ z={cz}")
    axes[2].set_xlabel("x"); axes[2].set_ylabel("y")
    fig.colorbar(im2, ax=axes, fraction=0.04, pad=0.02).set_label(field_name)
    fig.suptitle(title)
    return _save(fig, filename, dpi=dpi)


def plot_field_3d_volumetric(
    volume: np.ndarray,
    filename: str | Path,
    *,
    title: str = "3D field — volumetric (alpha-blended ray cast)",
    cmap: str = "viridis",
    n_samples: int = 96,
    azim: float = 35.0,
    elev: float = 22.0,
    extent: tuple[float, float, float, float, float, float] | None = None,
    background: tuple[float, float, float] = (0.04, 0.04, 0.05),
    alpha_gain: float = 1.0,
    dpi: int = 150,
) -> Path:
    """Render a true alpha-blended volumetric ray-cast view of a 3D field.

    The volume is mapped to per-voxel emission (via ``cmap``) and density
    (via ``|f - mean(f)|`` normalized). We trace ``n_samples`` parallel
    rays per pixel along the +z direction in camera space, accumulating
    front-to-back with the standard premultiplied-alpha compositing
    equation. The viewing direction is set by ``azim`` and ``elev``
    (degrees, matplotlib convention). Output is a single PNG figure.

    This complements ``plot_field_3d_three_slice`` (axis-aligned slices)
    and ``plot_field_3d_isosurface`` (marching-cubes mesh) — pick the
    representation that best shows the structure of interest.
    """
    from matplotlib.colors import Normalize
    Nx, Ny, Nz = volume.shape
    f = np.asarray(volume, dtype=np.float32)
    f_mean = float(f.mean())
    density = np.abs(f - f_mean)
    d_max = float(density.max())
    if d_max <= 0:
        density = np.zeros_like(density)
    else:
        density = density / d_max
    vmin, vmax = float(f.min()), float(f.max())
    if vmax <= vmin:
        vmax = vmin + 1e-9
    norm = Normalize(vmin=vmin, vmax=vmax)
    cmap_obj = plt.get_cmap(cmap)

    # Camera-space sampling grid.
    img_w = max(192, min(Nx * 4, 384))
    img_h = max(192, min(Ny * 4, 384))
    img = np.zeros((img_h, img_w, 3), dtype=np.float32) + np.array(background)
    accum_alpha = np.zeros((img_h, img_w), dtype=np.float32)

    az = np.deg2rad(azim)
    el = np.deg2rad(elev)
    # Forward = into the scene
    forward = np.array([np.cos(el) * np.cos(az),
                        np.cos(el) * np.sin(az),
                        np.sin(el)], dtype=np.float32)
    # Right and up vectors orthonormal to forward
    world_up = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    right = np.cross(forward, world_up)
    nrm = np.linalg.norm(right)
    right = right / nrm if nrm > 1e-9 else np.array([1.0, 0.0, 0.0])
    up = np.cross(right, forward)

    half_extent = 0.6 * max(Nx, Ny, Nz)
    cx_, cy_, cz_ = (Nx - 1) / 2.0, (Ny - 1) / 2.0, (Nz - 1) / 2.0

    u_lin = (np.linspace(-1.0, 1.0, img_w) * half_extent).astype(np.float32)
    v_lin = (np.linspace(-1.0, 1.0, img_h) * half_extent).astype(np.float32)
    uu, vv = np.meshgrid(u_lin, v_lin, indexing="xy")

    # For each ray (one per pixel), step from front to back along forward.
    t_lin = np.linspace(-half_extent, half_extent, n_samples, dtype=np.float32)
    step = (t_lin[1] - t_lin[0]) if n_samples > 1 else 1.0
    alpha_scale = alpha_gain * step / (max(Nx, Ny, Nz) / float(n_samples))

    for tval in t_lin:
        # World-space sample point per pixel
        x = cx_ + uu * right[0] + vv * up[0] + tval * forward[0]
        y = cy_ + uu * right[1] + vv * up[1] + tval * forward[1]
        z = cz_ + uu * right[2] + vv * up[2] + tval * forward[2]
        ix = np.clip(np.round(x).astype(np.int32), 0, Nx - 1)
        iy = np.clip(np.round(y).astype(np.int32), 0, Ny - 1)
        iz = np.clip(np.round(z).astype(np.int32), 0, Nz - 1)
        in_box = (
            (x >= 0) & (x <= Nx - 1) &
            (y >= 0) & (y <= Ny - 1) &
            (z >= 0) & (z <= Nz - 1)
        )
        sample = f[ix, iy, iz]
        d = density[ix, iy, iz] * in_box
        rgb = cmap_obj(norm(sample))[..., :3].astype(np.float32)
        a = 1.0 - np.exp(-alpha_scale * d)
        new_a = accum_alpha + (1.0 - accum_alpha) * a
        contrib = (1.0 - accum_alpha)[..., None] * a[..., None] * rgb
        img += contrib
        accum_alpha = new_a

    fig, ax = plt.subplots(figsize=(7, 7), facecolor=background)
    ax.imshow(img, origin="lower", interpolation="bilinear")
    ax.set_axis_off()
    ax.set_title(f"{title}\nazim={azim:.0f}°, elev={elev:.0f}°, "
                 f"samples={n_samples}", color="white")
    fig.patch.set_facecolor(background)
    return _save(fig, filename, dpi=dpi)


def plot_field_3d_isosurface(
    volume: np.ndarray,
    filename: str | Path,
    *,
    iso_level: float | None = None,
    title: str = "3D field — marching-cubes isosurface",
    color: str = "C2",
    edge_alpha: float = 0.05,
    azim: float = 35.0,
    elev: float = 22.0,
    dpi: int = 150,
) -> Path:
    """Render a marching-cubes isosurface of a 3D field.

    Uses ``skimage.measure.marching_cubes`` when scikit-image is
    available (high-quality mesh); falls back to a voxel point-cloud
    rendered as a 3D scatter plot otherwise (still informative for a
    quick look at where the kink is).

    ``iso_level`` defaults to the field's mean. For a Phi_MDL kink in
    Z₇ × Z₃, the field oscillates around 0; passing ``iso_level=0`` will
    show the domain-wall manifold.
    """
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers 3d projection)
    f = np.asarray(volume, dtype=np.float32)
    if iso_level is None:
        iso_level = float(f.mean())
    fig = plt.figure(figsize=(8, 7))
    ax = fig.add_subplot(111, projection="3d")
    used_marching_cubes = False
    try:
        from skimage.measure import marching_cubes  # type: ignore
        verts, faces, _, _ = marching_cubes(f, level=float(iso_level))
        from matplotlib.colors import to_rgba
        rgba = to_rgba(color)
        ax.plot_trisurf(
            verts[:, 0], verts[:, 1], faces, verts[:, 2],
            color=rgba, alpha=0.85, linewidth=0.0,
            edgecolor=(0, 0, 0, edge_alpha),
            antialiased=True,
        )
        used_marching_cubes = True
    except Exception:
        # Voxel fallback: pick the |f - level| smallest 1% as a point cloud
        delta = np.abs(f - iso_level)
        thresh = float(np.quantile(delta, 0.01))
        mask = delta <= thresh
        xs, ys, zs = np.where(mask)
        # Subsample if too many points
        if xs.size > 30000:
            idx = np.random.default_rng(0).choice(xs.size, size=30000,
                                                    replace=False)
            xs, ys, zs = xs[idx], ys[idx], zs[idx]
        ax.scatter(xs, ys, zs, c=color, s=2, alpha=0.5)
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")
    ax.set_xlim(0, f.shape[0]); ax.set_ylim(0, f.shape[1])
    ax.set_zlim(0, f.shape[2])
    ax.view_init(elev=elev, azim=azim)
    suffix = (" (marching cubes)" if used_marching_cubes
              else " (voxel fallback — install scikit-image for mesh)")
    ax.set_title(f"{title}\niso={iso_level:.4f}{suffix}")
    return _save(fig, filename, dpi=dpi)


def plot_energy_trace(
    times: np.ndarray,
    energies: np.ndarray,
    filename: str | Path,
    *,
    title: str = "Energy E(t)",
    dpi: int = 150,
) -> Path:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(times, energies, color="C3", linewidth=1.5)
    ax.set_xlabel("Time")
    ax.set_ylabel("Total energy")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    return _save(fig, filename, dpi=dpi)


def plot_sr_error(
    velocities: Sequence[float],
    gamma_theory: Sequence[float],
    gamma_measured: Sequence[float],
    filename: str | Path,
    *,
    title: str = "SR check: gamma_measured vs gamma_theory",
    dpi: int = 150,
) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].plot(velocities, gamma_theory, "k-", label=r"$\gamma_{theory}$")
    axes[0].plot(velocities, gamma_measured, "C0o", label=r"$\gamma_{meas}$")
    axes[0].set_xlabel("v / c")
    axes[0].set_ylabel("gamma")
    axes[0].set_title("gamma comparison")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(fontsize=9)
    err = [abs(m / max(t, 1e-12) - 1.0) * 100 for m, t in zip(gamma_measured, gamma_theory)]
    axes[1].plot(velocities, err, "C3o-")
    axes[1].set_xlabel("v / c")
    axes[1].set_ylabel("SR error (%)")
    axes[1].set_title("SR error")
    axes[1].grid(True, alpha=0.3)
    fig.suptitle(title)
    fig.tight_layout()
    return _save(fig, filename, dpi=dpi)
