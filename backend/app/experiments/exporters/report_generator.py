"""Structured research report model and orchestrator."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.experiments.models import Experiment
from backend.app.experiments.statistics import statistical_analyzer


class ResearchReport(BaseModel):
    title: str
    experiment_id: str
    problem_type: str
    executive_summary: str
    methodology: str
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    statistical_tests: List[Dict[str, Any]] = Field(default_factory=list)
    hardware_provenance: Dict[str, str] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)


def generate_research_report(experiment: Experiment) -> ResearchReport:
    """Generate structured research findings and analytical conclusions."""
    by_algo = {}
    for r in experiment.results:
        by_algo.setdefault(r.algorithm, []).append(r)

    metrics = {}
    algo_objs = {}
    for algo, runs in by_algo.items():
        objs = [r.objective_value for r in runs if r.objective_value is not None]
        rts = [r.runtime_seconds for r in runs]
        feas = [r.is_feasible for r in runs]
        evals = [r.num_evaluations for r in runs]
        if objs:
            metrics[algo] = statistical_analyzer.compute_metrics(objs, rts, feas, evals)
            algo_objs[algo] = objs

    pairwise = statistical_analyzer.pairwise_comparison(algo_objs) if len(algo_objs) >= 2 else []

    return ResearchReport(
        title=f"Optimization Benchmark Report: {experiment.name}",
        experiment_id=experiment.experiment_id,
        problem_type=experiment.configuration.problem_type,
        executive_summary=(
            f"Evaluation of {len(experiment.configuration.algorithms)} optimization algorithm(s) on "
            f"{experiment.configuration.problem_type} with {experiment.configuration.num_trials} trial(s)."
        ),
        methodology="Independent stochastic trials evaluated against canonical problem formulation with independent evaluation.",
        performance_metrics=metrics,
        statistical_tests=pairwise,
        hardware_provenance={
            "python_version": experiment.metadata.python_version,
            "reproducibility_hash": experiment.metadata.reproducibility_hash,
            "qiskit_version": experiment.metadata.qiskit_version,
        },
        limitations=[
            "Quantum variational algorithms executed on classical Qiskit Aer statevector simulators.",
            "Heuristic convergence subject to stochastic variance across random seeds.",
        ],
    )
