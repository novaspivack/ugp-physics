import numpy as np
import pytest

from pr0_system.analysis import diagnostics
from pr0_system.bootstrap.dissonance import SDSBootstrap
from pr0_system.forces import em, gravity, weak


# ---------------------------------------------------------------------------
# Regression tests for shared annealing helpers (Work Package C)
# ---------------------------------------------------------------------------


@pytest.fixture
def seeded_rng():
    return np.random.default_rng(1729)


def _prime_best_tracker(tracker, params, metric):
    tracker.best_metric = metric
    tracker.params = {k: float(v) for k, v in params.items()}


def test_em_meta_learn_reverts_to_best(monkeypatch, seeded_rng):
    system = em.BootstrapEM_Final(L_x=16, L_y=16)
    system._annealer.rng = seeded_rng

    baseline = {
        "alpha": system.best_alpha,
        "power": system.best_power,
        "cutoff_beta": system.best_cutoff,
    }
    _prime_best_tracker(system._best_tracker, baseline, metric=0.6)
    system.best_dissonance = 0.6

    system.alpha = baseline["alpha"] * 1.4
    system.power = baseline["power"] * 0.8
    system.cutoff_beta = baseline["cutoff_beta"] + 0.08
    system.current_sep = None

    monkeypatch.setattr(em, "compute_dissonance_EM_final", lambda *args, **kwargs: 2.5)

    system._em_meta_learn()

    assert abs(system.alpha - baseline["alpha"]) <= baseline["alpha"] * 0.05
    assert abs(system.power - baseline["power"]) <= baseline["power"] * 0.05
    assert abs(system.cutoff_beta - baseline["cutoff_beta"]) <= 0.01


def test_weak_meta_learn_small_adjustment(monkeypatch, seeded_rng):
    system = weak.BootstrapWeak_Final(L_x=16, L_y=16)
    system._annealer.rng = seeded_rng

    baseline = {
        "alpha": system.best_alpha,
        "power": system.best_power,
        "cutoff_beta": system.best_cutoff,
    }
    _prime_best_tracker(system._best_tracker, baseline, metric=0.4)
    system.best_dissonance = 0.4

    system.alpha = baseline["alpha"] * 1.1
    system.power = baseline["power"] * 0.9
    system.cutoff_beta = baseline["cutoff_beta"] + 0.05
    system.current_sep = None  # normally populated during step()
    monkeypatch.setattr(weak, "compute_dissonance_weak_final", lambda *args, **kwargs: 0.35)

    system._annealer.rng = seeded_rng
    system._weak_meta_learn()

    assert 0.005 <= system.alpha <= 0.030
    assert 0.8 <= system.power <= 1.8
    assert 0.15 <= system.cutoff_beta <= 0.8


def test_gravity_meta_learn_reverts_to_best(monkeypatch, seeded_rng):
    system = gravity.BootstrapGravity(L_x=16, L_y=16)
    system._annealer.rng = seeded_rng

    baseline_g = system.best_G
    _prime_best_tracker(system._best_tracker, {"G_grav": baseline_g}, metric=0.8)
    system.best_dissonance = 0.8

    system.G_grav = baseline_g * 0.3
    monkeypatch.setattr(gravity, "compute_dissonance_gravity", lambda *args, **kwargs: 1.6)

    system._gravity_meta_learn()

    assert 0.001 <= system.G_grav <= 0.5


def test_sds_meta_learn_shared_helpers(monkeypatch, seeded_rng):
    system = SDSBootstrap(L_x=16, L_y=16)
    system._annealer.rng = seeded_rng

    baseline = {
        "gamma_base": system.best_gamma_base,
        "gamma_scale": system.best_gamma_scale,
    }
    _prime_best_tracker(system._best_tracker, baseline, metric=0.4)
    system.best_dissonance = 0.4

    system.gamma_base = baseline["gamma_base"] * 1.3
    system.gamma_scale = baseline["gamma_scale"] * 0.7
    monkeypatch.setattr(
        "pr0_system.bootstrap.dissonance.compute_ontological_dissonance",
        lambda *args, **kwargs: 0.9,
    )

    system._sds_meta_learn()

    assert 0.001 <= system.gamma_base <= 0.1
    assert 0.1 <= system.gamma_scale <= 2.0


# ---------------------------------------------------------------------------
# Diagnostics helpers (Work Package B)
# ---------------------------------------------------------------------------


def test_curvature_heatmap_normalizes():
    curvature = np.array([[0.0, 2.0], [-3.0, 1.0]])
    heatmap = diagnostics.curvature_heatmap(curvature, smoothing_sigma=None)
    assert np.isclose(np.abs(heatmap).max(), 1.0)
    assert np.isclose(heatmap.min(), -1.0)


def test_compute_dissonance_timeseries(tmp_path):
    psi_history = [np.ones((2, 2)) * i for i in range(3)]
    chi_history = [np.zeros((2, 2)) for _ in range(3)]

    def fake_dissonance(psi, chi, history):
        return float(np.sum(np.abs(psi)) + np.sum(np.abs(chi)) + len(history))

    series = diagnostics.compute_dissonance_timeseries(
        psi_history,
        chi_history,
        fake_dissonance,
        window=2,
        stride=1,
    )
    assert series.shape == (3,)
    path = diagnostics.export_timeseries_csv(series, tmp_path / "series.csv")
    assert path.exists()


