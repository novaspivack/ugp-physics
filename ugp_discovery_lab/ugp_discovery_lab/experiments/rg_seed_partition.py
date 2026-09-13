# ugp_discovery_lab/experiments/rg_seed_partition.py
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Tuple
import json
import math
import numpy as np
from collections import Counter

from .base import Experiment
from ..core.logging import get_logger
from ..core.reporting import write_json_report, write_md_report
from ..core.registry import register_experiment


def _load_rg_summaries(globs: List[str]) -> List[Dict[str, Any]]:
    """Load experiment result files from glob patterns."""
    files = []
    for g in globs:
        files.extend(Path().glob(g))
    out = []
    for f in files:
        try:
            out.append(json.loads(Path(f).read_text()))
        except Exception:
            pass
    return out


def _extract_attractor_from_summary(d: Dict[str, Any]) -> List[Tuple[Tuple[int,int,int], int, str, float]]:
    """
    Return list of (seed_tuple, window, policy, alpha*) per result item.
    Expect structure under d["results"][i]["meta"], ["trajectory"].
    """
    out = []
    for item in d.get("results", []):
        meta = item.get("meta", {})
        seed = meta.get("seed", [None, None, None])
        try:
            seed_t = (int(seed[0]), int(seed[1]), int(seed[2]))
        except Exception:
            continue
        window = int(meta.get("window", -1))
        policy = str(meta.get("policy", "?"))
        traj = item.get("trajectory", [])
        if not traj: 
            continue
        alpha_star = float(traj[-1].get("alpha", math.nan))
        if not np.isfinite(alpha_star): 
            continue
        out.append((seed_t, window, policy, alpha_star))
    return out


def _label_attractor(alpha: float, bins: List[Tuple[float, float, str]]) -> str:
    """
    Map alpha* to attractor label using fixed numeric bins, e.g.:
    [(-0.09,-0.08,'A'), (0.07,0.08,'B'), (0.26,0.27,'C')]
    """
    for lo, hi, lab in bins:
        if lo <= alpha <= hi:
            return lab
    return "UNK"


def _mutual_info_discrete(x: np.ndarray, y: np.ndarray) -> float:
    """Simple MI estimator for discrete labels."""
    n = len(x)
    cx = Counter(x.tolist())
    cy = Counter(y.tolist())
    cxy = Counter(zip(x.tolist(), y.tolist()))
    mi = 0.0
    for (xi, yi), c in cxy.items():
        pxy = c / n
        px = cx[xi] / n
        py = cy[yi] / n
        mi += pxy * math.log((pxy / (px * py + 1e-18)) + 1e-18)
    return float(max(mi, 0.0))


def _create_stability_heatmap(matrix: np.ndarray, xlabels: List[str], ylabels: List[str], 
                             outdir: Path, title: str) -> str:
    """Create a stability heatmap figure."""
    import matplotlib.pyplot as plt
    
    outdir.mkdir(parents=True, exist_ok=True)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(matrix, cmap='RdYlBu_r', aspect='auto')
    
    ax.set_xticks(range(len(xlabels)))
    ax.set_yticks(range(len(ylabels)))
    ax.set_xticklabels(xlabels, rotation=45, ha='right')
    ax.set_yticklabels(ylabels)
    
    ax.set_xlabel('Policy')
    ax.set_ylabel('Window')
    ax.set_title(title)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Attractor Label (A=0, B=1, C=2)')
    
    # Add text annotations
    for i in range(len(ylabels)):
        for j in range(len(xlabels)):
            text = ax.text(j, i, f'{matrix[i, j]:.0f}',
                         ha="center", va="center", color="black" if abs(matrix[i, j]) < 1 else "white")
    
    plt.tight_layout()
    
    # Save figure
    fig_path = outdir / f"{title.lower().replace(' ', '_')}.png"
    fig.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return str(fig_path)


@register_experiment("rg_seed_partition")
class RGSeedPartition(Experiment):
    """
    Classify seeds into RG basins (attractor labels), build a seed→label map,
    and compute mutual information between simple seed features and labels.
    """
    
    def tasks(self) -> List[Dict[str, Any]]:
        return [{"task_id": "rgsp"}]

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger = get_logger("rg_seed_partition", (self.root / "results/logs" / "rg_seed_partition.log"))
        cfg = self.cfg
        inputs = cfg.get("inputs", {}).get("runs", [])
        bins = cfg.get("labels", {}).get("alpha_bins", [
            (-0.09, -0.08, "A"), 
            (0.07, 0.08, "B"), 
            (0.26, 0.27, "C")
        ])

        # Load data
        data = _load_rg_summaries(inputs)
        rows = []
        for d in data:
            rows += _extract_attractor_from_summary(d)

        if not rows:
            logger.warning("No valid attractor data found")
            return {"task_id": "rgsp", "status": "no_data"}

        # Create mapping and MI scores for simple seed features
        seeds, windows, policies, alphas = zip(*rows)
        labels = [_label_attractor(a, bins) for a in alphas]

        # Example simple feature: the third component of the seed triplet
        feat_third = np.asarray([s[2] for s in seeds], dtype=int)
        # Discretize third component into quartiles for MI
        q = np.quantile(feat_third, [0.25, 0.5, 0.75])
        feat_disc = np.digitize(feat_third, q)  # 0..3
        y = np.asarray([{"A": 0, "B": 1, "C": 2, "UNK": 3}[lab] for lab in labels], dtype=int)

        mi_third = _mutual_info_discrete(feat_disc, y)

        # Make a simple seed grid table (seed->label) for a report
        table = [
            {
                "seed": list(seeds[i]), 
                "window": windows[i], 
                "policy": policies[i],
                "alpha_star": alphas[i], 
                "label": labels[i]
            }
            for i in range(len(rows))
        ]

        # Optional heatmap: label stability per window x policy
        uniq_win = sorted(set(windows))
        uniq_pol = sorted(set(policies))
        m = np.zeros((len(uniq_win), len(uniq_pol)))
        
        for iw, w in enumerate(uniq_win):
            for ip, p in enumerate(uniq_pol):
                lab_sub = [labels[i] for i in range(len(rows)) if windows[i] == w and policies[i] == p]
                if lab_sub:
                    # map labels to 0/1/2 for A/B/C, -1 otherwise
                    enc = {"A": 0, "B": 1, "C": 2}.get(max(set(lab_sub), key=lab_sub.count), -1)
                else:
                    enc = -1
                m[iw, ip] = enc

        # Create heatmap figure
        outdir = self.root / "results" / "artifacts" / "rg_seed_partition"
        xlabels = [str(p) for p in uniq_pol]
        ylabels = [str(w) for w in uniq_win]
        fig = _create_stability_heatmap(m, xlabels, ylabels, outdir, "Seed partition modal labels")

        # Calculate label distribution
        label_counts = Counter(labels)
        total_seeds = len(labels)
        
        return {
            "task_id": "rgsp",
            "alpha_bins": bins,
            "mi_seed_third_vs_label": float(mi_third),
            "table": table,
            "fig_paths": [fig],
            "label_distribution": dict(label_counts),
            "total_seeds": total_seeds,
            "status": "ok"
        }

    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        r = results[0] if results else {}
        write_json_report(self.root, "rg_seed_partition_summary", r)
        
        md = [
            "# RG Seed Partition — Summary",
            f"- Alpha bins (label encoding): {r.get('alpha_bins')}",
            f"- Total seeds analyzed: {r.get('total_seeds', 0)}",
            f"- MI(seed_third_quartile; attractor_label) = {r.get('mi_seed_third_vs_label', 0):.4g}",
            "",
            "## Label Distribution",
        ]
        
        for label, count in r.get("label_distribution", {}).items():
            percentage = (count / r.get("total_seeds", 1)) * 100
            md.append(f"- {label}: {count} seeds ({percentage:.1f}%)")
        
        md.extend([
            "",
            "## Sample Rows",
        ])
        
        for row in r.get("table", [])[:20]:
            md.append(f"- seed={row['seed']} window={row['window']} policy={row['policy']} "
                      f"alpha*={row['alpha_star']:.6f} label={row['label']}")
        
        if r.get("fig_paths"):
            md.append("")
            md.append("## Figures")
            for p in r["fig_paths"]:
                md.append(f"![seed_partition]({p})")
        
        write_md_report(self.root, "rg_seed_partition_summary", "\n".join(md))
        return r
