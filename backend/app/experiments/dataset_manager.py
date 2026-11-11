"""Benchmark dataset manager — creates, stores, and retrieves reproducible problem instances."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Dict, List, Optional

from backend.app.db.mongodb import db_manager
from backend.app.experiments.dataset_models import BenchmarkDataset, DatasetMetadata, ProblemInstance
from backend.app.experiments.experiment_exceptions import DatasetNotFoundError
from backend.app.experiments.generators.max_cut_generator import (
    generate_erdos_renyi,
    generate_random_regular,
)
from backend.app.experiments.generators.assignment_generator import generate_random_assignment
from backend.app.experiments.generators.tsp_generator import (
    generate_euclidean_tsp,
    generate_random_tsp,
)
from backend.app.core.logging import logger

DATASET_COLLECTION = "benchmark_datasets"


def _fingerprint(instance_data: Dict[str, Any]) -> str:
    """Compute a stable SHA-256 fingerprint of an instance."""
    canonical = json.dumps(instance_data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


class BenchmarkDatasetManager:
    """Creates, stores, and retrieves reproducible benchmark datasets."""

    # ------------------------------------------------------------------ #
    # Max-Cut generators
    # ------------------------------------------------------------------ #
    def generate_max_cut_erdos_renyi(
        self,
        num_nodes: int,
        edge_probability: float = 0.5,
        num_instances: int = 1,
        base_seed: Optional[int] = None,
        weighted: bool = False,
        name: str = "Max-Cut Erdős–Rényi Dataset",
        tags: List[str] = None,
    ) -> BenchmarkDataset:
        return self._build_dataset(
            problem_type="max_cut",
            generator_type="erdos_renyi",
            generator_params={"num_nodes": num_nodes, "edge_probability": edge_probability, "weighted": weighted},
            num_instances=num_instances,
            base_seed=base_seed,
            generator_fn=lambda seed: generate_erdos_renyi(num_nodes, edge_probability, seed=seed, weighted=weighted),
            name=name,
            tags=tags or [],
        )

    def generate_max_cut_random_regular(
        self,
        num_nodes: int,
        degree: int,
        num_instances: int = 1,
        base_seed: Optional[int] = None,
        weighted: bool = False,
        name: str = "Max-Cut Random Regular Dataset",
        tags: List[str] = None,
    ) -> BenchmarkDataset:
        return self._build_dataset(
            problem_type="max_cut",
            generator_type="random_regular",
            generator_params={"num_nodes": num_nodes, "degree": degree, "weighted": weighted},
            num_instances=num_instances,
            base_seed=base_seed,
            generator_fn=lambda seed: generate_random_regular(num_nodes, degree, seed=seed, weighted=weighted),
            name=name,
            tags=tags or [],
        )

    # ------------------------------------------------------------------ #
    # Assignment generators
    # ------------------------------------------------------------------ #
    def generate_assignment_dataset(
        self,
        num_agents: int,
        num_tasks: int,
        cost_distribution: str = "uniform",
        num_instances: int = 1,
        base_seed: Optional[int] = None,
        name: str = "Assignment Dataset",
        tags: List[str] = None,
    ) -> BenchmarkDataset:
        return self._build_dataset(
            problem_type="assignment",
            generator_type="random_assignment",
            generator_params={"num_agents": num_agents, "num_tasks": num_tasks, "cost_distribution": cost_distribution},
            num_instances=num_instances,
            base_seed=base_seed,
            generator_fn=lambda seed: generate_random_assignment(num_agents, num_tasks, cost_distribution=cost_distribution, seed=seed),
            name=name,
            tags=tags or [],
        )

    # ------------------------------------------------------------------ #
    # TSP generators
    # ------------------------------------------------------------------ #
    def generate_tsp_euclidean(
        self,
        num_cities: int,
        num_instances: int = 1,
        base_seed: Optional[int] = None,
        name: str = "TSP Euclidean Dataset",
        tags: List[str] = None,
    ) -> BenchmarkDataset:
        return self._build_dataset(
            problem_type="tsp",
            generator_type="euclidean_tsp",
            generator_params={"num_cities": num_cities},
            num_instances=num_instances,
            base_seed=base_seed,
            generator_fn=lambda seed: generate_euclidean_tsp(num_cities, seed=seed),
            name=name,
            tags=tags or [],
        )

    def generate_tsp_random(
        self,
        num_cities: int,
        num_instances: int = 1,
        base_seed: Optional[int] = None,
        name: str = "TSP Random Dataset",
        tags: List[str] = None,
    ) -> BenchmarkDataset:
        return self._build_dataset(
            problem_type="tsp",
            generator_type="random_tsp",
            generator_params={"num_cities": num_cities},
            num_instances=num_instances,
            base_seed=base_seed,
            generator_fn=lambda seed: generate_random_tsp(num_cities, seed=seed),
            name=name,
            tags=tags or [],
        )

    # ------------------------------------------------------------------ #
    # Storage operations
    # ------------------------------------------------------------------ #
    def save(self, dataset: BenchmarkDataset) -> None:
        db_manager.memory_insert(
            DATASET_COLLECTION,
            dataset.metadata.dataset_id,
            dataset.model_dump(mode="json"),
        )

    def get(self, dataset_id: str) -> BenchmarkDataset:
        raw = db_manager.memory_get(DATASET_COLLECTION, dataset_id)
        if raw is None:
            raise DatasetNotFoundError(dataset_id)
        return BenchmarkDataset.model_validate(raw)

    def list_datasets(self) -> List[BenchmarkDataset]:
        return [
            BenchmarkDataset.model_validate(r)
            for r in db_manager.memory_list(DATASET_COLLECTION)
        ]

    def delete(self, dataset_id: str) -> bool:
        self.get(dataset_id)  # raises if not found
        return db_manager.memory_delete(DATASET_COLLECTION, dataset_id)

    # ------------------------------------------------------------------ #
    # Internal builder
    # ------------------------------------------------------------------ #
    def _build_dataset(
        self,
        problem_type: str,
        generator_type: str,
        generator_params: Dict[str, Any],
        num_instances: int,
        base_seed: Optional[int],
        generator_fn,
        name: str,
        tags: List[str],
    ) -> BenchmarkDataset:
        dataset_id = str(uuid.uuid4())
        instances: List[ProblemInstance] = []
        for idx in range(num_instances):
            seed = (base_seed + idx) if base_seed is not None else None
            instance_data = generator_fn(seed)
            fp = _fingerprint(instance_data)
            instances.append(
                ProblemInstance(
                    instance_id=str(uuid.uuid4()),
                    dataset_id=dataset_id,
                    problem_type=problem_type,
                    instance_data=instance_data,
                    fingerprint=fp,
                    seed=seed,
                )
            )

        # Dataset-level fingerprint: hash of all instance fingerprints
        all_fps = "|".join(sorted(i.fingerprint for i in instances))
        dataset_fp = hashlib.sha256(all_fps.encode()).hexdigest()

        metadata = DatasetMetadata(
            dataset_id=dataset_id,
            name=name,
            problem_type=problem_type,
            generator_type=generator_type,
            generator_params=generator_params,
            fingerprint=dataset_fp,
            num_instances=num_instances,
            tags=tags,
        )
        dataset = BenchmarkDataset(metadata=metadata, instances=instances)
        self.save(dataset)
        logger.info(f"Generated dataset '{dataset_id}' ({generator_type}, {num_instances} instances)")
        return dataset


dataset_manager = BenchmarkDatasetManager()
