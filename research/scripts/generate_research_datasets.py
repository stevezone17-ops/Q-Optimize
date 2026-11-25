"""Stage 10.2 — Controlled Research Dataset Generator.

Generates reproducible Max-Cut, Linear Assignment, and TSP datasets using
BenchmarkDatasetManager, normalizes them into canonical Q-Optimize schemas,
computes QUBO variable counts and SHA-256 fingerprints, and persists the
canonical dataset catalog to research/datasets/qoptimize_research_datasets.json.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.experiments.dataset_manager import BenchmarkDatasetManager
from backend.app.formulations.engine import FormulationEngine


def _canonicalize_instance(problem_type: str, raw: Dict[str, Any]) -> Dict[str, Any]:
    """Convert generator output into canonical Q-Optimize solver/formulation schema."""
    if problem_type == "max_cut":
        n = int(raw["num_nodes"])
        nodes = [f"N{i}" for i in range(n)]
        edges = []
        seen = set()
        for e in raw.get("edge_list", []):
            u, v = int(e[0]), int(e[1])
            if u == v:
                continue
            key = (min(u, v), max(u, v))
            if key in seen:
                continue
            seen.add(key)
            w = round(float(e[2]), 4) if len(e) > 2 else 1.0
            edges.append([f"N{key[0]}", f"N{key[1]}", w])
        return {"nodes": nodes, "edges": edges}

    if problem_type == "assignment":
        mat = raw["cost_matrix"]
        n_agents = len(mat)
        n_tasks = len(mat[0]) if mat else 0
        return {
            "agents": [f"A{i}" for i in range(n_agents)],
            "tasks": [f"T{j}" for j in range(n_tasks)],
            "cost_matrix": [[round(float(x), 4) for x in row] for row in mat],
        }

    if problem_type == "tsp":
        mat = raw["distance_matrix"]
        n_cities = len(mat)
        return {
            "cities": [f"C{i}" for i in range(n_cities)],
            "distance_matrix": [[round(float(x), 4) for x in row] for row in mat],
            "symmetric": True,
        }

    raise ValueError(f"Unsupported problem type: {problem_type}")


def _sha256(data: Dict[str, Any]) -> str:
    canonical = json.dumps(data, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def main() -> None:
    mgr = BenchmarkDatasetManager()
    form_engine = FormulationEngine()

    specs = [
        ("mc_er_n6_p05", lambda: mgr.generate_max_cut_erdos_renyi(6, 0.5, num_instances=3, base_seed=1001, weighted=False, name="Max-Cut ER N=6 p=0.5 Unweighted")),
        ("mc_er_n8_p05_w", lambda: mgr.generate_max_cut_erdos_renyi(8, 0.5, num_instances=3, base_seed=1010, weighted=True, name="Max-Cut ER N=8 p=0.5 Weighted")),
        ("mc_reg_n8_d3", lambda: mgr.generate_max_cut_random_regular(8, 3, num_instances=3, base_seed=1020, weighted=False, name="Max-Cut 3-Regular N=8")),
        ("mc_er_n10_p06_w", lambda: mgr.generate_max_cut_erdos_renyi(10, 0.6, num_instances=2, base_seed=1030, weighted=True, name="Max-Cut ER N=10 p=0.6 Weighted")),
        ("assign_3x3_uniform", lambda: mgr.generate_assignment_dataset(3, 3, cost_distribution="uniform", num_instances=3, base_seed=2001, name="Assignment 3x3 Uniform")),
        ("assign_3x3_normal", lambda: mgr.generate_assignment_dataset(3, 3, cost_distribution="normal", num_instances=2, base_seed=2010, name="Assignment 3x3 Normal")),
        ("assign_4x4_uniform", lambda: mgr.generate_assignment_dataset(4, 4, cost_distribution="uniform", num_instances=2, base_seed=2020, name="Assignment 4x4 Uniform")),
        ("tsp_3city_euclid", lambda: mgr.generate_tsp_euclidean(3, num_instances=3, base_seed=3001, name="TSP 3-City Euclidean")),
        ("tsp_4city_euclid", lambda: mgr.generate_tsp_euclidean(4, num_instances=2, base_seed=3010, name="TSP 4-City Euclidean")),
    ]

    datasets_out: List[Dict[str, Any]] = []
    total_instances = 0

    for family_key, builder_fn in specs:
        ds = builder_fn()
        instances_enriched: List[Dict[str, Any]] = []
        for idx, inst in enumerate(ds.instances):
            canonical = _canonicalize_instance(ds.metadata.problem_type, inst.instance_data)
            qubo = form_engine.generate_qubo(ds.metadata.problem_type, canonical)
            instances_enriched.append({
                "instance_id": f"{family_key}_i{idx+1}",
                "seed": inst.seed,
                "fingerprint_sha256": _sha256(canonical),
                "qubo_variables": len(qubo.variable_order),
                "qubo_quadratic_terms": len(qubo.quadratic_terms),
                "instance_data": canonical,
            })
            total_instances += 1

        datasets_out.append({
            "family_key": family_key,
            "dataset_id": ds.metadata.dataset_id,
            "name": ds.metadata.name,
            "problem_type": ds.metadata.problem_type,
            "generator_type": ds.metadata.generator_type,
            "generator_params": ds.metadata.generator_params,
            "num_instances": len(instances_enriched),
            "instances": instances_enriched,
        })

    out_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_families": len(datasets_out),
        "total_instances": total_instances,
        "datasets": datasets_out,
    }

    out_path = REPO_ROOT / "research" / "datasets" / "qoptimize_research_datasets.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out_payload, indent=2), encoding="utf-8")
    print(f"Generated {len(datasets_out)} dataset families ({total_instances} total instances) -> {out_path}")


if __name__ == "__main__":
    main()
