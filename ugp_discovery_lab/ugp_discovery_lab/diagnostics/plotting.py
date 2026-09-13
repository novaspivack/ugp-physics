"""
Visualization export system for UGP Discovery Lab.
"""

import os
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
import warnings

# Optional matplotlib import with graceful fallback
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.colors import LinearSegmentedColormap
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    warnings.warn("matplotlib not available - plotting disabled")


def is_plotting_available() -> bool:
    """Check if plotting is available."""
    return MATPLOTLIB_AVAILABLE


def create_heatmap(
    data: np.ndarray,
    x_labels: List[str],
    y_labels: List[str],
    title: str,
    xlabel: str,
    ylabel: str,
    cmap: str = "viridis"
) -> Optional[plt.Figure]:
    """
    Create a heatmap visualization.
    
    Args:
        data: 2D array of data
        x_labels: Labels for x-axis
        y_labels: Labels for y-axis
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        cmap: Colormap name
    
    Returns:
        Matplotlib figure or None if plotting unavailable
    """
    if not MATPLOTLIB_AVAILABLE:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create heatmap
    im = ax.imshow(data, cmap=cmap, aspect='auto')
    
    # Set labels
    ax.set_xticks(range(len(x_labels)))
    ax.set_yticks(range(len(y_labels)))
    ax.set_xticklabels(x_labels)
    ax.set_yticklabels(y_labels)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Value', rotation=270, labelpad=15)
    
    # Add text annotations
    for i in range(len(y_labels)):
        for j in range(len(x_labels)):
            text = ax.text(j, i, f'{data[i, j]:.3f}',
                         ha="center", va="center", color="white" if data[i, j] < 0.5 else "black")
    
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    
    plt.tight_layout()
    return fig


def plot_trajectory(
    x_data: List[float],
    y_data: List[float],
    title: str,
    xlabel: str,
    ylabel: str,
    color: str = "blue",
    marker: str = "o"
) -> Optional[plt.Figure]:
    """
    Create a trajectory plot.
    
    Args:
        x_data: X-axis data
        y_data: Y-axis data
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        color: Line color
        marker: Marker style
    
    Returns:
        Matplotlib figure or None if plotting unavailable
    """
    if not MATPLOTLIB_AVAILABLE:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(x_data, y_data, color=color, marker=marker, linewidth=2, markersize=4)
    
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def plot_rg_trajectory(
    trajectory: List[Dict[str, Any]],
    title: str = "RG Flow Trajectory"
) -> Optional[plt.Figure]:
    """
    Create RG flow trajectory visualization.
    
    Args:
        trajectory: List of trajectory points
        title: Plot title
    
    Returns:
        Matplotlib figure or None if plotting unavailable
    """
    if not MATPLOTLIB_AVAILABLE or not trajectory:
        return None
    
    # Extract data
    iterations = list(range(len(trajectory)))
    alphas = [point.get("alpha", 0) for point in trajectory]
    errors = [point.get("plane_error", 0) for point in trajectory]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot alpha evolution
    ax1.plot(iterations, alphas, 'b-o', linewidth=2, markersize=4)
    ax1.axhline(y=0.25, color='r', linestyle='--', alpha=0.7, label='Quarter-Lock (0.25)')
    ax1.set_title(f"{title} - Alpha Evolution")
    ax1.set_xlabel("RG Iteration")
    ax1.set_ylabel("Alpha")
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Plot error evolution
    ax2.plot(iterations, errors, 'g-o', linewidth=2, markersize=4)
    ax2.set_title("Plane Error Evolution")
    ax2.set_xlabel("RG Iteration")
    ax2.set_ylabel("Plane Error")
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale('log')
    
    plt.tight_layout()
    return fig


def save_plot(fig: Optional[plt.Figure], output_path: Path, 
              dpi: int = 300, bbox_inches: str = "tight") -> bool:
    """
    Save a matplotlib figure to file.
    
    Args:
        fig: Matplotlib figure
        output_path: Output file path
        dpi: Resolution
        bbox_inches: Bounding box setting
    
    Returns:
        True if saved successfully, False otherwise
    """
    if not MATPLOTLIB_AVAILABLE or fig is None:
        return False
    
    try:
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save figure
        fig.savefig(output_path, dpi=dpi, bbox_inches=bbox_inches)
        plt.close(fig)  # Free memory
        return True
        
    except Exception as e:
        warnings.warn(f"Failed to save plot to {output_path}: {e}")
        return False


def create_lock_stability_heatmap(
    stability_results: List[Dict[str, Any]],
    output_path: Path
) -> bool:
    """
    Create heatmap for lock stability results.
    
    Args:
        stability_results: List of stability test results
        output_path: Output file path
    
    Returns:
        True if created successfully
    """
    if not MATPLOTLIB_AVAILABLE or not stability_results:
        return False
    
    # Extract data for heatmap
    seeds = set()
    windows = set()
    laws = set()
    
    for result in stability_results:
        if "seed" in result:
            seeds.add(str(result["seed"]))
        if "window" in result:
            windows.add(result["window"])
        if "law" in result:
            laws.add(str(result["law"]))
    
    # Create stability score matrix
    stability_matrix = np.zeros((len(windows), len(seeds)))
    seed_list = sorted(list(seeds))
    window_list = sorted(list(windows))
    
    for result in stability_results:
        if "window" in result and "seed" in result and "stability_score" in result:
            try:
                w_idx = window_list.index(result["window"])
                s_idx = seed_list.index(str(result["seed"]))
                stability_matrix[w_idx, s_idx] = result["stability_score"]
            except ValueError:
                continue
    
    # Create heatmap
    fig = create_heatmap(
        stability_matrix,
        seed_list,
        [f"Window {w}" for w in window_list],
        "Lock Stability Heatmap",
        "Seed",
        "Window Size",
        cmap="RdYlGn"
    )
    
    if fig is not None:
        return save_plot(fig, output_path)
    
    return False


def create_rg_flow_plots(
    rg_results: List[Dict[str, Any]],
    output_dir: Path
) -> List[Path]:
    """
    Create RG flow trajectory plots.
    
    Args:
        rg_results: List of RG flow results
        output_dir: Output directory
    
    Returns:
        List of created plot file paths
    """
    created_plots = []
    
    if not MATPLOTLIB_AVAILABLE:
        return created_plots
    
    for i, result in enumerate(rg_results):
        if not result.get("success", False):
            continue
        
        analysis = result.get("analysis", {})
        trajectory = analysis.get("rg_trajectory", [])
        
        if not trajectory:
            continue
        
        # Create trajectory plot
        fig = plot_rg_trajectory(
            trajectory,
            f"RG Flow Trajectory - Task {result.get('task_id', i)}"
        )
        
        if fig is not None:
            plot_path = output_dir / f"rg_trajectory_{i:03d}.png"
            if save_plot(fig, plot_path):
                created_plots.append(plot_path)
    
    return created_plots


def export_experiment_plots(
    experiment_name: str,
    results: List[Dict[str, Any]],
    output_dir: Path,
    enable_plots: bool = True
) -> List[Path]:
    """
    Export plots for an experiment based on its type.
    
    Args:
        experiment_name: Name of the experiment
        results: List of experiment results
        output_dir: Output directory
        enable_plots: Whether to create plots
    
    Returns:
        List of created plot file paths
    """
    if not enable_plots or not MATPLOTLIB_AVAILABLE:
        return []
    
    created_plots = []
    
    # Create experiment-specific plots
    if experiment_name == "lock_stability":
        heatmap_path = output_dir / "stability_heatmap.png"
        if create_lock_stability_heatmap(results, heatmap_path):
            created_plots.append(heatmap_path)
    
    elif experiment_name == "rg_flow":
        rg_plots = create_rg_flow_plots(results, output_dir)
        created_plots.extend(rg_plots)
    
    return created_plots


# Advanced plotting functions for publication-quality figures

def fig_alpha_distributions(alpha_records: List[Dict[str, Any]], outdir: str | Path, title: str) -> str:
    """
    Create alpha distribution plots for publication.
    
    Args:
        alpha_records: List of dicts with {"alpha": float, "policy": str, "seed": str/int, "window": int}
        outdir: Output directory
        title: Plot title
    
    Returns:
        Path to saved figure
    """
    if not MATPLOTLIB_AVAILABLE:
        return ""
    
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    fig, ax = plt.subplots(figsize=(8, 5))
    alphas = [r["alpha"] for r in alpha_records if "alpha" in r]
    labels = [f'{r.get("policy","?")}|s{r.get("seed","?")}|n{r.get("window","?")}' for r in alpha_records]
    
    # Try to use seaborn if available
    try:
        import seaborn as sns
        sns.boxplot(x=labels, y=alphas, ax=ax)
        sns.stripplot(x=labels, y=alphas, ax=ax, color="black", size=2, alpha=0.6)
    except ImportError:
        ax.boxplot(alphas, vert=True)
        ax.plot(range(1, len(alphas)+1), alphas, "ko", ms=2, alpha=0.6)
        ax.set_xticks(range(1, len(alphas)+1))
        ax.set_xticklabels(labels, rotation=90)

    ax.set_title(title)
    ax.set_ylabel("alpha")
    fig.tight_layout()
    out = outdir / "fig_alpha_distributions.png"
    fig.savefig(out, dpi=175)
    plt.close(fig)
    return str(out)


def fig_rg_trajectories(trajectories: List[Dict[str, Any]], outdir: str | Path, title: str) -> List[str]:
    """
    Create RG trajectory plots for publication.
    
    Args:
        trajectories: List of {"name": str, "alpha_series": [float,...]}
        outdir: Output directory
        title: Plot title
    
    Returns:
        List of saved figure paths
    """
    if not MATPLOTLIB_AVAILABLE:
        return []
    
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    figs = []
    
    # Spaghetti plot
    fig, ax = plt.subplots(figsize=(7, 4))
    for tr in trajectories:
        s = tr.get("alpha_series", [])
        ax.plot(range(len(s)), s, alpha=0.5, lw=1)
    ax.set_title(f"{title} (trajectories)")
    ax.set_xlabel("iteration")
    ax.set_ylabel("alpha")
    fig.tight_layout()
    out1 = outdir / "fig_rg_spaghetti.png"
    fig.savefig(out1, dpi=175)
    plt.close(fig)
    figs.append(str(out1))

    # Mean with CI (if lengths align)
    max_len = max((len(t.get("alpha_series", [])) for t in trajectories), default=0)
    if max_len > 0:
        arr = []
        for t in trajectories:
            s = t.get("alpha_series", [])
            if len(s) == max_len:
                arr.append(s)
        if len(arr) >= 2:
            arr = np.asarray(arr, dtype=float)
            mean = arr.mean(axis=0)
            std = arr.std(axis=0)
            fig2, ax2 = plt.subplots(figsize=(7, 4))
            x = np.arange(max_len)
            ax2.plot(x, mean, lw=2, color="tab:blue", label="mean")
            ax2.fill_between(x, mean-1.96*std, mean+1.96*std, color="tab:blue", alpha=0.25, label="95% CI")
            ax2.set_title(f"{title} (mean ± 95% CI)")
            ax2.set_xlabel("iteration")
            ax2.set_ylabel("alpha")
            ax2.legend()
            fig2.tight_layout()
            out2 = outdir / "fig_rg_mean_ci.png"
            fig2.savefig(out2, dpi=175)
            plt.close(fig2)
            figs.append(str(out2))
    
    return figs


def fig_dihedral_alpha_vs_n(results_per_n: List[Dict[str, Any]], overlay_theory: bool, outdir: str | Path, title: str) -> str:
    """
    Create dihedral alpha vs n plots.
    
    Args:
        results_per_n: List of {"n": int, "alpha_hat": float, "ci": [float, float]}
        overlay_theory: Whether to overlay theoretical values
        outdir: Output directory
        title: Plot title
    
    Returns:
        Path to saved figure
    """
    if not MATPLOTLIB_AVAILABLE:
        return ""
    
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    ns = [r["n"] for r in results_per_n]
    alphas = [r["alpha_hat"] for r in results_per_n]
    ci_lo = [r.get("ci", [None, None])[0] for r in results_per_n]
    ci_hi = [r.get("ci", [None, None])[1] for r in results_per_n]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.errorbar(ns, alphas, yerr=[np.array(alphas)-np.array(ci_lo), np.array(ci_hi)-np.array(alphas)], 
                fmt="o", capsize=3, label="empirical")
    
    if overlay_theory:
        theo = []
        for n in ns:
            try:
                val = 1.0 / (2.0 * np.cos(np.pi / n))
            except Exception:
                val = np.nan
            theo.append(val)
        ax.plot(ns, theo, "s--", label="1/(2cos(pi/n))", alpha=0.7)
    
    ax.set_xlabel("n")
    ax.set_ylabel("alpha_hat")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    out = outdir / "fig_dihedral_alpha_vs_n.png"
    fig.savefig(out, dpi=175)
    plt.close(fig)
    return str(out)


def fig_noether_dJ_series(dJ_series: np.ndarray, outdir: str | Path, title: str) -> List[str]:
    """
    Create Noether current ΔJ series plots.
    
    Args:
        dJ_series: Array of ΔJ values
        outdir: Output directory
        title: Plot title
    
    Returns:
        List of saved figure paths
    """
    if not MATPLOTLIB_AVAILABLE:
        return []
    
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    figs = []
    
    # Time series plot
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.plot(dJ_series, "k-", lw=1)
    ax.set_title(title + " (ΔJ time series)")
    ax.set_xlabel("t")
    ax.set_ylabel("ΔJ")
    fig.tight_layout()
    out1 = outdir / "fig_noether_dJ_series.png"
    fig.savefig(out1, dpi=175)
    plt.close(fig)
    figs.append(str(out1))

    # Histogram
    fig2, ax2 = plt.subplots(figsize=(5, 3))
    ax2.hist(np.abs(dJ_series), bins=40, color="tab:orange", alpha=0.8)
    ax2.set_title(title + " (|ΔJ| histogram)")
    ax2.set_xlabel("|ΔJ|")
    fig2.tight_layout()
    out2 = outdir / "fig_noether_dJ_hist.png"
    fig2.savefig(out2, dpi=175)
    plt.close(fig2)
    figs.append(str(out2))

    return figs


def fig_plane_residuals(points: np.ndarray, plane_params: Dict[str, float], outdir: str | Path, title: str) -> List[str]:
    """
    Create plane residual plots.
    
    Args:
        points: Nx3 array of (kG, kL, kM)
        plane_params: Dict with 'a','b','c' for kM = a*kG + b*kL + c
        outdir: Output directory
        title: Plot title
    
    Returns:
        List of saved figure paths
    """
    if not MATPLOTLIB_AVAILABLE:
        return []
    
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    a, b, c = plane_params.get("a", 1.0), plane_params.get("b", 0.0), plane_params.get("c", 0.0)
    kG, kL, kM = points[:, 0], points[:, 1], points[:, 2]
    resid = kM - (a * kG + b * kL + c)

    figs = []
    
    # Scatter residuals
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(resid, "k.", alpha=0.6)
    ax.set_title(title + " (residual scatter)")
    ax.set_xlabel("index")
    ax.set_ylabel("residual")
    fig.tight_layout()
    out1 = outdir / "fig_plane_resid_scatter.png"
    fig.savefig(out1, dpi=175)
    plt.close(fig)
    figs.append(str(out1))

    # QQ plot
    try:
        from scipy import stats
        fig2, ax2 = plt.subplots(figsize=(4, 4))
        stats.probplot(resid, dist="norm", plot=ax2)
        ax2.set_title(title + " (QQ plot)")
        fig2.tight_layout()
        out2 = outdir / "fig_plane_resid_qq.png"
        fig2.savefig(out2, dpi=175)
        plt.close(fig2)
        figs.append(str(out2))
    except ImportError:
        pass  # scipy not available

    return figs


def fig_changepoints(alpha_series: np.ndarray, detected_points: List[int], outdir: str | Path, title: str) -> str:
    """
    Create change-point detection plots.
    
    Args:
        alpha_series: Array of alpha values over time
        detected_points: List of detected change-point indices
        outdir: Output directory
        title: Plot title
    
    Returns:
        Path to saved figure
    """
    if not MATPLOTLIB_AVAILABLE:
        return ""
    
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.plot(alpha_series, "k-", lw=1)
    for cp in detected_points:
        ax.axvline(cp, color="red", ls="--", lw=1, alpha=0.7)
    ax.set_title(title + " (alpha change-points)")
    ax.set_xlabel("t")
    ax.set_ylabel("alpha")
    fig.tight_layout()
    out = outdir / "fig_alpha_changepoints.png"
    fig.savefig(out, dpi=175)
    plt.close(fig)
    return str(out)
