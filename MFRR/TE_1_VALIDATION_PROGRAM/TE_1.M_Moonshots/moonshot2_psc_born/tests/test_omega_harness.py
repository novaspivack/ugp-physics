import numpy as np

from moonshot2_psc_born import adjudication_parallel, bounded_observer, omega_harness


def test_sample_measurements_pcg64_reproducible():
    amps = [1.0, 1.0]
    result = omega_harness.sample_measurements(amps, samples=256, provider="pcg64", seed=42)
    assert result.provider == "pcg64"
    # For equal amplitudes, empirical probabilities should be close to 0.5
    assert np.allclose(result.empirical_probabilities, [0.5, 0.5], atol=0.1)
    assert result.metrics["tv_distance"] < 0.1


def test_sample_measurements_cached_omega():
    amps = [0.6, 0.8]
    result = omega_harness.sample_measurements(amps, samples=128, provider="omega")
    assert result.provider == "omega"
    assert len(result.empirical_counts) == 2
    # ensure deterministic hash
    assert result.bit_hash == omega_harness.sample_measurements(amps, samples=128, provider="omega").bit_hash


def test_bounded_observer_within_limit():
    analyzer = bounded_observer.BoundedObserverAnalyzer(c=1.0, gamma=1.0)
    empirical = np.array([0.51, 0.49])
    expected = np.array([0.5, 0.5])
    report = analyzer.evaluate(empirical, expected, samples=1000, observer_complexity=256)
    assert report["within_bound"]
    assert report["bound"] > 0.0


def test_adjudication_parallel_smoke():
    amps = [np.sqrt(0.3), np.sqrt(0.7)]
    result = adjudication_parallel.run_parallel_experiment(
        amps,
        samples=128,
        provider_a="pcg64",
        provider_b="omega",
        observer_complexity=128,
        seed_a=123,
    )
    assert "arm_a" in result and "arm_b" in result
    assert "bounded_observer" in result
    assert result["bounded_observer"]["samples"] == 128


