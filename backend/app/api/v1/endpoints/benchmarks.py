"""Benchmark orchestration REST endpoints — Stage 8.2."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from backend.app.experiments.benchmark_orchestrator import (
    BenchmarkConfiguration,
    BenchmarkRecord,
    BenchmarkMode,
    benchmark_orchestrator,
)
from backend.app.experiments.models import ExperimentAlgorithm

router = APIRouter(prefix="/benchmarks", tags=["Benchmarks"])


@router.post("", response_model=BenchmarkRecord, status_code=201)
async def run_benchmark(config: BenchmarkConfiguration) -> BenchmarkRecord:
    """Execute a multi-algorithm benchmark run synchronously."""
    try:
        return benchmark_orchestrator.run_benchmark(config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("", response_model=List[BenchmarkRecord])
async def list_benchmarks() -> List[BenchmarkRecord]:
    """List all benchmark records."""
    return benchmark_orchestrator.list_benchmarks()


@router.get("/{benchmark_id}", response_model=BenchmarkRecord)
async def get_benchmark(benchmark_id: str) -> BenchmarkRecord:
    """Retrieve a benchmark record by ID."""
    record = benchmark_orchestrator.get_benchmark(benchmark_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Benchmark '{benchmark_id}' not found.")
    return record
