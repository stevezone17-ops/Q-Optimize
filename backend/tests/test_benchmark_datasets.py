"""Tests for Stage 8.3 — Benchmark Datasets and Problem Instance Generators."""

import pytest

from backend.app.experiments.dataset_manager import BenchmarkDatasetManager, _fingerprint
from backend.app.experiments.generators.max_cut_generator import (
    generate_erdos_renyi,
    generate_random_regular,
)
from backend.app.experiments.generators.assignment_generator import generate_random_assignment
from backend.app.experiments.generators.tsp_generator import (
    generate_euclidean_tsp,
    generate_random_tsp,
)
from backend.app.experiments.experiment_exceptions import DatasetNotFoundError


class TestMaxCutGenerator:
    def test_erdos_renyi_produces_valid_edges(self):
        inst = generate_erdos_renyi(num_nodes=6, edge_probability=0.5, seed=42)
        assert inst["num_nodes"] == 6
        for edge in inst["edge_list"]:
            u, v = edge[0], edge[1]
            assert 0 <= u < 6
            assert 0 <= v < 6
            assert u != v

    def test_erdos_renyi_seed_reproducibility(self):
        a = generate_erdos_renyi(num_nodes=8, edge_probability=0.4, seed=99)
        b = generate_erdos_renyi(num_nodes=8, edge_probability=0.4, seed=99)
        assert a["edge_list"] == b["edge_list"]

    def test_erdos_renyi_different_seeds_differ(self):
        a = generate_erdos_renyi(num_nodes=8, edge_probability=0.5, seed=1)
        b = generate_erdos_renyi(num_nodes=8, edge_probability=0.5, seed=2)
        assert a["edge_list"] != b["edge_list"]

    def test_random_regular_produces_valid_graph(self):
        inst = generate_random_regular(num_nodes=6, degree=2, seed=42)
        assert inst["num_nodes"] == 6
        assert len(inst["edge_list"]) == (6 * 2) // 2

    def test_random_regular_seed_reproducibility(self):
        a = generate_random_regular(num_nodes=6, degree=2, seed=7)
        b = generate_random_regular(num_nodes=6, degree=2, seed=7)
        assert a["edge_list"] == b["edge_list"]


class TestAssignmentGenerator:
    def test_generates_correct_matrix_shape(self):
        inst = generate_random_assignment(num_agents=3, num_tasks=4, seed=42)
        matrix = inst["cost_matrix"]
        assert len(matrix) == 3
        assert len(matrix[0]) == 4

    def test_seed_reproducibility(self):
        a = generate_random_assignment(num_agents=4, num_tasks=4, seed=55)
        b = generate_random_assignment(num_agents=4, num_tasks=4, seed=55)
        assert a["cost_matrix"] == b["cost_matrix"]

    def test_integer_distribution(self):
        inst = generate_random_assignment(num_agents=3, num_tasks=3, cost_distribution="integer", cost_low=1.0, cost_high=10.0, seed=1)
        for row in inst["cost_matrix"]:
            for val in row:
                assert val == int(val)

    def test_invalid_distribution_raises(self):
        with pytest.raises(ValueError):
            generate_random_assignment(num_agents=3, num_tasks=3, cost_distribution="invalid")


class TestTSPGenerator:
    def test_euclidean_produces_symmetric_matrix(self):
        inst = generate_euclidean_tsp(num_cities=5, seed=42)
        m = inst["distance_matrix"]
        for i in range(5):
            assert m[i][i] == 0.0
            for j in range(5):
                assert abs(m[i][j] - m[j][i]) < 1e-6

    def test_euclidean_seed_reproducibility(self):
        a = generate_euclidean_tsp(num_cities=4, seed=100)
        b = generate_euclidean_tsp(num_cities=4, seed=100)
        assert a["distance_matrix"] == b["distance_matrix"]

    def test_random_tsp_symmetric(self):
        inst = generate_random_tsp(num_cities=5, seed=42)
        m = inst["distance_matrix"]
        for i in range(5):
            assert m[i][i] == 0.0


class TestDatasetManager:
    def test_generate_and_retrieve_max_cut_dataset(self):
        mgr = BenchmarkDatasetManager()
        ds = mgr.generate_max_cut_erdos_renyi(num_nodes=4, num_instances=2, base_seed=42)
        assert ds.metadata.num_instances == 2
        assert len(ds.instances) == 2

    def test_fingerprint_stable_for_same_seed(self):
        mgr = BenchmarkDatasetManager()
        ds1 = mgr.generate_max_cut_erdos_renyi(num_nodes=4, num_instances=1, base_seed=42)
        ds2 = mgr.generate_max_cut_erdos_renyi(num_nodes=4, num_instances=1, base_seed=42)
        assert ds1.instances[0].fingerprint == ds2.instances[0].fingerprint

    def test_fingerprint_differs_for_different_seeds(self):
        mgr = BenchmarkDatasetManager()
        ds1 = mgr.generate_max_cut_erdos_renyi(num_nodes=4, num_instances=1, base_seed=1)
        ds2 = mgr.generate_max_cut_erdos_renyi(num_nodes=4, num_instances=1, base_seed=2)
        assert ds1.instances[0].fingerprint != ds2.instances[0].fingerprint

    def test_save_and_retrieve_dataset(self):
        mgr = BenchmarkDatasetManager()
        ds = mgr.generate_assignment_dataset(num_agents=3, num_tasks=3, base_seed=1)
        retrieved = mgr.get(ds.metadata.dataset_id)
        assert retrieved.metadata.dataset_id == ds.metadata.dataset_id

    def test_get_nonexistent_dataset_raises(self):
        mgr = BenchmarkDatasetManager()
        with pytest.raises(DatasetNotFoundError):
            mgr.get("no-such-dataset")

    def test_list_datasets_includes_generated(self):
        mgr = BenchmarkDatasetManager()
        ds = mgr.generate_tsp_euclidean(num_cities=3, num_instances=1, base_seed=7)
        all_ds = mgr.list_datasets()
        ids = [d.metadata.dataset_id for d in all_ds]
        assert ds.metadata.dataset_id in ids

    def test_delete_dataset(self):
        mgr = BenchmarkDatasetManager()
        ds = mgr.generate_tsp_random(num_cities=3, num_instances=1)
        result = mgr.delete(ds.metadata.dataset_id)
        assert result is True
        with pytest.raises(DatasetNotFoundError):
            mgr.get(ds.metadata.dataset_id)

    def test_fingerprint_function(self):
        data = {"num_nodes": 4, "edge_list": [[0, 1], [2, 3]]}
        fp1 = _fingerprint(data)
        fp2 = _fingerprint(data)
        assert fp1 == fp2
        assert len(fp1) == 64  # sha256 hex
