"""Chart data preparation and serialization helpers for frontend visualizations."""

from typing import Any, Dict, List, Optional
from backend.app.experiments.models import ExperimentResult


def prepare_objective_comparison_data(results: List[ExperimentResult]) -> List[Dict[str, Any]]:
    """Format objective values grouped by algorithm for bar/scatter charts."""
    by_algo: Dict[str, List[float]] = {}
    for r in results:
        if r.status == "completed" and r.objective_value is not None:
            by_algo.setdefault(r.algorithm, []).append(r.objective_value)

    data = []
    for algo, vals in by_algo.items():
        data.append({
            "algorithm": algo,
            "best": max(vals),
            "worst": min(vals),
            "mean": sum(vals) / len(vals),
            "trials": len(vals),
            "values": vals,
        })
    return data


def prepare_runtime_comparison_data(results: List[ExperimentResult]) -> List[Dict[str, Any]]:
    """Format runtimes grouped by algorithm."""
    by_algo: Dict[str, List[float]] = {}
    for r in results:
        by_algo.setdefault(r.algorithm, []).append(r.runtime_seconds)

    data = []
    for algo, vals in by_algo.items():
        data.append({
            "algorithm": algo,
            "mean_runtime": sum(vals) / len(vals) if vals else 0.0,
            "min_runtime": min(vals) if vals else 0.0,
            "max_runtime": max(vals) if vals else 0.0,
            "trials": len(vals),
        })
    return data


def prepare_convergence_series(results: List[ExperimentResult]) -> Dict[str, List[float]]:
    """Extract representative convergence curves per algorithm."""
    curves: Dict[str, List[float]] = {}
    for r in results:
        if r.convergence_history and r.algorithm not in curves:
            curves[r.algorithm] = r.convergence_history
    return curves
