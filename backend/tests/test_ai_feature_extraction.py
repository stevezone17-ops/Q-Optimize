"""Unit tests for Stage 7.2: Optimization Feature Engineering."""

import pytest
import numpy as np

from backend.app.domain.problems.models import ProblemType
from backend.app.ai.feature_extraction import OptimizationFeatureExtractor
from backend.app.ai.exceptions import FeatureExtractionError


@pytest.fixture
def extractor() -> OptimizationFeatureExtractor:
    return OptimizationFeatureExtractor()


def test_max_cut_feature_extraction(extractor: OptimizationFeatureExtractor):
    """Test feature extraction on a weighted graph instance."""
    instance = {
        "nodes": ["A", "B", "C", "D"],
        "edges": [
            ["A", "B", 1.5],
            ["B", "C", 2.0],
            ["C", "D", 2.5],
            ["D", "A", 3.0],
            ["A", "C", 1.0],
        ],
    }

    features = extractor.extract_features(ProblemType.MAX_CUT, instance)

    assert features.problem_type == ProblemType.MAX_CUT
    assert features.num_vertices == 4
    assert features.num_edges == 5
    assert features.num_variables == 4
    assert features.num_constraints == 0
    # Density: 5 / (4*3/2) = 5 / 6 = 0.8333
    assert features.graph_density == pytest.approx(5.0 / 6.0, rel=1e-3)
    assert features.num_connected_components == 1
    assert features.coeff_min == 1.0
    assert features.coeff_max == 3.0
    assert features.coeff_range == 2.0
    assert features.estimated_search_space_log2 == 4.0
    assert features.required_qubits == 4

    # Check vector export
    vec = features.to_feature_vector()
    assert len(vec) == 18
    assert all(isinstance(x, float) for x in vec)


def test_max_cut_disconnected_graph(extractor: OptimizationFeatureExtractor):
    """Test connected components detection on disconnected graph."""
    instance = {
        "nodes": ["A", "B", "C", "D"],
        "edges": [
            ["A", "B", 1.0],
            ["C", "D", 2.0],
        ],
    }
    features = extractor.extract_features(ProblemType.MAX_CUT, instance)
    assert features.num_connected_components == 2
    assert features.min_degree == 1
    assert features.max_degree == 1


def test_assignment_feature_extraction(extractor: OptimizationFeatureExtractor):
    """Test feature extraction on linear assignment problem."""
    instance = {
        "agents": ["A1", "A2", "A3"],
        "tasks": ["T1", "T2", "T3"],
        "cost_matrix": [
            [4.0, 7.0, 2.0],
            [3.0, 8.0, 6.0],
            [5.0, 1.0, 9.0],
        ],
    }

    features = extractor.extract_features(ProblemType.ASSIGNMENT, instance)

    assert features.problem_type == ProblemType.ASSIGNMENT
    assert features.num_agents == 3
    assert features.num_tasks == 3
    assert features.is_square_matrix is True
    assert features.num_variables == 9  # 3x3 binary variables
    assert features.num_constraints == 6  # 3 rows + 3 cols
    assert features.coeff_min == 1.0
    assert features.coeff_max == 9.0
    assert features.coeff_range == 8.0
    # Search space: log2(3!) = log2(6) ≈ 2.585
    assert features.estimated_search_space_log2 == pytest.approx(2.585, rel=1e-2)
    assert features.required_qubits == 9


def test_tsp_feature_extraction(extractor: OptimizationFeatureExtractor):
    """Test feature extraction on TSP instance."""
    # 4 cities metric symmetric distance matrix satisfying triangle inequality
    instance = {
        "cities": ["C0", "C1", "C2", "C3"],
        "distance_matrix": [
            [0.0, 10.0, 15.0, 20.0],
            [10.0, 0.0, 20.0, 25.0],
            [15.0, 20.0, 0.0, 10.0],
            [20.0, 25.0, 10.0, 0.0],
        ],
    }

    features = extractor.extract_features(ProblemType.TSP, instance)

    assert features.problem_type == ProblemType.TSP
    assert features.num_cities == 4
    assert features.num_variables == 16  # 4x4
    assert features.num_constraints == 8  # 2n
    assert features.is_symmetric_distance is True
    assert features.satisfies_triangle_inequality is True
    assert features.coeff_min == 10.0
    assert features.coeff_max == 25.0
    # Search space: log2((4-1)! / 2) = log2(3) ≈ 1.585
    assert features.estimated_search_space_log2 == pytest.approx(1.585, rel=1e-2)
    assert features.required_qubits == 16


def test_feature_determinism(extractor: OptimizationFeatureExtractor):
    """Verify feature extraction is strictly deterministic across multiple invocations."""
    instance = {
        "nodes": ["V1", "V2", "V3", "V4", "V5"],
        "edges": [
            ["V1", "V2", 2.2],
            ["V2", "V3", 3.3],
            ["V3", "V4", 1.1],
            ["V4", "V5", 4.4],
            ["V5", "V1", 5.5],
        ],
    }

    f1 = extractor.extract_features(ProblemType.MAX_CUT, instance)
    f2 = extractor.extract_features(ProblemType.MAX_CUT, instance)

    v1 = f1.to_feature_vector()
    v2 = f2.to_feature_vector()

    assert v1 == v2
    assert f1.model_dump() == f2.model_dump()


def test_unsupported_problem_type_raises(extractor: OptimizationFeatureExtractor):
    """Verify invalid problem types trigger FeatureExtractionError."""
    with pytest.raises(FeatureExtractionError):
        extractor.extract_features("unknown_type", {})
