"""Tests for Stage 8.4 — Statistical Analysis and Performance Metrics."""

import math
import pytest

from backend.app.experiments.statistics import (
    StatisticalAnalyzer,
    optimality_gap,
    approximation_ratio,
    cohens_d,
    mann_whitney_u,
    wilcoxon_signed_rank,
    _mean,
    _std,
    _median,
    _t_confidence_interval,
)


class TestCoreMathHelpers:
    def test_mean_basic(self):
        assert _mean([1.0, 2.0, 3.0]) == pytest.approx(2.0)

    def test_mean_empty(self):
        assert math.isnan(_mean([]))

    def test_std_two_values(self):
        # std of [1, 3] = 1.414...
        assert _std([1.0, 3.0]) == pytest.approx(math.sqrt(2.0), rel=1e-5)

    def test_std_single(self):
        assert math.isnan(_std([5.0]))

    def test_median_odd(self):
        assert _median([1.0, 3.0, 5.0]) == 3.0

    def test_median_even(self):
        assert _median([1.0, 2.0, 3.0, 4.0]) == 2.5

    def test_median_empty(self):
        assert math.isnan(_median([]))

    def test_confidence_interval_decreases_with_more_data(self):
        small = [1.0, 2.0, 3.0]
        large = [1.0, 2.0, 3.0] * 10
        ci_small = _t_confidence_interval(small)
        ci_large = _t_confidence_interval(large)
        width_small = ci_small[1] - ci_small[0]
        width_large = ci_large[1] - ci_large[0]
        assert width_large < width_small


class TestOptimalityMetrics:
    def test_optimality_gap_zero_when_optimal(self):
        gap = optimality_gap(10.0, 10.0)
        assert gap == pytest.approx(0.0)

    def test_optimality_gap_basic(self):
        gap = optimality_gap(8.0, 10.0)
        assert gap == pytest.approx(20.0)

    def test_optimality_gap_zero_optimal_returns_nan(self):
        assert math.isnan(optimality_gap(5.0, 0.0))

    def test_approximation_ratio_max(self):
        ratio = approximation_ratio(8.0, 10.0, "max")
        assert ratio == pytest.approx(0.8)

    def test_approximation_ratio_min(self):
        ratio = approximation_ratio(10.0, 8.0, "min")
        assert ratio == pytest.approx(0.8)

    def test_approximation_ratio_candidate_zero_returns_nan(self):
        assert math.isnan(approximation_ratio(0.0, 10.0, "min"))


class TestStatisticalTests:
    def test_mann_whitney_basic(self):
        a = [1.0, 2.0, 3.0, 4.0, 5.0]
        b = [6.0, 7.0, 8.0, 9.0, 10.0]
        result = mann_whitney_u(a, b)
        if "error" not in result:
            assert result["p_value"] < 0.05  # clearly different

    def test_mann_whitney_insufficient_samples(self):
        result = mann_whitney_u([1.0], [2.0])
        assert "error" in result or math.isnan(result.get("p_value", float("nan")))

    def test_cohens_d_no_effect(self):
        samples = [5.0, 5.0, 5.0, 5.0, 5.0]
        d = cohens_d(samples, samples)
        assert math.isnan(d) or abs(d) < 1e-9

    def test_cohens_d_large_effect(self):
        a = [1.0, 1.1, 0.9, 1.0, 1.0]
        b = [10.0, 10.1, 9.9, 10.0, 10.0]
        d = cohens_d(a, b)
        assert not math.isnan(d)
        assert abs(d) > 5.0  # large effect

    def test_wilcoxon_equal_samples_no_error(self):
        a = [1.0, 2.0, 3.0, 4.0, 5.0]
        b = [1.1, 2.1, 3.1, 4.1, 5.1]
        result = wilcoxon_signed_rank(a, b)
        assert "test" in result

    def test_wilcoxon_unequal_sizes_returns_error(self):
        result = wilcoxon_signed_rank([1.0, 2.0], [1.0, 2.0, 3.0])
        assert "error" in result


class TestStatisticalAnalyzer:
    def setup_method(self):
        self.analyzer = StatisticalAnalyzer()

    def test_compute_metrics_basic(self):
        metrics = self.analyzer.compute_metrics(
            objective_values=[8.0, 9.0, 10.0],
            runtimes=[0.1, 0.2, 0.15],
            feasibility_flags=[True, True, True],
            eval_counts=[100, 110, 105],
        )
        assert metrics["best_objective"] == pytest.approx(10.0)
        assert metrics["feasibility_rate"] == pytest.approx(1.0)
        assert metrics["n_trials"] == 3

    def test_compute_metrics_with_optimal(self):
        metrics = self.analyzer.compute_metrics(
            objective_values=[8.0, 9.0],
            runtimes=[0.1, 0.1],
            feasibility_flags=[True, True],
            eval_counts=[100, 100],
            optimal_value=10.0,
            objective_direction="max",
        )
        assert "optimality_gap_best_pct" in metrics
        assert metrics["optimality_gap_best_pct"] == pytest.approx(10.0)

    def test_compute_metrics_empty_returns_error(self):
        result = self.analyzer.compute_metrics(
            objective_values=[],
            runtimes=[],
            feasibility_flags=[],
            eval_counts=[],
        )
        assert "error" in result

    def test_compare_algorithms(self):
        result = self.analyzer.compare_algorithms(
            [5.0, 6.0, 7.0], [1.0, 2.0, 3.0], "SA", "GA"
        )
        assert result["label_a"] == "SA"
        assert result["label_b"] == "GA"
        assert "mann_whitney_u" in result

    def test_pairwise_comparison(self):
        algo_results = {
            "sa": [5.0, 6.0, 7.0, 8.0],
            "ga": [4.0, 5.0, 6.0, 7.0],
            "exact": [10.0, 10.0, 10.0, 10.0],
        }
        comparisons = self.analyzer.pairwise_comparison(algo_results)
        assert len(comparisons) == 3  # C(3,2) = 3 pairs

    def test_metrics_feasibility_rate_partial(self):
        metrics = self.analyzer.compute_metrics(
            objective_values=[1.0, 2.0, 3.0, 4.0],
            runtimes=[0.1] * 4,
            feasibility_flags=[True, False, True, False],
            eval_counts=[100] * 4,
        )
        assert metrics["feasibility_rate"] == pytest.approx(0.5)

    def test_minimization_direction(self):
        metrics = self.analyzer.compute_metrics(
            objective_values=[5.0, 3.0, 8.0],
            runtimes=[0.1] * 3,
            feasibility_flags=[True] * 3,
            eval_counts=[100] * 3,
            optimal_value=2.0,
            objective_direction="min",
        )
        assert metrics["best_objective"] == pytest.approx(3.0)

