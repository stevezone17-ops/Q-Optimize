"""Dataset management REST endpoints — Stage 8.3 / 8.7."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.experiments.dataset_manager import dataset_manager
from backend.app.experiments.dataset_models import BenchmarkDataset
from backend.app.experiments.experiment_exceptions import DatasetNotFoundError

router = APIRouter(prefix="/datasets", tags=["Benchmark Datasets"])


class GenerateDatasetRequest(BaseModel):
    problem_type: str
    generator_type: str = "erdos_renyi"
    num_instances: int = Field(default=1, ge=1, le=50)
    base_seed: Optional[int] = 42
    name: str = "Synthetic Benchmark Dataset"
    params: Dict[str, Any] = Field(default_factory=dict)


@router.get("", response_model=List[BenchmarkDataset])
async def list_datasets() -> List[BenchmarkDataset]:
    """List all stored reproducible benchmark datasets."""
    return dataset_manager.list_datasets()


@router.get("/{dataset_id}", response_model=BenchmarkDataset)
async def get_dataset(dataset_id: str) -> BenchmarkDataset:
    """Retrieve benchmark dataset details and problem instances."""
    try:
        return dataset_manager.get(dataset_id)
    except DatasetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/generate", response_model=BenchmarkDataset, status_code=201)
async def generate_dataset(req: GenerateDatasetRequest) -> BenchmarkDataset:
    """Generate a reproducible benchmark dataset using synthetic generators."""
    try:
        p_type = req.problem_type.lower()
        if p_type == "max_cut":
            if req.generator_type == "random_regular":
                return dataset_manager.generate_max_cut_random_regular(
                    num_nodes=int(req.params.get("num_nodes", 6)),
                    degree=int(req.params.get("degree", 2)),
                    num_instances=req.num_instances,
                    base_seed=req.base_seed,
                    name=req.name,
                )
            else:
                return dataset_manager.generate_max_cut_erdos_renyi(
                    num_nodes=int(req.params.get("num_nodes", 6)),
                    edge_probability=float(req.params.get("edge_probability", 0.5)),
                    num_instances=req.num_instances,
                    base_seed=req.base_seed,
                    name=req.name,
                )
        elif p_type == "assignment":
            return dataset_manager.generate_assignment_dataset(
                num_agents=int(req.params.get("num_agents", 4)),
                num_tasks=int(req.params.get("num_tasks", 4)),
                cost_distribution=str(req.params.get("cost_distribution", "uniform")),
                num_instances=req.num_instances,
                base_seed=req.base_seed,
                name=req.name,
            )
        elif p_type == "tsp":
            if req.generator_type == "random":
                return dataset_manager.generate_tsp_random(
                    num_cities=int(req.params.get("num_cities", 5)),
                    num_instances=req.num_instances,
                    base_seed=req.base_seed,
                    name=req.name,
                )
            else:
                return dataset_manager.generate_tsp_euclidean(
                    num_cities=int(req.params.get("num_cities", 5)),
                    num_instances=req.num_instances,
                    base_seed=req.base_seed,
                    name=req.name,
                )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported problem type: '{req.problem_type}'")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(dataset_id: str) -> None:
    """Delete a dataset by ID."""
    try:
        dataset_manager.delete(dataset_id)
    except DatasetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
