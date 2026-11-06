"""Unit tests for Stage 7.6: Natural Language Optimization Assistant."""

import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.domain.problems.models import ProblemType
from backend.app.ai.natural_language.assistant import NaturalLanguageAssistant
from backend.app.ai.natural_language.provider import (
    DeterministicFallbackParser,
    MockLLMProvider,
)
from backend.app.ai.registry import AIServiceRegistry


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def assistant() -> NaturalLanguageAssistant:
    return NaturalLanguageAssistant()


@pytest.mark.asyncio
async def test_assistant_tsp_intent_and_extraction(assistant: NaturalLanguageAssistant):
    """Test TSP parsing from delivery route description."""
    text = "I have five delivery locations and want to find the shortest possible route starting and ending at the warehouse."
    draft = await assistant.parse_problem_description(text)

    assert draft.is_supported is True
    assert draft.problem_type == ProblemType.TSP
    assert len(draft.suggested_instance.get("cities", [])) >= 3
    assert "distance_matrix" in draft.suggested_instance
    assert draft.requires_user_confirmation is True
    assert draft.is_mathematically_valid is True
    assert draft.validation_status.lower() == "valid"
    assert len(draft.missing_information) >= 1  # Missing explicit distance values


@pytest.mark.asyncio
async def test_assistant_assignment_intent_and_extraction(assistant: NaturalLanguageAssistant):
    """Test Assignment problem parsing from worker allocation description."""
    text = "Please assign 4 workers to 4 jobs to minimize the total completion cost."
    draft = await assistant.parse_problem_description(text)

    assert draft.is_supported is True
    assert draft.problem_type == ProblemType.ASSIGNMENT
    assert len(draft.suggested_instance.get("agents", [])) == 4
    assert len(draft.suggested_instance.get("tasks", [])) == 4
    assert "cost_matrix" in draft.suggested_instance
    assert draft.is_mathematically_valid is True
    assert draft.validation_status.lower() == "valid"


@pytest.mark.asyncio
async def test_assistant_max_cut_intent_and_extraction(assistant: NaturalLanguageAssistant):
    """Test Max-Cut graph partitioning description."""
    text = "Partition a network of 4 vertices into two disjoint sets to maximize the total weight of edges crossing between them."
    draft = await assistant.parse_problem_description(text)

    assert draft.is_supported is True
    assert draft.problem_type == ProblemType.MAX_CUT
    assert len(draft.suggested_instance.get("nodes", [])) == 4
    assert len(draft.suggested_instance.get("edges", [])) >= 3
    assert draft.is_mathematically_valid is True
    assert draft.validation_status.lower() == "valid"


@pytest.mark.asyncio
async def test_assistant_unsupported_problem_handling(assistant: NaturalLanguageAssistant):
    """Test unsupported problem description is gracefully flagged rather than misclassified."""
    text = "Please write a quicksort algorithm in python to sort an array of numbers."
    draft = await assistant.parse_problem_description(text)

    assert draft.is_supported is False
    assert draft.problem_type is None
    assert len(draft.missing_information) >= 1
    assert "supported families" in draft.missing_information[0].lower()


@pytest.mark.asyncio
async def test_mock_llm_provider_integration():
    """Verify custom mock LLM provider works with assistant."""
    mock_resp = {
        "is_supported": True,
        "problem_type": ProblemType.MAX_CUT,
        "title": "Mocked MaxCut",
        "description": "Mocked graph cut",
        "entities": {"nodes": ["N1", "N2", "N3"]},
        "objective": {"direction": "maximize", "description": "max cut"},
        "constraints": ["binary partition"],
        "missing_information": [],
        "assumptions": ["unit weights"],
        "suggested_instance": {
            "nodes": ["N1", "N2", "N3"],
            "edges": [["N1", "N2", 1.0], ["N2", "N3", 2.0]],
        },
        "confidence_score": 0.99,
    }

    mock_prov = MockLLMProvider(mock_resp)
    AIServiceRegistry.register_llm_provider("mock_test", mock_prov)

    assistant = NaturalLanguageAssistant(default_provider=mock_prov)
    draft = await assistant.parse_problem_description("any text here", provider_name="mock_test")

    assert draft.name == "Mocked MaxCut"
    assert draft.problem_type == ProblemType.MAX_CUT
    assert draft.is_mathematically_valid is True


def test_api_assistant_parse_endpoint(client: TestClient):
    """Verify REST POST /api/v1/ai/assistant/parse endpoint."""
    payload = {
        "text": "I have four delivery locations and want to find the shortest round trip route.",
    }

    resp = client.post("/api/v1/ai/assistant/parse", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["is_supported"] is True
    assert data["problem_type"] == "tsp"
    assert data["requires_user_confirmation"] is True
    assert data["is_mathematically_valid"] is True
    assert "suggested_instance" in data


def test_api_assistant_validate_draft_endpoint(client: TestClient):
    """Verify REST POST /api/v1/ai/assistant/validate-draft endpoint."""
    payload = {
        "problem_type": "assignment",
        "instance": {
            "agents": ["A1", "A2"],
            "tasks": ["T1", "T2"],
            "cost_matrix": [[5.0, 2.0], [3.0, 8.0]],
        },
    }

    resp = client.post("/api/v1/ai/assistant/validate-draft", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["is_valid"] is True
    assert data["status"].lower() == "valid"
    assert data["num_variables"] >= 1
    assert data["num_constraints"] >= 1
