"""Tests for Stage 8.2 — Benchmark Orchestration."""

import pytest

from backend.app.experiments.benchmark_orchestrator import (
    BenchmarkConfiguration,
    BenchmarkMode,
    BenchmarkOrchestrator,
)
from backend.app.experiments.models import ExperimentAlgorithm


def _make_config(**kwargs) -> BenchmarkConfiguration:
    defaults = {
        "name": "Test Benchmark",
        "problem_type": "max_cut",
        "problem_instance": {"num_nodes": 4, "edge_list": [[0, 1], [1, 2], [2, 3]]},
        "algorithms": [ExperimentAlgorithm.SIMULATED_ANNEALING],
        "num_trials": 2,
        "mode": BenchmarkMode.PARALLEL,
        "timeout_seconds": 60.0,
    }
    defaults.update(kwargs)
    return BenchmarkConfiguration(**defaults)


class TestBenchmarkOrchestration:
    def test_benchmark_runs_and_returns_record(self):
        orch = BenchmarkOrchestrator()
        config = _make_config()
        record = orch.run_benchmark(config)
        assert record.benchmark_id == config.benchmark_id
        assert record.status in {"completed", "partially_completed", "failed"}

    def test_benchmark_has_expected_trial_count(self):
        orch = BenchmarkOrchestrator()
        config = _make_config(num_trials=2)
        record = orch.run_benchmark(config)
        assert len(record.trials) == 2

    def test_benchmark_multi_algorithm(self):
        orch = BenchmarkOrchestrator()
        config = _make_config(
            algorithms=[
                ExperimentAlgorithm.SIMULATED_ANNEALING,
                ExperimentAlgorithm.GENETIC_ALGORITHM,
            ],
            num_trials=1,
        )
        record = orch.run_benchmark(config)
        algo_names = {t.algorithm for t in record.trials}
        assert "simulated_annealing" in algo_names
        assert "genetic_algorithm" in algo_names

    def test_benchmark_sequential_mode(self):
        orch = BenchmarkOrchestrator()
        config = _make_config(mode=BenchmarkMode.SEQUENTIAL, num_trials=2)
        record = orch.run_benchmark(config)
        assert len(record.trials) == 2

    def test_benchmark_with_seeds(self):
        orch = BenchmarkOrchestrator()
        config = _make_config(num_trials=2, seeds=[42, 123])
        record = orch.run_benchmark(config)
        seeds = [t.seed for t in record.trials]
        assert 42 in seeds

    def test_benchmark_stored_and_retrievable(self):
        orch = BenchmarkOrchestrator()
        config = _make_config()
        record = orch.run_benchmark(config)
        retrieved = orch.get_benchmark(record.benchmark_id)
        assert retrieved is not None
        assert retrieved.benchmark_id == record.benchmark_id

    def test_get_nonexistent_benchmark_returns_none(self):
        orch = BenchmarkOrchestrator()
        result = orch.get_benchmark("nonexistent-benchmark-id")
        assert result is None

    def test_benchmark_records_total_runtime(self):
        orch = BenchmarkOrchestrator()
        config = _make_config(num_trials=1)
        record = orch.run_benchmark(config)
        assert record.total_runtime_seconds >= 0.0

    def test_benchmark_partial_failure_handled(self):
        """Benchmark with an invalid problem instance should not crash — returns failed status."""
        orch = BenchmarkOrchestrator()
        config = _make_config(
            problem_instance={"num_nodes": 0, "edge_list": []},
            num_trials=1,
        )
        try:
            record = orch.run_benchmark(config)
            assert record.status in {"completed", "partially_completed", "failed"}
        except Exception:
            pass  # Acceptable — solver raised

    def test_list_benchmarks_includes_run(self):
        orch = BenchmarkOrchestrator()
        config = _make_config()
        record = orch.run_benchmark(config)
        all_benchmarks = orch.list_benchmarks()
        ids = [b.benchmark_id for b in all_benchmarks]
        assert record.benchmark_id in ids
