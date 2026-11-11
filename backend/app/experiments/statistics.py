"""Statistical analysis engine for benchmarking results."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

try:
    from scipy import stats as scipy_stats
    _SCIPY_AVAILABLE = True
except ImportError:
    _SCIPY_AVAILABLE = False


# ---------------------------------------------------------------------------
# Core metric helpers
# ---------------------------------------------------------------------------

def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def _variance(values: List[float]) -> float:
    if len(values) < 2:
        return float("nan")
    m = _mean(values)
    return sum((x - m) ** 2 for x in values) / (len(values) - 1)


def _std(values: List[float]) -> float:
    v = _variance(values)
    return math.sqrt(v) if not math.isnan(v) else float("nan")


def _median(values: List[float]) -> float:
    if not values:
        return float("nan")
    s = sorted(values)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2.0


def _t_confidence_interval(values: List[float], alpha: float = 0.05) -> Tuple[float, float]:
    """Two-sided (1-alpha)% confidence interval using t-distribution."""
    n = len(values)
    if n < 2:
        return (float("nan"), float("nan"))
    m = _mean(values)
    s = _std(values)
    if _SCIPY_AVAILABLE:
        t_crit = scipy_stats.t.ppf(1 - alpha / 2, df=n - 1)
    else:
        # Approximate for large n
        t_crit = 1.96
    margin = t_crit * s / math.sqrt(n)
    return (m - margin, m + margin)


def optimality_gap(candidate: float, optimal: float) -> float:
    """
    Percentage gap: |C_candidate - C_optimal| / |C_optimal| * 100.
    Returns NaN when optimal is zero.
    """
    if optimal == 0.0:
        return float("nan")
    return abs(candidate - optimal) / abs(optimal) * 100.0


def approximation_ratio(
    candidate: float, optimal: float, objective_direction: str = "max"
) -> float:
    """
    Approximation ratio.
    For maximization: ratio = candidate / optimal.
    For minimization: ratio = optimal / candidate.
    Returns NaN on division by zero.
    """
    if objective_direction == "max":
        if optimal == 0.0:
            return float("nan")
        return candidate / optimal
    else:
        if candidate == 0.0:
            return float("nan")
        return optimal / candidate


# ---------------------------------------------------------------------------
# Statistical tests
# ---------------------------------------------------------------------------

def mann_whitney_u(
    sample_a: List[float],
    sample_b: List[float],
    alternative: str = "two-sided",
) -> Dict[str, Any]:
    """
    Mann-Whitney U test for independent samples.
    Returns test name, statistic, p-value, sample sizes, effect size (rank-biserial r).
    """
    if not _SCIPY_AVAILABLE:
        return {
            "test": "mann_whitney_u",
            "error": "scipy not available",
            "statistic": float("nan"),
            "p_value": float("nan"),
        }
    if len(sample_a) < 2 or len(sample_b) < 2:
        return {
            "test": "mann_whitney_u",
            "error": "Insufficient sample sizes (need >= 2 each)",
            "statistic": float("nan"),
            "p_value": float("nan"),
        }
    u_stat, p_value = scipy_stats.mannwhitneyu(sample_a, sample_b, alternative=alternative)
    n1, n2 = len(sample_a), len(sample_b)
    # Rank-biserial correlation (effect size)
    r = 1 - (2 * u_stat) / (n1 * n2)
    return {
        "test": "mann_whitney_u",
        "statistic": float(u_stat),
        "p_value": float(p_value),
        "n_a": n1,
        "n_b": n2,
        "effect_size_r": float(r),
        "alternative": alternative,
        "assumptions": "Independent samples. Non-parametric.",
    }


def wilcoxon_signed_rank(
    sample_a: List[float],
    sample_b: List[float],
    alternative: str = "two-sided",
) -> Dict[str, Any]:
    """
    Wilcoxon signed-rank test for paired samples.
    """
    if not _SCIPY_AVAILABLE:
        return {
            "test": "wilcoxon_signed_rank",
            "error": "scipy not available",
            "statistic": float("nan"),
            "p_value": float("nan"),
        }
    if len(sample_a) != len(sample_b):
        return {
            "test": "wilcoxon_signed_rank",
            "error": "Sample sizes must be equal for paired test.",
            "statistic": float("nan"),
            "p_value": float("nan"),
        }
    if len(sample_a) < 5:
        return {
            "test": "wilcoxon_signed_rank",
            "error": "Insufficient sample size (need >= 5 for Wilcoxon)",
            "statistic": float("nan"),
            "p_value": float("nan"),
        }
    try:
        w_stat, p_value = scipy_stats.wilcoxon(sample_a, sample_b, alternative=alternative)
    except Exception as exc:
        return {
            "test": "wilcoxon_signed_rank",
            "error": str(exc),
            "statistic": float("nan"),
            "p_value": float("nan"),
        }
    return {
        "test": "wilcoxon_signed_rank",
        "statistic": float(w_stat),
        "p_value": float(p_value),
        "n": len(sample_a),
        "alternative": alternative,
        "assumptions": "Paired samples. Non-parametric.",
    }


def cohens_d(sample_a: List[float], sample_b: List[float]) -> float:
    """Cohen's d effect size."""
    if len(sample_a) < 2 or len(sample_b) < 2:
        return float("nan")
    m_a, m_b = _mean(sample_a), _mean(sample_b)
    s_a, s_b = _std(sample_a), _std(sample_b)
    n_a, n_b = len(sample_a), len(sample_b)
    pooled_std = math.sqrt(
        ((n_a - 1) * s_a ** 2 + (n_b - 1) * s_b ** 2) / (n_a + n_b - 2)
    )
    if pooled_std == 0.0:
        return float("nan")
    return (m_a - m_b) / pooled_std


# ---------------------------------------------------------------------------
# Main Analyzer class
# ---------------------------------------------------------------------------

class StatisticalAnalyzer:
    """Computes performance metrics and runs statistical tests on benchmark results."""

    def compute_metrics(
        self,
        objective_values: List[float],
        runtimes: List[float],
        feasibility_flags: List[bool],
        eval_counts: List[int],
        optimal_value: Optional[float] = None,
        objective_direction: str = "max",
    ) -> Dict[str, Any]:
        """
        Compute comprehensive performance metrics for a set of trials.

        Args:
            objective_values: Objective values from each trial.
            runtimes: Wall-clock runtimes (seconds) per trial.
            feasibility_flags: Boolean feasibility indicator per trial.
            eval_counts: Number of function evaluations per trial.
            optimal_value: Known optimal (for gap/ratio computation).
            objective_direction: 'max' or 'min'.

        Returns:
            Dict with best/mean/median/worst/std objective, runtime stats,
            feasibility rate, success rate, optimality gap, approximation ratio,
            confidence intervals.
        """
        if not objective_values:
            return {"error": "No results to analyze."}

        n = len(objective_values)
        best_obj = max(objective_values) if objective_direction == "max" else min(objective_values)
        worst_obj = min(objective_values) if objective_direction == "max" else max(objective_values)
        mean_obj = _mean(objective_values)
        median_obj = _median(objective_values)
        std_obj = _std(objective_values)
        ci_obj = _t_confidence_interval(objective_values)

        mean_rt = _mean(runtimes)
        std_rt = _std(runtimes)
        min_rt = min(runtimes) if runtimes else float("nan")
        max_rt = max(runtimes) if runtimes else float("nan")

        feasibility_rate = sum(1 for f in feasibility_flags if f) / n if n > 0 else 0.0
        mean_evals = _mean([float(e) for e in eval_counts]) if eval_counts else float("nan")

        result: Dict[str, Any] = {
            "n_trials": n,
            "objective_direction": objective_direction,
            "best_objective": best_obj,
            "worst_objective": worst_obj,
            "mean_objective": mean_obj,
            "median_objective": median_obj,
            "std_objective": std_obj,
            "ci_95_objective": {"lower": ci_obj[0], "upper": ci_obj[1]},
            "mean_runtime_seconds": mean_rt,
            "std_runtime_seconds": std_rt,
            "min_runtime_seconds": min_rt,
            "max_runtime_seconds": max_rt,
            "feasibility_rate": feasibility_rate,
            "mean_evaluations": mean_evals,
        }

        if optimal_value is not None:
            best_gap = optimality_gap(best_obj, optimal_value)
            best_ratio = approximation_ratio(best_obj, optimal_value, objective_direction)
            mean_gap = optimality_gap(mean_obj, optimal_value)
            result["optimality_gap_best_pct"] = best_gap
            result["optimality_gap_mean_pct"] = mean_gap
            result["approximation_ratio_best"] = best_ratio

        return result

    def compare_algorithms(
        self,
        samples_a: List[float],
        samples_b: List[float],
        label_a: str = "Algorithm A",
        label_b: str = "Algorithm B",
    ) -> Dict[str, Any]:
        """
        Run statistical comparison between two algorithm samples.
        Returns Mann-Whitney U, Cohen's d, and descriptive stats.
        """
        mw = mann_whitney_u(samples_a, samples_b)
        d = cohens_d(samples_a, samples_b)
        return {
            "label_a": label_a,
            "label_b": label_b,
            "n_a": len(samples_a),
            "n_b": len(samples_b),
            "mean_a": _mean(samples_a),
            "mean_b": _mean(samples_b),
            "mann_whitney_u": mw,
            "cohens_d": d,
        }

    def pairwise_comparison(
        self, algorithm_results: Dict[str, List[float]]
    ) -> List[Dict[str, Any]]:
        """
        Run pairwise Mann-Whitney U tests for all algorithm pairs.

        Args:
            algorithm_results: Dict mapping algorithm name to list of objective values.

        Returns:
            List of comparison dicts.
        """
        algorithms = list(algorithm_results.keys())
        comparisons = []
        for i in range(len(algorithms)):
            for j in range(i + 1, len(algorithms)):
                label_a = algorithms[i]
                label_b = algorithms[j]
                comparisons.append(
                    self.compare_algorithms(
                        algorithm_results[label_a],
                        algorithm_results[label_b],
                        label_a=label_a,
                        label_b=label_b,
                    )
                )
        return comparisons


statistical_analyzer = StatisticalAnalyzer()

