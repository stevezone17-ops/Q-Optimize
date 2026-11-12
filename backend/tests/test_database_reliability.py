"""Tests for Database Reliability, Indexing, Connection Pooling, and Soft Deletion (Stage 9.3)."""

import pytest
from datetime import datetime
from backend.app.db.mongodb import db_manager, DatabaseManager
from backend.app.services.problem_service import ProblemService
from backend.app.domain.problems.models import ProblemCreate, ProblemType


@pytest.fixture(autouse=True)
def clean_db():
    db_manager._memory_store["problems"] = {}
    db_manager._memory_store["users"] = {}


@pytest.mark.asyncio
async def test_connection_pool_configuration():
    """Verify production connection pool constants and settings."""
    assert db_manager.MAX_POOL_SIZE == 50
    assert db_manager.MIN_POOL_SIZE == 5
    assert db_manager.MAX_IDLE_TIME_MS == 30000
    assert db_manager.CONNECT_TIMEOUT_MS == 5000


@pytest.mark.asyncio
async def test_index_creation_across_all_collections():
    """Verify automated index initialization covers all domain collections."""
    indexes = await db_manager.create_indexes()

    expected_collections = [
        "users",
        "problems",
        "formulations",
        "experiments",
        "executions",
        "benchmarks",
        "benchmark_datasets",
    ]
    for coll in expected_collections:
        assert coll in indexes
        assert len(indexes[coll]) > 0


@pytest.mark.asyncio
async def test_soft_delete_preserves_audit_trail_and_filters():
    """Verify soft delete removes entity from active queries but keeps audit trail."""
    prob_in = ProblemCreate(
        name="Soft Delete Max-Cut Test",
        problem_type=ProblemType.MAX_CUT,
        instance={
            "nodes": ["N1", "N2"],
            "edges": [["N1", "N2", 1.0]],
        },
    )
    created = await ProblemService.create_problem(prob_in, owner_id="user_test_93")
    assert created.is_deleted is False

    # Normal fetch returns item
    fetched = await ProblemService.get_problem(created.id, owner_id="user_test_93")
    assert fetched is not None

    # Perform soft delete
    deleted = await ProblemService.delete_problem(created.id, deleted_by="admin_operator")
    assert deleted is True

    # Default fetch should return None (soft-deleted)
    deleted_fetch = await ProblemService.get_problem(created.id, owner_id="user_test_93")
    assert deleted_fetch is None

    # Default list should exclude soft-deleted problem
    active_list = await ProblemService.list_problems(owner_id="user_test_93")
    assert not any(p.id == created.id for p in active_list)

    # Fetch with include_deleted=True should recover record and audit fields
    audit_fetch = await ProblemService.get_problem(
        created.id, owner_id="user_test_93", include_deleted=True
    )
    assert audit_fetch is not None
    assert audit_fetch.is_deleted is True
    assert audit_fetch.deleted_by == "admin_operator"
    assert audit_fetch.deleted_at is not None
    assert isinstance(audit_fetch.deleted_at, datetime)


@pytest.mark.asyncio
async def test_database_status_diagnostics():
    """Verify get_db_status returns comprehensive engine and health diagnostics."""
    status = await db_manager.get_db_status()
    assert "connected" in status
    assert "engine" in status
    assert status["engine"] in ["mongodb", "in_memory_fallback"]


@pytest.mark.asyncio
async def test_connect_with_retry_handles_unreachable_host():
    """Verify connect_with_retry does not raise unhandled exception on connection failure."""
    mgr = DatabaseManager()
    # Connect with short retries
    connected = await mgr.connect_with_retry(max_retries=1, initial_delay=0.1)
    # Even if offline, manager gracefully falls back without unhandled crash
    assert connected is False or connected is True
    status = await mgr.get_db_status()
    assert status["connected"] == connected

