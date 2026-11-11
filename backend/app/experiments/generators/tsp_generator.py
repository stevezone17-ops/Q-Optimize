"""TSP problem instance generator — Euclidean and random distance matrices."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np


def generate_euclidean_tsp(
    num_cities: int,
    coordinate_low: float = 0.0,
    coordinate_high: float = 100.0,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generate a TSP instance from random 2D Euclidean coordinates.
    Distance matrix is symmetric with zero diagonal.
    """
    rng = np.random.default_rng(seed)
    coords = rng.uniform(coordinate_low, coordinate_high, size=(num_cities, 2))
    dist_matrix = np.zeros((num_cities, num_cities))
    for i in range(num_cities):
        for j in range(num_cities):
            if i != j:
                dist_matrix[i, j] = np.sqrt(
                    (coords[i, 0] - coords[j, 0]) ** 2
                    + (coords[i, 1] - coords[j, 1]) ** 2
                )
    dist_matrix = np.round(dist_matrix, 4)
    return {
        "num_cities": num_cities,
        "distance_matrix": dist_matrix.tolist(),
        "coordinates": coords.tolist(),
        "graph_type": "euclidean",
        "seed": seed,
    }


def generate_random_tsp(
    num_cities: int,
    distance_low: float = 1.0,
    distance_high: float = 100.0,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generate a TSP instance from random symmetric distance matrix.
    """
    rng = np.random.default_rng(seed)
    upper = rng.uniform(distance_low, distance_high, size=(num_cities, num_cities))
    # Make symmetric
    dist_matrix = (upper + upper.T) / 2.0
    np.fill_diagonal(dist_matrix, 0.0)
    dist_matrix = np.round(dist_matrix, 4)
    return {
        "num_cities": num_cities,
        "distance_matrix": dist_matrix.tolist(),
        "coordinates": None,
        "graph_type": "random",
        "seed": seed,
    }
