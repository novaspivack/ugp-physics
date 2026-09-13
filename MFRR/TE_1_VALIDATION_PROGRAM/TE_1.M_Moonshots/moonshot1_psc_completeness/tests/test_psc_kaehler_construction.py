import numpy as np

from moonshot1_psc_completeness import cp_boundary_count, psc_kaehler_construction, run_modular_flow


def test_compute_complex_structure_basic():
    metric = np.eye(2)
    symplectic = np.array([[0.0, 1.0], [-1.0, 0.0]])
    complex_structure = psc_kaehler_construction.compute_complex_structure(metric, symplectic)
    results = psc_kaehler_construction.verify_kaehler_conditions(
        metric,
        symplectic,
        complex_structure,
    )
    assert all(results.values())


def test_cp_boundary_count_regression():
    # Generate synthetic data with known coefficients.
    area = np.linspace(10.0, 100.0, num=50)
    alpha_true = 0.25
    beta_true = -1.5
    gamma_true = 2.0
    entropy = alpha_true * area + beta_true * np.log(area) + gamma_true

    result = cp_boundary_count.estimate_coefficients(area, entropy)
    assert np.isclose(result.alpha, alpha_true, atol=1e-6)
    assert np.isclose(result.beta_log, beta_true, atol=1e-6)
    assert np.isclose(result.gamma, gamma_true, atol=1e-6)
    assert np.isclose(result.r2, 1.0, atol=1e-9)
    assert result.samples == area.size


def test_run_modular_flow_smoke(tmp_path):
    output = tmp_path / "modular.json"
    result = run_modular_flow.run_modular_flow(
        steps=128,
        grid_size=8,
        bootstrap_samples=8,
        seed=1234,
        output_path=output,
    )
    # Validate presence of key fields.
    assert "linear" in result
    assert "density" in result["linear"]
    assert output.exists()


