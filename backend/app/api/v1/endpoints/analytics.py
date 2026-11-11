"""Analytics and algorithm comparison REST endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from backend.app.experiments.analytics import (
    ComparisonAnalysisResponse,
    ScalabilityDataPoint,
    comparison_engine,
)
from backend.app.experiments.registry import experiment_registry
from backend.app.experiments.experiment_exceptions import ExperimentNotFoundError

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/experiments/{experiment_id}/compare", response_model=ComparisonAnalysisResponse)
async def compare_experiment_algorithms(
    experiment_id: str,
    optimal_value: Optional[float] = Query(default=None),
    direction: str = Query(default="max"),
) -> ComparisonAnalysisResponse:
    """Perform multi-algorithm comparative analytics on a completed experiment."""
    try:
        return comparison_engine.analyze_experiment(
            experiment_id=experiment_id,
            optimal_value=optimal_value,
            objective_direction=direction,
        )
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/scalability", response_model=List[ScalabilityDataPoint])
async def get_scalability_series(
    problem_type: Optional[str] = Query(default=None),
) -> List[ScalabilityDataPoint]:
    """Retrieve scalability metrics aggregated across completed experiments."""
    all_experiments = experiment_registry.list_all(page=1, page_size=100)
    filtered = [
        e for e in all_experiments
        if e.results and (not problem_type or e.configuration.problem_type == problem_type)
    ]
    return comparison_engine.compute_scalability_series(filtered)
