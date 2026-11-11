"""Max-Cut problem instance generator — Erdős–Rényi and Random Regular graphs."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def generate_erdos_renyi(
    num_nodes: int,
    edge_probability: float = 0.5,
    seed: Optional[int] = None,
    weighted: bool = False,
    weight_low: float = 1.0,
    weight_high: float = 10.0,
) -> Dict[str, Any]:
    """Generate a Max-Cut instance using an Erdős–Rényi random graph G(n, p)."""
    rng = np.random.default_rng(seed)
    edge_list: List[List] = []
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            if rng.random() < edge_probability:
                if weighted:
                    w = float(rng.uniform(weight_low, weight_high))
                    edge_list.append([i, j, w])
                else:
                    edge_list.append([i, j])
    return {
        "num_nodes": num_nodes,
        "edge_list": edge_list,
        "graph_type": "erdos_renyi",
        "edge_probability": edge_probability,
        "weighted": weighted,
        "seed": seed,
    }


def generate_random_regular(
    num_nodes: int,
    degree: int,
    seed: Optional[int] = None,
    weighted: bool = False,
    weight_low: float = 1.0,
    weight_high: float = 10.0,
) -> Dict[str, Any]:
    """
    Generate a Max-Cut instance from a random d-regular graph.
    num_nodes * degree must be even.
    """
    if (num_nodes * degree) % 2 != 0:
        raise ValueError("num_nodes * degree must be even for a regular graph.")
    if degree >= num_nodes:
        raise ValueError("degree must be less than num_nodes.")

    rng = np.random.default_rng(seed)
    # Pairing stubs algorithm
    stubs = list(range(num_nodes)) * degree
    rng.shuffle(stubs)
    edge_set: set = set()
    edge_list: List[List] = []

    attempts = 0
    while len(edge_set) < (num_nodes * degree) // 2 and attempts < 100:
        attempts += 1
        rng.shuffle(stubs)
        edge_set = set()
        edge_list = []
        ok = True
        for k in range(0, len(stubs), 2):
            u, v = stubs[k], stubs[k + 1]
            if u == v or (min(u, v), max(u, v)) in edge_set:
                ok = False
                break
            edge_set.add((min(u, v), max(u, v)))
            if weighted:
                w = float(rng.uniform(weight_low, weight_high))
                edge_list.append([min(u, v), max(u, v), w])
            else:
                edge_list.append([min(u, v), max(u, v)])
        if ok:
            break

    return {
        "num_nodes": num_nodes,
        "edge_list": edge_list,
        "graph_type": "random_regular",
        "degree": degree,
        "weighted": weighted,
        "seed": seed,
    }
