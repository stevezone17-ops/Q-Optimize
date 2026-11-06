"""Unified data access layer for retrieving and validating historical optimization experiments."""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone

from backend.app.db.mongodb import db_manager
from backend.app.domain.problems.models import ProblemType
from backend.app.ai.models import ExperimentRecord
from backend.app.ai.exceptions import DataQualityError
from backend.app.core.logging import logger


class ExperimentDataAccess:
    """Unified access layer retrieving records across classical and quantum execution stores."""

    @classmethod
    async def fetch_all_experiments(
        cls,
        include_classical: bool = True,
        include_qaoa: bool = True,
        include_adaptive: bool = True,
        include_benchmarks: bool = True,
        filter_failed: bool = True,
    ) -> List[ExperimentRecord]:
        """
        Aggregate, normalize, and validate optimization experiment records across all persistence stores.
        Enforces deduplication and data-quality checks.
        """
        records: List[ExperimentRecord] = []
        seen_keys: Set[str] = set()

        if include_classical:
            classical_records = await cls._fetch_classical_executions()
            cls._merge_records(records, classical_records, seen_keys, filter_failed)

        if include_qaoa:
            qaoa_records = await cls._fetch_quantum_executions()
            cls._merge_records(records, qaoa_records, seen_keys, filter_failed)

        if include_adaptive:
            adaptive_records = await cls._fetch_adaptive_executions()
            cls._merge_records(records, adaptive_records, seen_keys, filter_failed)

        if include_benchmarks:
            benchmark_records = await cls._fetch_benchmark_trials()
            cls._merge_records(records, benchmark_records, seen_keys, filter_failed)

        logger.info(f"ExperimentDataAccess fetched {len(records)} normalized valid experiment records")
        return records

    @classmethod
    def _merge_records(
        cls,
        target_list: List[ExperimentRecord],
        new_records: List[ExperimentRecord],
        seen_keys: Set[str],
        filter_failed: bool,
    ) -> None:
        """Helper to merge records with deduplication and quality filters."""
        for rec in new_records:
            # Generate deduplication fingerprint: (problem_id or type, solver_name, seed or timestamp)
            dedup_key = f"{rec.problem_type.value}_{rec.solver_name}_{rec.objective_value}_{rec.runtime_seconds:.3f}"
            if dedup_key in seen_keys:
                continue

            if filter_failed and (rec.status in ["FAILED", "CANCELLED"] or not rec.is_valid_for_training):
                continue

            seen_keys.add(dedup_key)
            target_list.append(rec)

    @classmethod
    async def _fetch_classical_executions(cls) -> List[ExperimentRecord]:
        """Fetch classical solver runs from 'executions' store."""
        records: List[ExperimentRecord] = []
        items = cls._get_collection_items("executions")

        for item in items:
            try:
                status = item.get("status", "UNKNOWN")
                res = item.get("result") or {}
                prob_type_str = item.get("problem_type")
                if not prob_type_str:
                    continue

                prob_type = ProblemType(prob_type_str)
                config = item.get("config") or {}

                is_failed = status in ["FAILED", "CANCELLED"]
                rec = ExperimentRecord(
                    record_id=item.get("execution_id") or str(item.get("_id", "unknown")),
                    provenance_collection="executions",
                    problem_id=item.get("problem_id"),
                    problem_type=prob_type,
                    instance_data=item.get("instance") or {},
                    solver_name=item.get("solver_name", "classical_solver"),
                    solver_category="classical",
                    solver_config=config,
                    status=status,
                    is_feasible=res.get("is_feasible", True),
                    objective_value=res.get("objective_value"),
                    runtime_seconds=float(res.get("runtime_seconds") or 0.0),
                    evaluation_count=int(res.get("extra_metadata", {}).get("evaluation_count", 0)),
                    random_seed=config.get("random_seed"),
                    timestamp=cls._parse_datetime(item.get("created_at")),
                    is_valid_for_training=not is_failed,
                    exclusion_reason="Execution failed" if is_failed else None,
                )
                records.append(rec)
            except Exception as e:
                logger.warning(f"Skipping malformed classical execution record: {e}")
        return records

    @classmethod
    async def _fetch_quantum_executions(cls) -> List[ExperimentRecord]:
        """Fetch standard QAOA runs from 'quantum_executions' store."""
        records: List[ExperimentRecord] = []
        items = cls._get_collection_items("quantum_executions")

        for item in items:
            try:
                status = item.get("status", "UNKNOWN")
                res = item.get("result") or {}
                prob_type_str = item.get("problem_type")
                if not prob_type_str:
                    continue

                prob_type = ProblemType(prob_type_str)
                config = item.get("config") or {}
                is_failed = status in ["FAILED", "CANCELLED"]

                rec = ExperimentRecord(
                    record_id=item.get("execution_id") or str(item.get("_id", "unknown")),
                    provenance_collection="quantum_executions",
                    problem_id=item.get("problem_id"),
                    problem_type=prob_type,
                    instance_data=item.get("instance") or {},
                    solver_name="standard_qaoa",
                    solver_category="quantum_simulator",
                    solver_config=config,
                    status=status,
                    is_feasible=res.get("best_solution", {}).get("is_feasible", True) if res.get("best_solution") else True,
                    objective_value=res.get("best_solution", {}).get("objective_value") if res.get("best_solution") else None,
                    runtime_seconds=float(res.get("runtime_seconds") or 0.0),
                    evaluation_count=int(len(res.get("convergence_history") or [])),
                    circuit_metadata=res.get("circuit_metadata"),
                    random_seed=config.get("seed"),
                    timestamp=cls._parse_datetime(item.get("submitted_at")),
                    is_valid_for_training=not is_failed,
                    exclusion_reason="Execution failed" if is_failed else None,
                )
                records.append(rec)
            except Exception as e:
                logger.warning(f"Skipping malformed quantum execution record: {e}")
        return records

    @classmethod
    async def _fetch_adaptive_executions(cls) -> List[ExperimentRecord]:
        """Fetch adaptive QAOA runs from 'adaptive_executions' store."""
        records: List[ExperimentRecord] = []
        items = cls._get_collection_items("adaptive_executions")

        for item in items:
            try:
                status = item.get("status", "UNKNOWN")
                res = item.get("result") or {}
                prob_type_str = item.get("problem_type")
                if not prob_type_str:
                    continue

                prob_type = ProblemType(prob_type_str)
                config = item.get("config") or {}
                is_failed = status in ["FAILED", "CANCELLED"]

                rec = ExperimentRecord(
                    record_id=item.get("execution_id") or str(item.get("_id", "unknown")),
                    provenance_collection="adaptive_executions",
                    problem_id=item.get("problem_id"),
                    problem_type=prob_type,
                    instance_data=item.get("instance") or {},
                    solver_name="adaptive_qaoa",
                    solver_category="quantum_simulator",
                    solver_config=config,
                    status=status,
                    is_feasible=res.get("is_feasible", True),
                    objective_value=res.get("objective_value"),
                    runtime_seconds=float(res.get("execution_time_ms", 0.0)) / 1000.0,
                    evaluation_count=int(res.get("total_evaluations", 0)),
                    circuit_metadata=res.get("circuit_metadata"),
                    random_seed=config.get("seed"),
                    timestamp=cls._parse_datetime(item.get("submitted_at")),
                    is_valid_for_training=not is_failed,
                    exclusion_reason="Execution failed" if is_failed else None,
                )
                records.append(rec)
            except Exception as e:
                logger.warning(f"Skipping malformed adaptive execution record: {e}")
        return records

    @classmethod
    async def _fetch_benchmark_trials(cls) -> List[ExperimentRecord]:
        """Extract individual solver trials from classical, hybrid, and adaptive benchmarks."""
        records: List[ExperimentRecord] = []

        # 1. Classical benchmarks
        bench_items = cls._get_collection_items("benchmarks")
        for bench in bench_items:
            prob_type_str = bench.get("problem_type")
            if not prob_type_str:
                continue
            prob_type = ProblemType(prob_type_str)
            trials = bench.get("trials") or []

            for t in trials:
                try:
                    rec = ExperimentRecord(
                        record_id=f"bench_trial_{bench.get('benchmark_id')}_{t.get('solver_name')}_{t.get('trial_index', 0)}",
                        provenance_collection="benchmarks",
                        problem_id=bench.get("problem_id"),
                        problem_type=prob_type,
                        instance_data={},
                        solver_name=t.get("solver_name", "classical_solver"),
                        solver_category="classical",
                        solver_config={},
                        status="COMPLETED",
                        is_feasible=t.get("is_feasible", True),
                        objective_value=t.get("objective_value"),
                        runtime_seconds=float(t.get("runtime_seconds") or 0.0),
                        evaluation_count=int(t.get("evaluations", 0)),
                        random_seed=t.get("trial_seed"),
                        timestamp=cls._parse_datetime(bench.get("created_at")),
                        is_valid_for_training=True,
                    )
                    records.append(rec)
                except Exception as e:
                    logger.debug(f"Skipping benchmark trial: {e}")

        # 2. Hybrid benchmarks
        hybrid_items = cls._get_collection_items("hybrid_benchmarks")
        for h in hybrid_items:
            prob_type_str = h.get("problem_type")
            if not prob_type_str:
                continue
            prob_type = ProblemType(prob_type_str)
            summaries = h.get("summaries") or []

            for s in summaries:
                try:
                    s_name = s.get("solver_id") or s.get("solver_name")
                    rec = ExperimentRecord(
                        record_id=f"hybrid_summary_{h.get('benchmark_id')}_{s_name}",
                        provenance_collection="hybrid_benchmarks",
                        problem_id=h.get("problem_id"),
                        problem_type=prob_type,
                        instance_data={},
                        solver_name=s_name,
                        solver_category=s.get("solver_category", "classical"),
                        solver_config={},
                        status="COMPLETED",
                        is_feasible=s.get("feasibility_rate", 1.0) > 0.5,
                        objective_value=s.get("best_objective"),
                        runtime_seconds=float(s.get("mean_runtime_ms", 0.0)) / 1000.0,
                        evaluation_count=int(s.get("mean_evaluations", 0)),
                        circuit_metadata=s.get("circuit_metadata"),
                        timestamp=cls._parse_datetime(h.get("created_at")),
                        is_valid_for_training=True,
                    )
                    records.append(rec)
                except Exception as e:
                    logger.debug(f"Skipping hybrid summary trial: {e}")

        return records

    @staticmethod
    def _get_collection_items(collection: str) -> List[Dict[str, Any]]:
        """Retrieve items from MongoDB or local memory fallback."""
        return db_manager.memory_list(collection)

    @staticmethod
    def _parse_datetime(val: Any) -> datetime:
        """Parse datetime safely or return current UTC time."""
        if isinstance(val, datetime):
            return val
        if isinstance(val, str):
            try:
                return datetime.fromisoformat(val)
            except ValueError:
                pass
        return datetime.now(timezone.utc)
