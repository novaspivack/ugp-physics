"""
TE_1.C Phase 1 pipeline runner.

Coordinates FRW background scans, G(k) running estimates, ringdown diagnostics,
Yukawa fits, and stability checks as described in TE_1.C.1_PLAN.md.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

try:
    from .config_loader import load_config
    from .frw_background import (
        FRWInitialConditions,
        FRWModelConfig,
        FRWRunResult,
        generate_frw_figures,
        run_frw_grid,
        save_frw_results,
    )
    from .g_running import GRGConfig, compute_running, plot_running, save_running
    from .ringdown import RingdownConfig, compute_ringdown, plot_ringdown, save_ringdown
    from .stability import StabilityConfig, run_stability, save_stability
    from .yukawa_ppn import YukawaConfig, plot_yukawa, run_yukawa, save_yukawa
    from .spectra_analytic import (
        compute_slow_roll_spectra,
        plot_spectrum_points,
        run_background_for_spectra,
        save_spectrum_points,
    )
except ImportError:  # pragma: no cover
    import sys

    PACKAGE_ROOT = Path(__file__).resolve().parent
    if str(PACKAGE_ROOT) not in sys.path:
        sys.path.append(str(PACKAGE_ROOT))
    from config_loader import load_config
    from frw_background import (
        FRWInitialConditions,
        FRWModelConfig,
        FRWRunResult,
        generate_frw_figures,
        run_frw_grid,
        save_frw_results,
    )
    from g_running import GRGConfig, compute_running, plot_running, save_running
    from ringdown import RingdownConfig, compute_ringdown, plot_ringdown, save_ringdown
    from stability import StabilityConfig, run_stability, save_stability
    from yukawa_ppn import YukawaConfig, plot_yukawa, run_yukawa, save_yukawa
    from spectra_analytic import (
        compute_slow_roll_spectra,
        plot_spectrum_points,
        run_background_for_spectra,
        save_spectrum_points,
    )


@dataclass
class Phase1ConfigPaths:
    frw: Path
    g_running: Path
    spectra: Path
    ringdown: Path
    yukawa: Path
    stability: Path


class Phase1Runner:
    def __init__(self, root: Path):
        self.root = root
        self.config_dir = root / "configs"
        self.results_dir = root / "results"
        self.figs_dir = root / "figs"
        self.logs_dir = root / "logs"

    def config_paths(self) -> Phase1ConfigPaths:
        return Phase1ConfigPaths(
            frw=self.config_dir / "frw.yaml",
            g_running=self.config_dir / "g_running.yaml",
            spectra=self.config_dir / "spectra_slow_roll.yaml",
            ringdown=self.config_dir / "ringdown.yaml",
            yukawa=self.config_dir / "yukawa.yaml",
            stability=self.config_dir / "stability.yaml",
        )

    def run(self) -> Dict[str, Dict[str, float]]:
        paths = self.config_paths()
        summaries: Dict[str, Dict[str, float]] = {}

        self._log("Running FRW background grid")
        frw_results = self._run_frw(paths.frw)
        summaries["frw"] = self._summarize_frw(frw_results)

        self._log("Evaluating G(k) running")
        g_result = self._run_g_running(paths.g_running)
        summaries["g_running"] = g_result.to_summary()

        if paths.spectra.exists():
            self._log("Computing analytic spectra")
            spectra_summary = self._run_spectra(paths.spectra)
            summaries["spectra"] = spectra_summary

        self._log("Running ringdown diagnostics")
        ringdown_result = self._run_ringdown(paths.ringdown)
        summaries["ringdown"] = ringdown_result.to_summary()

        self._log("Evaluating Yukawa / PPN profile")
        yukawa_result = self._run_yukawa(paths.yukawa)
        summaries["yukawa"] = yukawa_result.to_summary()

        self._log("Running stability checks")
        stability_result = self._run_stability(paths.stability)
        summaries["stability"] = stability_result.to_summary()

        self._write_overall_summary(summaries)
        return summaries

    def _run_frw(self, path: Path) -> List[FRWRunResult]:
        cfg_dict = load_config(path)
        ic = FRWInitialConditions(**cfg_dict["initial_conditions"])
        base_model = cfg_dict["model_defaults"]
        grid = cfg_dict["grid"]

        configs: List[FRWModelConfig] = []
        for m in grid["m"]:
            for beta in grid["beta"]:
                for omega_bar in grid["omega_bar"]:
                    for rf in grid["rf_bar"]:
                        cfg = FRWModelConfig(
                            m=m,
                            beta=beta,
                            omega_bar=omega_bar,
                            rf_bar=rf,
                            hubble_constant=base_model.get("hubble_constant", FRWModelConfig.__dataclass_fields__["hubble_constant"].default),
                            omega_m0=base_model.get("omega_m0", 0.3),
                            zmax=base_model.get("zmax", 2.0),
                            nsteps=base_model.get("nsteps", 1800),
                        )
                        configs.append(cfg)

        results = run_frw_grid(
            configs,
            ic,
            progress_callback=lambda idx, total, _cfg: self._progress("FRW grid", idx, total),
        )
        save_frw_results(results, self.results_dir)
        generate_frw_figures(results, self.figs_dir)
        return results

    def _summarize_frw(self, results: Iterable[FRWRunResult]) -> Dict[str, float]:
        import numpy as np

        results_list = list(results)
        w0 = np.array([r.diagnostics.w0_psi for r in results_list])
        wa = np.array([r.diagnostics.wa_psi for r in results_list])
        return {
            "w0_mean": float(w0.mean()),
            "w0_std": float(w0.std()),
            "wa_max_abs": float(np.max(np.abs(wa))),
            "cases": len(results_list),
        }

    def _run_g_running(self, path: Path):
        cfg = GRGConfig(**load_config(path))
        result = compute_running(cfg)
        save_running(result, self.results_dir)
        plot_running(result, self.figs_dir)
        return result

    def _run_spectra(self, path: Path) -> Dict[str, float]:
        cfg_dict = load_config(path)
        stem = cfg_dict.get("stem", "spectra_slow_roll")
        bg_cfg = FRWModelConfig(**cfg_dict["background"])
        ic = FRWInitialConditions(**cfg_dict["initial_conditions"])
        k_targets = cfg_dict.get("k_targets_m_inv", [])
        min_ln_a = cfg_dict.get("min_ln_a")
        run = run_background_for_spectra(bg_cfg, ic, min_ln_a=min_ln_a)
        points = compute_slow_roll_spectra(run, k_targets)
        summary = save_spectrum_points(points, self.results_dir, stem=stem)
        plot_spectrum_points(points, self.figs_dir, stem=stem)
        metrics = cfg_dict.get("slow_roll_metrics", {})
        if metrics:
            summary.update({f"slow_roll_{k}": v for k, v in metrics.items()})
        return summary

    def _run_ringdown(self, path: Path):
        cfg = RingdownConfig(**load_config(path))
        result = compute_ringdown(cfg)
        save_ringdown(result, self.results_dir)
        plot_ringdown(result, self.figs_dir)
        return result

    def _run_yukawa(self, path: Path):
        cfg = YukawaConfig(**load_config(path))
        result = run_yukawa(cfg)
        save_yukawa(result, self.results_dir)
        plot_yukawa(result, self.figs_dir)
        return result

    def _run_stability(self, path: Path):
        cfg_dict = load_config(path)
        model_cfg = FRWModelConfig(**cfg_dict["model"])
        cfg = StabilityConfig(
            model=model_cfg,
            perturbation_scale=cfg_dict["perturbation_scale"],
            realizations=cfg_dict["realizations"],
            seed=cfg_dict.get("seed", 1729),
        )
        summary = run_stability(cfg)
        save_stability(summary, self.logs_dir)
        return summary

    def _write_overall_summary(self, summaries: Dict[str, Dict[str, float]]) -> None:
        (self.results_dir / "phase1_summary.json").write_text(
            json.dumps(summaries, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _progress(self, label: str, idx: int, total: int) -> None:
        self._log(f"{label}: {idx}/{total}")

    def _log(self, message: str) -> None:
        print(f"[TE_1.C] {message}")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    runner = Phase1Runner(root)
    summaries = runner.run()
    print("Phase 1 summaries:")
    for key, value in summaries.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()

