"""Dataset construction and solver-selection policy for optimization experiment records."""

import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timezone

from backend.app.domain.problems.models import ProblemType
from backend.app.ai.models import (
    ExperimentRecord,
    TrainingSample,
    TrainingDatasetMetadata,
    OptimizationFeatures,
    SolverCandidate,
)
from backend.app.ai.feature_extraction import default_feature_extractor
from backend.app.ai.config import ai_settings
from backend.app.core.logging import logger


class SolverSelectionPolicy:
    """
    Principled, documented multi-objective policy for labeling the preferred solver
    for a given optimization problem instance based on measured trial runs.
    """

    @classmethod
    def select_best_solver(
        cls,
        problem_type: ProblemType,
        runs: List[ExperimentRecord],
    ) -> Optional[str]:
        """
        Select preferred solver according to feasibility, objective quality, and runtime efficiency.
        Returns canonical solver name or None if no valid runs.
        """
        if not runs:
            return None

        # Filter to feasible runs first
        feasible_runs = [r for r in runs if r.is_feasible and r.objective_value is not None]
        candidates = feasible_runs if feasible_runs else runs

        # Score runs
        scored_runs: List[Tuple[float, float, str, ExperimentRecord]] = []
        is_max = (problem_type == ProblemType.MAX_CUT)

        for r in candidates:
            obj = r.objective_value if r.objective_value is not None else (-1e9 if is_max else 1e9)
            norm_solver = cls.normalize_solver_name(r.solver_name)
            # Preference key: (quality_score, -runtime)
            # For maximize: higher obj is better (+obj)
            # For minimize: lower obj is better (-obj)
            quality = float(obj) if is_max else -float(obj)
            runtime = max(0.0001, r.runtime_seconds)
            scored_runs.append((quality, -runtime, norm_solver, r))

        # Sort descending by quality, then by runtime efficiency
        scored_runs.sort(key=lambda x: (x[0], x[1]), reverse=True)
        best_quality = scored_runs[0][0]

        # Consider top-tier within 1% of best quality
        top_tier = [sr for sr in scored_runs if abs(sr[0] - best_quality) <= 0.01 * (abs(best_quality) + 1e-6)]

        # Check if Exact solver is in top tier (ground truth optimality preferred)
        for _, _, s_name, _ in top_tier:
            if s_name == SolverCandidate.EXACT.value:
                return SolverCandidate.EXACT.value

        # Otherwise pick the most efficient in top tier (highest -runtime, i.e. lowest runtime)
        top_tier.sort(key=lambda x: x[1], reverse=True)
        return top_tier[0][2]

    @classmethod
    def normalize_solver_name(cls, raw_name: str) -> str:
        """Map raw solver ID or variant to one of the 5 canonical recommendation labels."""
        raw_lower = raw_name.lower().replace("-", "_").replace(" ", "_")

        if "exact" in raw_lower:
            return SolverCandidate.EXACT.value
        elif "genetic" in raw_lower or "ga" == raw_lower:
            return SolverCandidate.GENETIC_ALGORITHM.value
        elif "anneal" in raw_lower or "sa" == raw_lower:
            return SolverCandidate.SIMULATED_ANNEALING.value
        elif "adaptive" in raw_lower or "aqaoa" in raw_lower:
            return SolverCandidate.ADAPTIVE_QAOA.value
        elif "qaoa" in raw_lower:
            return SolverCandidate.STANDARD_QAOA.value

        return raw_lower


class ExperimentDatasetBuilder:
    """Constructs versioned, group-aware training datasets from experiment records."""

    @classmethod
    def build_dataset(
        cls,
        records: List[ExperimentRecord],
        dataset_version: str = "v1.0.0",
        policy: Optional[SolverSelectionPolicy] = None,
    ) -> Tuple[List[TrainingSample], TrainingDatasetMetadata]:
        """
        Aggregate records by problem instance, extract features, apply selection policy,
        and generate clean training samples with metadata.
        """
        policy = policy or SolverSelectionPolicy()

        # Group records by unique instance
        groups: Dict[str, List[ExperimentRecord]] = defaultdict(list)
        for rec in records:
            if not rec.is_valid_for_training:
                continue
            inst_key = cls._compute_instance_key(rec)
            groups[inst_key].append(rec)

        samples: List[TrainingSample] = []
        class_counts: Dict[str, int] = defaultdict(int)
        type_counts: Dict[str, int] = defaultdict(int)
        source_types: Set[str] = set()

        for inst_key, group_records in groups.items():
            rep = group_records[0]
            prob_type = rep.problem_type
            inst_data = rep.instance_data

            # Best solver via policy
            best_solver = policy.select_best_solver(prob_type, group_records)
            if not best_solver:
                continue

            # Ensure features are present
            features = rep.features
            if features is None:
                if inst_data:
                    features = default_feature_extractor.extract_features(prob_type, inst_data)
                else:
                    # Synthesize basic features from problem type & record properties
                    features = OptimizationFeatures(
                        schema_version=ai_settings.FEATURE_SCHEMA_VERSION,
                        problem_type=prob_type,
                        num_variables=max(4, rep.evaluation_count // 10 if rep.evaluation_count else 6),
                        estimated_search_space_log2=6.0,
                    )

            # Record solver evaluations
            solver_evals = {}
            for r in group_records:
                norm_s = policy.normalize_solver_name(r.solver_name)
                solver_evals[norm_s] = {
                    "objective_value": r.objective_value,
                    "runtime_seconds": r.runtime_seconds,
                    "is_feasible": r.is_feasible,
                    "evaluation_count": r.evaluation_count,
                }
                source_types.add(r.provenance_collection)

            sample = TrainingSample(
                instance_id=inst_key,
                problem_type=prob_type,
                features=features,
                feature_vector=features.to_feature_vector(),
                best_solver_label=best_solver,
                solver_evaluations=solver_evals,
            )
            samples.append(sample)
            class_counts[best_solver] += 1
            type_counts[prob_type.value] += 1

        metadata = TrainingDatasetMetadata(
            dataset_id=f"opt_dataset_{dataset_version}_{len(samples)}_samples",
            dataset_version=dataset_version,
            total_samples=len(samples),
            class_distribution=dict(class_counts),
            problem_type_counts=dict(type_counts),
            source_experiment_types=sorted(list(source_types)),
            created_at=datetime.now(timezone.utc),
            provenance_summary=f"Constructed from {len(records)} raw experiment runs across {len(samples)} problem instances",
        )

        logger.info(f"Built training dataset {metadata.dataset_id}: {len(samples)} samples, classes={metadata.class_distribution}")
        return samples, metadata

    @classmethod
    def _compute_instance_key(cls, rec: ExperimentRecord) -> str:
        """Compute unique identifier for problem instance to ensure group-aware separation."""
        if rec.problem_id and not rec.problem_id.startswith("ad-hoc"):
            return f"{rec.problem_type.value}_{rec.problem_id}"

        # Hash instance data dictionary
        if rec.instance_data:
            dumped = json.dumps(rec.instance_data, sort_keys=True)
            h = hashlib.sha256(dumped.encode("utf-8")).hexdigest()[:12]
            return f"{rec.problem_type.value}_{h}"

        return f"{rec.problem_type.value}_{rec.record_id}"

    @classmethod
    def create_sample_test_dataset(cls) -> Tuple[List[TrainingSample], TrainingDatasetMetadata]:
        """
        Creates a dedicated, isolated sample dataset strictly for automated software tests
        and pipeline validation. Clearly identified and never mixed with real production models.
        """
        records: List[ExperimentRecord] = []
        solvers = [
            SolverCandidate.EXACT.value,
            SolverCandidate.GENETIC_ALGORITHM.value,
            SolverCandidate.SIMULATED_ANNEALING.value,
            SolverCandidate.STANDARD_QAOA.value,
            SolverCandidate.ADAPTIVE_QAOA.value,
        ]

        # Generate 20 diverse synthetic benchmark instances for pipeline testing
        for i in range(20):
            p_type = ProblemType.MAX_CUT if i % 3 == 0 else (ProblemType.ASSIGNMENT if i % 3 == 1 else ProblemType.TSP)
            inst_id = f"test_inst_{p_type.value}_{i}"

            # Create dummy instance data
            if p_type == ProblemType.MAX_CUT:
                inst_data = {
                    "nodes": [f"V{j}" for j in range(4 + (i % 6))],
                    "edges": [[f"V{j}", f"V{(j+1)%4}", 1.0 + (i % 3)] for j in range(4)],
                }
            elif p_type == ProblemType.ASSIGNMENT:
                sz = 3 + (i % 4)
                inst_data = {
                    "agents": [f"A{j}" for j in range(sz)],
                    "tasks": [f"T{j}" for j in range(sz)],
                    "cost_matrix": [[float(j + k + 1) for k in range(sz)] for j in range(sz)],
                }
            else:
                sz = 3 + (i % 4)
                inst_data = {
                    "cities": [f"C{j}" for j in range(sz)],
                    "distance_matrix": [[0.0 if j == k else float(abs(j - k) * 5) for k in range(sz)] for j in range(sz)],
                }

            # Create runs for all solvers on this instance
            for s in solvers:
                # Modulate performance by problem size
                is_exact_preferred = (i % 5 == 0) and (s == SolverCandidate.EXACT.value)
                is_ga_preferred = (i % 5 == 1) and (s == SolverCandidate.GENETIC_ALGORITHM.value)
                is_sa_preferred = (i % 5 == 2) and (s == SolverCandidate.SIMULATED_ANNEALING.value)
                is_qaoa_preferred = (i % 5 == 3) and (s == SolverCandidate.STANDARD_QAOA.value)
                is_aqaoa_preferred = (i % 5 == 4) and (s == SolverCandidate.ADAPTIVE_QAOA.value)

                best = (is_exact_preferred or is_ga_preferred or is_sa_preferred or is_qaoa_preferred or is_aqaoa_preferred)
                obj_val = 100.0 if (best and p_type == ProblemType.MAX_CUT) else (10.0 if best else 50.0)

                rec = ExperimentRecord(
                    record_id=f"sample_{inst_id}_{s}",
                    provenance_collection="sample_test_store",
                    problem_id=inst_id,
                    problem_type=p_type,
                    instance_data=inst_data,
                    solver_name=s,
                    solver_category="quantum_simulator" if "qaoa" in s else "classical",
                    status="COMPLETED",
                    is_feasible=True,
                    objective_value=obj_val,
                    runtime_seconds=0.01 if best else 0.05,
                    evaluation_count=20 if best else 80,
                    is_valid_for_training=True,
                )
                records.append(rec)

        samples, meta = cls.build_dataset(records, dataset_version="test_sample_v1")
        meta.provenance_summary = "ISOLATED_TEST_DATASET_FOR_UNIT_TESTS_ONLY"
        return samples, meta
