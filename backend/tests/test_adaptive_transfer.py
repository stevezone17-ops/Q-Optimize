"""Unit tests for Stage 6.3: Adaptive QAOA Parameter Transfer & Warm Starts."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.solvers.quantum.adaptive.transfer import (
    ParameterTransferService,
    TransferCompatibilityReport,
    TransferParametersRequest,
    TransferParametersResponse,
)
from backend.app.solvers.quantum.adaptive.adaptive_exceptions import (
    IncompatibleTransferError,
    IncompatibleWarmStartError,
)
from backend.app.db.mongodb import db_manager

client = TestClient(app)


def test_transfer_compatibility_same_depth():
    """Verify same-depth compatibility check yields direct copy recommendation."""
    report = ParameterTransferService.check_compatibility(
        source_gamma=[0.1, 0.2],
        source_beta=[0.3, 0.4],
        target_depth=2,
    )
    assert report.is_compatible is True
    assert report.source_depth == 2
    assert report.target_depth == 2
    assert report.compatibility_score == 1.0
    assert report.recommended_method == "direct_copy"


def test_transfer_compatibility_depth_expansion():
    """Verify depth expansion yields high compatibility and linear interpolation recommendation."""
    report = ParameterTransferService.check_compatibility(
        source_gamma=[0.1, 0.2],
        source_beta=[0.3, 0.4],
        target_depth=4,
    )
    assert report.is_compatible is True
    assert report.source_depth == 2
    assert report.target_depth == 4
    assert report.compatibility_score >= 0.7
    assert report.recommended_method == "linear_interpolation"


def test_transfer_compatibility_incompatible_cases():
    """Verify dimension mismatches and out-of-bound depths are rejected."""
    # Length mismatch
    rep1 = ParameterTransferService.check_compatibility(
        source_gamma=[0.1, 0.2],
        source_beta=[0.3],
        target_depth=2,
    )
    assert rep1.is_compatible is False

    # Out-of-bounds depth
    rep2 = ParameterTransferService.check_compatibility(
        source_gamma=[0.1],
        source_beta=[0.1],
        target_depth=15,
    )
    assert rep2.is_compatible is False

    # Problem type conflict
    rep3 = ParameterTransferService.check_compatibility(
        source_gamma=[0.1],
        source_beta=[0.1],
        target_depth=1,
        source_problem_type="max_cut",
        target_problem_type="tsp",
    )
    assert rep3.is_compatible is False
    assert "Problem type mismatch" in rep3.notes[0]


def test_transfer_parameters_methods():
    """Verify linear interpolation, adiabatic extension, and layer padding."""
    gamma = [0.2, 0.8]
    beta = [0.7, 0.1]

    # Linear interpolation
    g_interp, b_interp, rep_interp = ParameterTransferService.transfer_parameters(
        source_gamma=gamma,
        source_beta=beta,
        target_depth=4,
        method="linear_interpolation",
    )
    assert len(g_interp) == 4
    assert len(b_interp) == 4
    assert g_interp[0] == pytest.approx(0.2)
    assert g_interp[-1] == pytest.approx(0.8)

    # Adiabatic extension
    g_ext, b_ext, _ = ParameterTransferService.transfer_parameters(
        source_gamma=gamma,
        source_beta=beta,
        target_depth=4,
        method="adiabatic_extension",
    )
    assert len(g_ext) == 4
    assert len(b_ext) == 4
    assert g_ext[0] == 0.2 and g_ext[1] == 0.8

    # Layer padding
    g_pad, b_pad, _ = ParameterTransferService.transfer_parameters(
        source_gamma=gamma,
        source_beta=beta,
        target_depth=4,
        method="layer_padding",
    )
    assert len(g_pad) == 4
    assert g_pad == [0.2, 0.8, 0.8, 0.8]
    assert b_pad == [0.7, 0.1, 0.1, 0.1]


@pytest.mark.asyncio
async def test_transfer_from_prior_execution():
    """Verify loading and transferring parameters from a stored execution record."""
    exec_id = "test-prior-qexec-1"
    mock_record = {
        "execution_id": exec_id,
        "problem_type": "max_cut",
        "result": {
            "optimal_gamma": [0.35, 0.65],
            "optimal_beta": [0.85, 0.25],
        }
    }
    db_manager.memory_insert("quantum_executions", exec_id, mock_record)

    g, b, rep = await ParameterTransferService.transfer_from_execution(
        execution_id=exec_id,
        target_depth=3,
        target_problem_type="max_cut",
    )
    assert len(g) == 3
    assert len(b) == 3
    assert rep.is_compatible is True

    # Missing execution raises error
    with pytest.raises(IncompatibleWarmStartError):
        await ParameterTransferService.transfer_from_execution(
            execution_id="nonexistent-exec-id",
            target_depth=3,
        )


def test_api_transfer_check_and_parameters():
    """Verify REST endpoints /transfer/check and /transfer/parameters."""
    # Check
    check_payload = {
        "source_gamma": [0.1, 0.5],
        "source_beta": [0.8, 0.2],
        "target_depth": 3,
        "transfer_method": "linear_interpolation",
    }
    res_chk = client.post("/api/v1/solvers/quantum/adaptive/transfer/check", json=check_payload)
    assert res_chk.status_code == 200
    chk_data = res_chk.json()
    assert chk_data["is_compatible"] is True
    assert chk_data["target_depth"] == 3

    # Transfer
    res_tr = client.post("/api/v1/solvers/quantum/adaptive/transfer/parameters", json=check_payload)
    assert res_tr.status_code == 200
    tr_data = res_tr.json()
    assert len(tr_data["transferred_gamma"]) == 3
    assert len(tr_data["transferred_beta"]) == 3
    assert tr_data["target_depth"] == 3

    # Incompatible problem types
    bad_payload = dict(check_payload)
    bad_payload["source_problem_type"] = "max_cut"
    bad_payload["target_problem_type"] = "tsp"
    res_bad = client.post("/api/v1/solvers/quantum/adaptive/transfer/parameters", json=bad_payload)
    assert res_bad.status_code == 400
