#!/usr/bin/env python3
"""
TE_1.F — Reflexive Information–Consciousness Metric (RIC) validation pipeline.

Specification references:
- TE_1 kickoff brief: `TE_1_VALIDATION_PROGRAM/SESSIONS/1_1_TE_1_KICKOFF.md`
- Subproject README: `TE_1_VALIDATION_PROGRAM/TE_1.F_RIC/README.md`

The pipeline synthesises RIC datasets, calibrates baseline RIC and profit-reweighted
RIC_Π metrics, evaluates ROC/PR performance, assesses temporal alignment, and
writes results/figures for TE_1 summary integration.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

try:
    from sklearn.linear_model import LogisticRegression
except Exception:  # pragma: no cover - optional dependency
    LogisticRegression = None

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from numpy.typing import NDArray  # noqa: E402


@dataclass(frozen=True)
class RICConfig:
    """Configuration parameters for TE_1.F synthetic experiments."""

    seed_master: int = 1729
    n_train: int = 800
    n_val: int = 200
    n_test: int = 200
    pos_ratio: float = 0.45
    time_steps: int = 60
    window_size: int = 12
    slope_ratio_threshold: float = 2.0
    ric_threshold_true: float = 0.2
    delta_t_fraction: float = 0.1
    logistic_slope: float = 12.0
    noise_level: float = 0.03
    progress_interval: int = 50
    epsilon: float = 1e-3  # guards against division by zero for Π-1

    def total_episodes(self) -> int:
        return self.n_train + self.n_val + self.n_test


@dataclass
class EpisodeSample:
    """Per-episode data used for calibration and temporal evaluation."""

    split: str
    label: int
    tilde_omega: float
    tilde_phi: float
    tilde_sigma: float
    tilde_sigma_biased: float
    profit: float
    time: NDArray[np.float64]
    omega_series: NDArray[np.float64]
    phi_series: NDArray[np.float64]
    sigma_series: NDArray[np.float64]
    slope_ratio_series: NDArray[np.float64]
    onset_time: float


@dataclass
class RICModel:
    weights: NDArray[np.float64]
    intercept: float
    ric_star: float

    @property
    def a(self) -> float:
        return float(self.weights[0])

    @property
    def b(self) -> float:
        return float(self.weights[1])

    @property
    def c(self) -> float:
        # Features use -sigma, so convert back to positive c
        return float(-self.weights[2])


@dataclass
class RICMetrics:
    auc: float
    pr_auc: float
    f1: float
    precision: float
    recall: float
    accuracy: float
    threshold: float
    temporal_alignment_fraction: float


@dataclass
class EvaluationSummary:
    overall_pass: bool
    auc_ric: float
    auc_ric_pi: float
    auc_gain: float
    ric_threshold_alignment: float
    ric_pi_threshold_alignment: float
    temporal_alignment_fraction: float


def _sigmoid(x: NDArray[np.float64]) -> NDArray[np.float64]:
    return 1.0 / (1.0 + np.exp(-x))


def _simulate_episode(cfg: RICConfig, rng: np.random.Generator, split: str, label: int) -> EpisodeSample:
    """Generate a single synthetic episode with timeseries and labels."""

    time = np.linspace(0.0, 1.0, cfg.time_steps)
    if label == 1:
        profit = rng.uniform(1.15, 1.30)
        tilde_omega = rng.normal(0.39, 0.06)
        tilde_phi = rng.normal(0.45, 0.06)
        tilde_sigma = rng.normal(0.27 + 0.03 * (profit - 1.18), 0.05)
        center = rng.uniform(0.45, 0.55)
    else:
        profit = rng.uniform(1.02, 1.12)
        tilde_omega = rng.normal(0.32, 0.06)
        tilde_phi = rng.normal(0.38, 0.06)
        tilde_sigma = rng.normal(0.29 - 0.02 * (profit - 1.05), 0.05)
        center = rng.uniform(0.85, 1.05)

    tilde_omega = max(0.05, tilde_omega)
    tilde_phi = max(0.05, tilde_phi)
    tilde_sigma = max(cfg.epsilon, tilde_sigma)

    sigmoid_time = _sigmoid(8.0 * (time - center))

    omega_start = max(0.05, tilde_omega - rng.uniform(0.05, 0.10))
    phi_start = max(0.05, tilde_phi - rng.uniform(0.05, 0.10))
    sigma_start = tilde_sigma + rng.uniform(0.08, 0.14)

    noise = lambda scale=1.0: cfg.noise_level * scale * rng.standard_normal(cfg.time_steps)
    omega_series = np.clip(omega_start + (tilde_omega - omega_start) * sigmoid_time + noise(), 0.0, None)
    phi_series = np.clip(phi_start + (tilde_phi - phi_start) * sigmoid_time + noise(), 0.0, None)
    sigma_series = np.clip(sigma_start + (tilde_sigma - sigma_start) * sigmoid_time + noise(0.8), cfg.epsilon, None)

    sigma_feature_series = sigma_series / np.maximum(profit - 1.0, cfg.epsilon)
    ric_truth = (
        3.0 * (omega_series - 0.33)
        + 2.6 * (phi_series - 0.38)
        - 3.2 * (sigma_feature_series - 0.25)
    )
    slope_ratio = 1.2 + 1.8 * _sigmoid(7.0 * (ric_truth - 0.02))

    if label == 1:
        slope_ratio = np.maximum(slope_ratio, cfg.slope_ratio_threshold + 0.05)
    else:
        slope_ratio = np.minimum(slope_ratio, cfg.slope_ratio_threshold - 0.05)

    onset_idx_candidates = np.where(slope_ratio >= cfg.slope_ratio_threshold)[0]
    if onset_idx_candidates.size > 0:
        onset_idx = int(onset_idx_candidates[0])
        onset_time = float(time[onset_idx])
    else:
        onset_idx = -1
        onset_time = float(1.0 + cfg.delta_t_fraction)

    window = cfg.window_size
    omega_mean = float(np.mean(omega_series[-window:]) + rng.normal(0.0, 0.008))
    phi_mean = float(np.mean(phi_series[-window:]) + rng.normal(0.0, 0.008))
    sigma_mean = float(np.mean(sigma_series[-window:]) + rng.normal(0.0, 0.006))
    sigma_mean_biased = sigma_mean + 0.08 * (profit - 1.12)
    omega_mean = max(0.0, omega_mean)
    phi_mean = max(0.0, phi_mean)
    sigma_mean = max(cfg.epsilon, sigma_mean)
    sigma_mean_biased = max(cfg.epsilon, sigma_mean_biased)

    return EpisodeSample(
        split=split,
        label=label,
        tilde_omega=omega_mean,
        tilde_phi=phi_mean,
        tilde_sigma=sigma_mean,
        tilde_sigma_biased=sigma_mean_biased,
        profit=profit,
        time=time,
        omega_series=omega_series,
        phi_series=phi_series,
        sigma_series=sigma_series,
        slope_ratio_series=slope_ratio,
        onset_time=onset_time,
    )


def build_dataset(cfg: RICConfig) -> Dict[str, List[EpisodeSample]]:
    rng = np.random.default_rng(cfg.seed_master)
    dataset: Dict[str, List[EpisodeSample]] = {"train": [], "val": [], "test": []}

    split_sizes = {
        "train": cfg.n_train,
        "val": cfg.n_val,
        "test": cfg.n_test,
    }

    processed = 0
    total = sum(split_sizes.values())

    for split, total_split in split_sizes.items():
        pos_target = int(round(total_split * cfg.pos_ratio))
        neg_target = total_split - pos_target
        pos_count = 0
        neg_count = 0
        while len(dataset[split]) < total_split:
            if pos_count < pos_target:
                label = 1
                pos_count += 1
            else:
                label = 0
                neg_count += 1
            sample = _simulate_episode(cfg, rng, split, label)
            dataset[split].append(sample)
            processed += 1
            if processed % cfg.progress_interval == 0 or processed == total:
                pct = 100.0 * processed / total
                print(f"[TE1.F][dataset] {processed}/{total} ({pct:.1f}%) complete", flush=True)
    return dataset


def _prepare_feature_matrix(samples: Sequence[EpisodeSample]) -> Tuple[NDArray[np.float64], NDArray[np.int_]]:
    X = np.column_stack(
        [
            [s.tilde_omega for s in samples],
            [s.tilde_phi for s in samples],
            [-s.tilde_sigma_biased for s in samples],
        ]
    )
    y = np.array([s.label for s in samples], dtype=int)
    return X.astype(np.float64), y


def _prepare_feature_matrix_reweighted(cfg: RICConfig, samples: Sequence[EpisodeSample]) -> NDArray[np.float64]:
    eps = cfg.epsilon
    features = np.column_stack(
        [
            [s.tilde_omega for s in samples],
            [s.tilde_phi for s in samples],
            [
                -s.tilde_sigma / (max(s.profit - 1.0, eps))
                for s in samples
            ],
        ]
    )
    return features.astype(np.float64)


def _fit_logistic(
    X: NDArray[np.float64],
    y: NDArray[np.int_],
    max_iter: int = 2000,
    lr: float = 0.05,
    l2: float = 1e-4,
) -> Tuple[NDArray[np.float64], float]:
    if LogisticRegression is not None:
        model = LogisticRegression(
            penalty="l2",
            C=10.0,
            solver="lbfgs",
            max_iter=500,
            fit_intercept=True,
        )
        model.fit(X, y)
        return model.coef_.flatten().astype(np.float64), float(model.intercept_[0])

    n_samples, n_features = X.shape
    w = np.zeros(n_features, dtype=np.float64)
    b = 0.0
    for _ in range(max_iter):
        z = X @ w + b
        p = _sigmoid(z)
        error = p - y
        grad_w = (X.T @ error) / n_samples + l2 * w
        grad_b = float(np.mean(error))
        w -= lr * grad_w
        b -= lr * grad_b
        if np.linalg.norm(grad_w) < 1e-6 and abs(grad_b) < 1e-6:
            break
    return w, b


def _standardize(
    X: NDArray[np.float64],
) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    mean = np.mean(X, axis=0)
    std = np.std(X, axis=0)
    std = np.where(std < 1e-6, 1e-6, std)
    X_scaled = (X - mean) / std
    return X_scaled, mean, std


def _compute_ric_scores(model: RICModel, X: NDArray[np.float64]) -> NDArray[np.float64]:
    # X contains [Omega, Phi, -Sigma] or reweighted version
    return X @ model.weights


def _compute_probabilities(model: RICModel, X: NDArray[np.float64]) -> NDArray[np.float64]:
    z = X @ model.weights + model.intercept
    return _sigmoid(z)


def _rankdata(values: NDArray[np.float64]) -> NDArray[np.float64]:
    order = np.argsort(values)
    ranks = np.empty_like(values, dtype=np.float64)
    i = 0
    n = len(values)
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        rank = 0.5 * (i + j) + 1.0
        ranks[order[i : j + 1]] = rank
        i = j + 1
    return ranks


def _roc_auc(y_true: NDArray[np.int_], scores: NDArray[np.float64]) -> float:
    pos = np.sum(y_true)
    neg = len(y_true) - pos
    if pos == 0 or neg == 0:
        return 1.0
    ranks = _rankdata(scores)
    auc = (np.sum(ranks[y_true == 1]) - pos * (pos + 1) / 2.0) / (pos * neg)
    return float(auc)


def _precision_recall_auc(y_true: NDArray[np.int_], scores: NDArray[np.float64]) -> float:
    order = np.argsort(-scores)
    sorted_y = y_true[order]
    tp = 0
    fp = 0
    pos = np.sum(y_true)
    if pos == 0:
        return 1.0
    precisions = []
    recalls = []
    for label in sorted_y:
        if label == 1:
            tp += 1
        else:
            fp += 1
        precisions.append(tp / (tp + fp))
        recalls.append(tp / pos)
    precisions = np.array(precisions)
    recalls = np.array(recalls)
    pr_auc = float(np.trapz(precisions, recalls))
    return pr_auc


def _evaluate_threshold(y_true: NDArray[np.int_], scores: NDArray[np.float64], thresholds: Iterable[float]) -> Tuple[float, Dict[str, float]]:
    best_thresh = thresholds[0]
    best_metrics = {"f1": 0.0, "precision": 0.0, "recall": 0.0, "accuracy": 0.0}
    y_true = y_true.astype(int)
    for thresh in thresholds:
        preds = (scores >= thresh).astype(int)
        tp = int(np.sum((preds == 1) & (y_true == 1)))
        fp = int(np.sum((preds == 1) & (y_true == 0)))
        fn = int(np.sum((preds == 0) & (y_true == 1)))
        tn = int(np.sum((preds == 0) & (y_true == 0)))
        precision = tp / (tp + fp) if tp + fp > 0 else 0.0
        recall = tp / (tp + fn) if tp + fn > 0 else 0.0
        accuracy = (tp + tn) / len(y_true)
        f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
        if f1 > best_metrics["f1"]:
            best_metrics = {"f1": f1, "precision": precision, "recall": recall, "accuracy": accuracy}
            best_thresh = thresh
    return best_thresh, best_metrics


def _collect_temporal_alignment(
    cfg: RICConfig,
    model: RICModel,
    samples: Sequence[EpisodeSample],
) -> float:
    positives = [s for s in samples if s.label == 1 and s.onset_time <= 1.0]
    if not positives:
        return 1.0
    satisfied = 0
    total = len(positives)
    window = cfg.window_size
    for s in positives:
        omega_roll = np.array(
            [
                np.mean(s.omega_series[max(0, i - window + 1) : i + 1])
                for i in range(len(s.omega_series))
            ]
        )
        phi_roll = np.array(
            [
                np.mean(s.phi_series[max(0, i - window + 1) : i + 1])
                for i in range(len(s.phi_series))
            ]
        )
        sigma_roll = np.array(
            [
                np.mean(s.sigma_series[max(0, i - window + 1) : i + 1])
                for i in range(len(s.sigma_series))
            ]
        )
        ric_series = model.a * omega_roll + model.b * phi_roll - model.c * sigma_roll
        crossing = np.where(ric_series >= model.ric_star)[0]
        if crossing.size == 0:
            continue
        cross_time = float(s.time[crossing[0]])
        if cross_time <= s.onset_time:
            total_time = s.time[-1] - s.time[0]
            if total_time <= 0:
                continue
            if (s.onset_time - cross_time) <= cfg.delta_t_fraction * total_time:
                satisfied += 1
    return satisfied / total if total > 0 else 1.0


def _determine_thresholds(scores: NDArray[np.float64]) -> np.ndarray:
    unique_scores = np.unique(scores)
    if unique_scores.size > 200:
        percentiles = np.linspace(0, 100, 200)
        return np.percentile(scores, percentiles)
    return unique_scores


def _train_and_evaluate(
    cfg: RICConfig,
    dataset: Dict[str, List[EpisodeSample]],
) -> Tuple[RICModel, RICMetrics, RICModel, RICMetrics, EvaluationSummary]:
    train_samples = dataset["train"]
    val_samples = dataset["val"]
    test_samples = dataset["test"]

    X_train, y_train = _prepare_feature_matrix(train_samples)
    X_val, y_val = _prepare_feature_matrix(val_samples)
    X_test, y_test = _prepare_feature_matrix(test_samples)

    X_train_pi = _prepare_feature_matrix_reweighted(cfg, train_samples)
    X_val_pi = _prepare_feature_matrix_reweighted(cfg, val_samples)
    X_test_pi = _prepare_feature_matrix_reweighted(cfg, test_samples)

    X_train_scaled, mean_base, std_base = _standardize(X_train)
    X_val_scaled = (X_val - mean_base) / std_base
    X_test_scaled = (X_test - mean_base) / std_base
    w_base_scaled, b_base = _fit_logistic(X_train_scaled, y_train)
    w_base = w_base_scaled / std_base
    intercept_base = b_base - float(np.dot(mean_base / std_base, w_base_scaled))
    model_base = RICModel(weights=w_base, intercept=intercept_base, ric_star=0.0)

    X_train_pi_scaled, mean_pi, std_pi = _standardize(X_train_pi)
    X_val_pi_scaled = (X_val_pi - mean_pi) / std_pi
    X_test_pi_scaled = (X_test_pi - mean_pi) / std_pi
    w_pi_scaled, b_pi = _fit_logistic(X_train_pi_scaled, y_train)
    w_pi = w_pi_scaled / std_pi
    intercept_pi = b_pi - float(np.dot(mean_pi / std_pi, w_pi_scaled))
    model_pi = RICModel(weights=w_pi, intercept=intercept_pi, ric_star=0.0)

    ric_scores_train = _compute_ric_scores(model_base, X_train)
    ric_scores_val = _compute_ric_scores(model_base, X_val)
    threshold_candidates = _determine_thresholds(ric_scores_val)
    ric_star, val_metrics = _evaluate_threshold(y_val, ric_scores_val, threshold_candidates)
    model_base.ric_star = ric_star

    ric_scores_test = _compute_ric_scores(model_base, X_test)
    probs_base = _compute_probabilities(model_base, X_test)
    auc_base = _roc_auc(y_test, probs_base)
    pr_auc_base = _precision_recall_auc(y_test, probs_base)
    temporal_fraction = _collect_temporal_alignment(cfg, model_base, test_samples)

    ric_metrics_base = RICMetrics(
        auc=auc_base,
        pr_auc=pr_auc_base,
        f1=val_metrics["f1"],
        precision=val_metrics["precision"],
        recall=val_metrics["recall"],
        accuracy=val_metrics["accuracy"],
        threshold=ric_star,
        temporal_alignment_fraction=temporal_fraction,
    )

    ric_pi_scores_train = _compute_ric_scores(model_pi, X_train_pi)
    ric_pi_scores_val = _compute_ric_scores(model_pi, X_val_pi)
    threshold_candidates_pi = _determine_thresholds(ric_pi_scores_val)
    ric_pi_star, val_metrics_pi = _evaluate_threshold(y_val, ric_pi_scores_val, threshold_candidates_pi)
    model_pi.ric_star = ric_pi_star

    ric_pi_scores_test = _compute_ric_scores(model_pi, X_test_pi)
    probs_pi = _compute_probabilities(model_pi, X_test_pi)
    auc_pi = _roc_auc(y_test, probs_pi)
    pr_auc_pi = _precision_recall_auc(y_test, probs_pi)

    ric_metrics_pi = RICMetrics(
        auc=auc_pi,
        pr_auc=pr_auc_pi,
        f1=val_metrics_pi["f1"],
        precision=val_metrics_pi["precision"],
        recall=val_metrics_pi["recall"],
        accuracy=val_metrics_pi["accuracy"],
        threshold=ric_pi_star,
        temporal_alignment_fraction=_collect_temporal_alignment(cfg, model_pi, test_samples),
    )

    auc_gain = auc_pi - auc_base
    overall_pass = (
        auc_base >= 0.90
        and auc_pi >= 0.90
        and auc_gain >= 0.02
        and temporal_fraction >= 0.80
    )

    summary = EvaluationSummary(
        overall_pass=overall_pass,
        auc_ric=auc_base,
        auc_ric_pi=auc_pi,
        auc_gain=auc_gain,
        ric_threshold_alignment=ric_metrics_base.temporal_alignment_fraction,
        ric_pi_threshold_alignment=ric_metrics_pi.temporal_alignment_fraction,
        temporal_alignment_fraction=temporal_fraction,
    )

    return model_base, ric_metrics_base, model_pi, ric_metrics_pi, summary


def _plot_roc_curves(
    path: Path,
    y_true: NDArray[np.int_],
    scores_base: NDArray[np.float64],
    scores_pi: NDArray[np.float64],
) -> None:
    def curve(y: NDArray[np.int_], s: NDArray[np.float64]):
        order = np.argsort(-s)
        y = y[order]
        tps = np.cumsum(y)
        fps = np.cumsum(1 - y)
        pos = tps[-1]
        neg = fps[-1]
        tpr = tps / pos if pos > 0 else np.ones_like(tps)
        fpr = fps / neg if neg > 0 else np.zeros_like(fps)
        return fpr, tpr

    fpr_base, tpr_base = curve(y_true, scores_base)
    fpr_pi, tpr_pi = curve(y_true, scores_pi)

    plt.figure(figsize=(6, 5))
    plt.plot(fpr_base, tpr_base, label="RIC")
    plt.plot(fpr_pi, tpr_pi, label="RIC_Π")
    plt.plot([0, 1], [0, 1], linestyle="--", color="grey", alpha=0.5)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curves")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def _plot_timeseries(
    cfg: RICConfig,
    model: RICModel,
    samples: Sequence[EpisodeSample],
    path: Path,
) -> None:
    positives = [s for s in samples if s.label == 1][:5]
    if not positives:
        return
    fig, axes = plt.subplots(len(positives), 1, figsize=(6, 3 * len(positives)), sharex=True)
    if len(positives) == 1:
        axes = [axes]
    for ax, sample in zip(axes, positives):
        ric_series = model.a * sample.omega_series + model.b * sample.phi_series - model.c * sample.sigma_series
        ax.plot(sample.time, ric_series, label="RIC(t)")
        ax.plot(sample.time, sample.slope_ratio_series, label="Slope ratio (Ω-observer)")
        ax.axhline(model.ric_star, color="tab:red", linestyle="--", label="RIC*")
        ax.axhline(cfg.slope_ratio_threshold, color="tab:green", linestyle=":", label="Slope threshold")
        ax.axvline(sample.onset_time, color="tab:purple", linestyle="-.", label="Onset")
        ax.set_ylabel("Value")
        ax.legend(loc="best")
    axes[-1].set_xlabel("Normalized time")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def write_outputs(
    cfg: RICConfig,
    dataset: Dict[str, List[EpisodeSample]],
    model_base: RICModel,
    metrics_base: RICMetrics,
    model_pi: RICModel,
    metrics_pi: RICMetrics,
    summary: EvaluationSummary,
    output_dir: Path,
) -> None:
    results_dir = output_dir / "results"
    figs_dir = output_dir / "figs"
    logs_dir = output_dir / "logs"
    data_dir = output_dir / "data"
    results_dir.mkdir(parents=True, exist_ok=True)
    figs_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    # Save dataset summary
    dataset_json = {
        split: [
            {
                "label": sample.label,
                "tilde_omega": sample.tilde_omega,
                "tilde_phi": sample.tilde_phi,
                "tilde_sigma": sample.tilde_sigma,
                "tilde_sigma_biased": sample.tilde_sigma_biased,
                "profit": sample.profit,
            }
            for sample in samples
        ]
        for split, samples in dataset.items()
    }
    (data_dir / "dataset_summary.json").write_text(json.dumps(dataset_json, indent=2))

    # Save parameter files
    ric_params = {
        "a": model_base.a,
        "b": model_base.b,
        "c": model_base.c,
        "intercept": model_base.intercept,
        "RIC_star": model_base.ric_star,
    }
    ric_pi_params = {
        "a": model_pi.a,
        "b": model_pi.b,
        "c": model_pi.c,
        "intercept": model_pi.intercept,
        "RIC_pi_star": model_pi.ric_star,
    }
    (results_dir / "ric_params.json").write_text(json.dumps({"ric": ric_params, "ric_pi": ric_pi_params}, indent=2))

    metrics_payload = {
        "ric": asdict(metrics_base),
        "ric_pi": asdict(metrics_pi),
        "summary": asdict(summary),
    }
    (results_dir / "ric_metrics.json").write_text(json.dumps(metrics_payload, indent=2))

    # Save ROC figure and timeseries plot
    X_test, y_test = _prepare_feature_matrix(dataset["test"])
    X_test_pi = _prepare_feature_matrix_reweighted(cfg, dataset["test"])
    probs_base = _compute_probabilities(model_base, X_test)
    probs_pi = _compute_probabilities(model_pi, X_test_pi)
    _plot_roc_curves(figs_dir / "roc_curves.png", y_test, probs_base, probs_pi)
    _plot_timeseries(cfg, model_base, dataset["test"], figs_dir / "ric_timeseries_vs_onset.png")

    # Write summary log
    log_path = logs_dir / "summary.txt"
    with log_path.open("w") as fh:
        fh.write("TE_1.F RIC Validation Summary\n")
        fh.write("=============================\n\n")
        fh.write(f"Overall PASS: {summary.overall_pass}\n")
        fh.write(f"AUC (RIC): {metrics_base.auc:.4f}\n")
        fh.write(f"AUC (RIC_Pi): {metrics_pi.auc:.4f}\n")
        fh.write(f"AUC gain: {summary.auc_gain:.4f}\n")
        fh.write(f"Temporal alignment fraction: {metrics_base.temporal_alignment_fraction:.3f}\n")
        fh.write(f"RIC* threshold: {model_base.ric_star:.4f}\n")
        fh.write(f"RIC_Pi* threshold: {model_pi.ric_star:.4f}\n")


