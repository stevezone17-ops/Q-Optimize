"""Assignment problem instance generator — configurable cost matrices."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np


def generate_random_assignment(
    num_agents: int,
    num_tasks: int,
    cost_distribution: str = "uniform",
    cost_low: float = 1.0,
    cost_high: float = 100.0,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generate an assignment problem cost matrix.

    Args:
        num_agents: Number of agents (rows).
        num_tasks: Number of tasks (columns).
        cost_distribution: 'uniform', 'normal', or 'integer'.
        cost_low: Lower bound for uniform/normal distribution.
        cost_high: Upper bound for uniform/normal distribution.
        seed: Random seed for reproducibility.

    Returns:
        Problem instance dict with 'cost_matrix'.
    """
    rng = np.random.default_rng(seed)

    if cost_distribution == "uniform":
        matrix = rng.uniform(cost_low, cost_high, size=(num_agents, num_tasks))
    elif cost_distribution == "normal":
        mean = (cost_low + cost_high) / 2.0
        std = (cost_high - cost_low) / 6.0
        matrix = rng.normal(mean, std, size=(num_agents, num_tasks))
        matrix = np.clip(matrix, cost_low, cost_high)
    elif cost_distribution == "integer":
        matrix = rng.integers(int(cost_low), int(cost_high) + 1, size=(num_agents, num_tasks)).astype(float)
    else:
        raise ValueError(f"Unknown cost_distribution: '{cost_distribution}'. Use 'uniform', 'normal', or 'integer'.")

    matrix = np.round(matrix, 4)
    return {
        "num_agents": num_agents,
        "num_tasks": num_tasks,
        "cost_matrix": matrix.tolist(),
        "cost_distribution": cost_distribution,
        "cost_low": cost_low,
        "cost_high": cost_high,
        "seed": seed,
    }
