"""Adaptive QAOA parameter transfer and warm-starting service."""

from typing import Tuple, List, Optional, Dict, Any
import numpy as np
from pydantic import BaseModel, Field

from backend.app.solvers.quantum.adaptive.adaptive_exceptions import (
    IncompatibleTransferError,
    IncompatibleWarmStartError,
)
from backend.app.db.mongodb import db_manager


class TransferCompatibilityReport(BaseModel):
    """Evaluation report on parameter transfer feasibility."""
    is_compatible: bool
    source_depth: int
    target_depth: int
    compatibility_score: float = Field(..., ge=0.0, le=1.0)
    recommended_method: str
    notes: List[str] = Field(default_factory=list)


class TransferParametersRequest(BaseModel):
    """Payload to request parameter transfer."""
    source_execution_id: Optional[str] = None
    source_gamma: Optional[List[float]] = None
    source_beta: Optional[List[float]] = None
    target_depth: int = Field(..., ge=1, le=10)
    transfer_method: str = Field("linear_interpolation", description="linear_interpolation | adiabatic_extension | layer_padding")
    source_problem_type: Optional[str] = None
    target_problem_type: Optional[str] = None


class TransferParametersResponse(BaseModel):
    """Output containing transferred parameter vectors."""
    transferred_gamma: List[float]
    transferred_beta: List[float]
    target_depth: int
    method_used: str
    compatibility_report: TransferCompatibilityReport


class ParameterTransferService:
    """Service governing parameter transfer across QAOA circuit depths and instances."""

    @staticmethod
    def check_compatibility(
        source_gamma: List[float],
        source_beta: List[float],
        target_depth: int,
        source_problem_type: Optional[str] = None,
        target_problem_type: Optional[str] = None,
    ) -> TransferCompatibilityReport:
        """
        Evaluate compatibility between source parameters and target depth/problem.
        """
        notes: List[str] = []
        is_compatible = True
        score = 1.0

        if len(source_gamma) != len(source_beta):
            return TransferCompatibilityReport(
                is_compatible=False,
                source_depth=len(source_gamma),
                target_depth=target_depth,
                compatibility_score=0.0,
                recommended_method="none",
                notes=[f"Source gamma length ({len(source_gamma)}) does not match source beta length ({len(source_beta)})"]
            )

        source_depth = len(source_gamma)
        if source_depth == 0:
            return TransferCompatibilityReport(
                is_compatible=False,
                source_depth=0,
                target_depth=target_depth,
                compatibility_score=0.0,
                recommended_method="none",
                notes=["Source parameter vectors are empty."]
            )

        if target_depth < 1 or target_depth > 10:
            return TransferCompatibilityReport(
                is_compatible=False,
                source_depth=source_depth,
                target_depth=target_depth,
                compatibility_score=0.0,
                recommended_method="none",
                notes=[f"Target depth {target_depth} is out of allowable range [1, 10]."]
            )

        # Problem type compatibility check
        if source_problem_type and target_problem_type and source_problem_type != target_problem_type:
            is_compatible = False
            score = 0.0
            notes.append(
                f"Problem type mismatch: cannot transfer parameters from {source_problem_type} "
                f"to {target_problem_type}."
            )
            return TransferCompatibilityReport(
                is_compatible=False,
                source_depth=source_depth,
                target_depth=target_depth,
                compatibility_score=0.0,
                recommended_method="none",
                notes=notes,
            )

        if source_depth == target_depth:
            method = "direct_copy"
            notes.append(f"Direct same-depth parameter transfer at p={target_depth}.")
        elif target_depth > source_depth:
            method = "linear_interpolation"
            score = max(0.6, 1.0 - 0.08 * (target_depth - source_depth))
            notes.append(
                f"Depth expansion from p={source_depth} to p={target_depth} via continuous interpolation."
            )
        else:
            method = "truncation"
            score = max(0.5, 1.0 - 0.1 * (source_depth - target_depth))
            notes.append(
                f"Depth truncation from p={source_depth} to p={target_depth}."
            )

        return TransferCompatibilityReport(
            is_compatible=is_compatible,
            source_depth=source_depth,
            target_depth=target_depth,
            compatibility_score=score,
            recommended_method=method,
            notes=notes,
        )

    @classmethod
    def transfer_parameters(
        cls,
        source_gamma: List[float],
        source_beta: List[float],
        target_depth: int,
        method: str = "linear_interpolation",
        source_problem_type: Optional[str] = None,
        target_problem_type: Optional[str] = None,
    ) -> Tuple[List[float], List[float], TransferCompatibilityReport]:
        """
        Execute parameter transfer producing angle vectors (gamma, beta) for target depth.
        """
        report = cls.check_compatibility(
            source_gamma=source_gamma,
            source_beta=source_beta,
            target_depth=target_depth,
            source_problem_type=source_problem_type,
            target_problem_type=target_problem_type,
        )
        if not report.is_compatible:
            raise IncompatibleTransferError(
                f"Cannot transfer parameters: {'; '.join(report.notes)}"
            )

        source_depth = len(source_gamma)
        if source_depth == target_depth:
            return (
                [float(g) for g in source_gamma],
                [float(b) for b in source_beta],
                report,
            )

        # Depth expansion / contraction
        if method == "linear_interpolation" or (target_depth > source_depth and method not in ["adiabatic_extension", "layer_padding"]):
            x_old = np.linspace(0.0, 1.0, source_depth)
            x_new = np.linspace(0.0, 1.0, target_depth)
            new_gamma = np.interp(x_new, x_old, source_gamma).tolist()
            new_beta = np.interp(x_new, x_old, source_beta).tolist()
            return [float(g) for g in new_gamma], [float(b) for b in new_beta], report

        elif method == "adiabatic_extension":
            delta_p = target_depth - source_depth
            if delta_p > 0:
                # Extend following current trend
                d_gamma = (source_gamma[-1] - source_gamma[0]) / max(1, source_depth - 1) if source_depth > 1 else 0.1
                d_beta = (source_beta[-1] - source_beta[0]) / max(1, source_depth - 1) if source_depth > 1 else -0.1
                new_gamma = list(source_gamma)
                new_beta = list(source_beta)
                for step in range(1, delta_p + 1):
                    new_gamma.append(float(source_gamma[-1] + step * d_gamma))
                    new_beta.append(float(max(0.01, source_beta[-1] + step * d_beta)))
                return new_gamma, new_beta, report
            else:
                return [float(g) for g in source_gamma[:target_depth]], [float(b) for b in source_beta[:target_depth]], report

        elif method == "layer_padding":
            delta_p = target_depth - source_depth
            if delta_p > 0:
                new_gamma = list(source_gamma) + [float(source_gamma[-1])] * delta_p
                new_beta = list(source_beta) + [float(source_beta[-1])] * delta_p
                return new_gamma, new_beta, report
            else:
                return [float(g) for g in source_gamma[:target_depth]], [float(b) for b in source_beta[:target_depth]], report

        else:
            raise ValueError(f"Unknown transfer method: {method}")

    @classmethod
    async def transfer_from_execution(
        cls,
        execution_id: str,
        target_depth: int,
        method: str = "linear_interpolation",
        target_problem_type: Optional[str] = None,
    ) -> Tuple[List[float], List[float], TransferCompatibilityReport]:
        """
        Load optimal parameter vectors from prior execution and transfer to target depth.
        """
        # Look in memory or mongo
        record = db_manager.memory_get("quantum_executions", execution_id)
        if not record:
            record = db_manager.memory_get("adaptive_quantum_executions", execution_id)

        if not record and db_manager.is_connected and db_manager.db is not None:
            try:
                record = await db_manager.db["quantum_executions"].find_one({"execution_id": execution_id})
                if not record:
                    record = await db_manager.db["adaptive_quantum_executions"].find_one({"execution_id": execution_id})
            except Exception:
                pass

        if not record:
            raise IncompatibleWarmStartError(f"Prior execution '{execution_id}' was not found in storage.")

        source_gamma: List[float] = []
        source_beta: List[float] = []
        source_problem_type = None

        if isinstance(record, dict):
            source_problem_type = record.get("problem_type")
            res_dict = record.get("result") or record
            if "optimal_gamma" in res_dict and "optimal_beta" in res_dict:
                source_gamma = res_dict.get("optimal_gamma", [])
                source_beta = res_dict.get("optimal_beta", [])
            elif "best_gamma" in res_dict and "best_beta" in res_dict:
                source_gamma = res_dict.get("best_gamma", [])
                source_beta = res_dict.get("best_beta", [])

        if not source_gamma or not source_beta:
            raise IncompatibleWarmStartError(
                f"Execution '{execution_id}' does not contain valid optimized parameter angles (gamma/beta)."
            )

        return cls.transfer_parameters(
            source_gamma=source_gamma,
            source_beta=source_beta,
            target_depth=target_depth,
            method=method,
            source_problem_type=source_problem_type,
            target_problem_type=target_problem_type,
        )
