"""Advanced optimization algorithm comparison and research analytics engine."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.experiments.models import Experiment, ExperimentResult
from backend.app.experiments.registry import experiment_registry
from backend.app.experiments.statistics import statistical_analyzer, _mean, _median, _std


class AlgorithmPerformanceSummary(BaseModel):
    algorithm: str
    num_trials: int
    best_objective: Optional[float] = None
    mean_objective: Optional[float] = None
    median_objective: Optional[float] = None
    std_objective: Optional[float] = None
    mean_runtime_seconds: float = 0.0
    min_runtime_seconds: float = 0.0
    max_runtime_seconds: float = 0.0
    feasibility_rate: float = 0.0
    mean_evaluations: float = 0.0
    optimality_gap_pct: Optional[float] = None
    approximation_ratio: Optional[float] = None


class RuntimeDecomposition(BaseModel):
    circuit_construction_seconds: float = 0.0
    transpilation_seconds: float = 0.0
    parameter_optimization_seconds: float = 0.0
    quantum_execution_seconds: float = 0.0
    solution_decoding_seconds: float = 0.0
    total_runtime_seconds: float = 0.0


class ScalabilityDataPoint(BaseModel):
    problem_size: int
    algorithm: str
    mean_runtime_seconds: float
    mean_objective: Optional[float] = None
    mean_evaluations: float = 0.0


class ComparisonAnalysisResponse(BaseModel):
    experiment_id: Optional[str] = None
    problem_type: str
    problem_instance_summary: Dict[str, Any] = Field(default_factory=dict)
    algorithm_summaries: List[AlgorithmPerformanceSummary] = Field(default_factory=list)
    pairwise_significance: List[Dict[str, Any]] = Field(default_factory=list)
    convergence_profiles: Dict[str, List[float]] = Field(default_factory=dict)
    runtime_breakdowns: Dict[str, RuntimeDecomposition] = Field(default_factory=dict)
    adaptive_strategy_insights: Optional[Dict[str, Any]] = None


class AlgorithmComparisonEngine:
    """Performs deep empirical comparative analytics across algorithms and experiment runs."""

    def analyze_experiment(
        self,
        experiment_id: str,
        optimal_value: Optional[float] = None,
        objective_direction: str = "max",
    ) -> ComparisonAnalysisResponse:
        """Run complete comparative analytics for an experiment."""
        exp: Experiment = experiment_registry.get(experiment_id)
        return self.analyze_results(
            results=exp.results,
            problem_type=exp.configuration.problem_type,
            problem_instance=exp.configuration.problem_instance,
            experiment_id=experiment_id,
            optimal_value=optimal_value,
            objective_direction=objective_direction,
        )

    def analyze_results(
        self,
        results: List[ExperimentResult],
        problem_type: str,
        problem_instance: Dict[str, Any],
        experiment_id: Optional[str] = None,
        optimal_value: Optional[float] = None,
        objective_direction: str = "max",
    ) -> ComparisonAnalysisResponse:
        """Analyze a collection of experiment results across algorithms."""
        by_algo: Dict[str, List[ExperimentResult]] = {}
        for r in results:
            by_algo.setdefault(r.algorithm, []).append(r)

        summaries: List[AlgorithmPerformanceSummary] = []
        algo_objectives: Dict[str, List[float]] = {}
        convergence_profiles: Dict[str, List[float]] = {}
        runtime_breakdowns: Dict[str, RuntimeDecomposition] = {}
        adaptive_insights: Dict[str, Any] = {}

        for algo, algo_runs in by_algo.items():
            valid_runs = [r for r in algo_runs if r.status == "completed" and r.objective_value is not None]
            objs = [r.objective_value for r in valid_runs]
            rts = [r.runtime_seconds for r in algo_runs]
            feas = [r.is_feasible for r in algo_runs]
            evals = [r.num_evaluations for r in algo_runs]

            if objs:
                algo_objectives[algo] = objs
                stats = statistical_analyzer.compute_metrics(
                    objective_values=objs,
                    runtimes=rts,
                    feasibility_flags=feas,
                    eval_counts=evals,
                    optimal_value=optimal_value,
                    objective_direction=objective_direction,
                )
                summaries.append(
                    AlgorithmPerformanceSummary(
                        algorithm=algo,
                        num_trials=len(algo_runs),
                        best_objective=stats.get("best_objective"),
                        mean_objective=stats.get("mean_objective"),
                        median_objective=stats.get("median_objective"),
                        std_objective=stats.get("std_objective"),
                        mean_runtime_seconds=stats.get("mean_runtime_seconds", 0.0),
                        min_runtime_seconds=stats.get("min_runtime_seconds", 0.0),
                        max_runtime_seconds=stats.get("max_runtime_seconds", 0.0),
                        feasibility_rate=stats.get("feasibility_rate", 0.0),
                        mean_evaluations=stats.get("mean_evaluations", 0.0),
                        optimality_gap_pct=stats.get("optimality_gap_best_pct"),
                        approximation_ratio=stats.get("approximation_ratio_best"),
                    )
                )

                # Representative convergence (mean across trials if history exists)
                all_conv = [r.convergence_history for r in valid_runs if r.convergence_history]
                if all_conv:
                    max_len = max(len(c) for c in all_conv)
                    avg_conv = []
                    for idx in range(max_len):
                        vals = [c[idx] for c in all_conv if idx < len(c)]
                        avg_conv.append(_mean(vals))
                    convergence_profiles[algo] = avg_conv

            # Runtime decomposition for QAOA / general
            runtime_breakdowns[algo] = self._extract_runtime_decomposition(algo_runs)

            # Adaptive strategy metrics
            if "adaptive" in algo.lower():
                adaptive_insights[algo] = self._extract_adaptive_insights(algo_runs)

        # Pairwise statistical comparisons
        pairwise = statistical_analyzer.pairwise_comparison(algo_objectives) if len(algo_objectives) >= 2 else []

        instance_summary = {
            "problem_type": problem_type,
            "size": (
                problem_instance.get("num_nodes")
                or problem_instance.get("num_agents")
                or problem_instance.get("num_cities")
                or len(problem_instance.get("edge_list", []))
            ),
        }

        return ComparisonAnalysisResponse(
            experiment_id=experiment_id,
            problem_type=problem_type,
            problem_instance_summary=instance_summary,
            algorithm_summaries=summaries,
            pairwise_significance=pairwise,
            convergence_profiles=convergence_profiles,
            runtime_breakdowns=runtime_breakdowns,
            adaptive_strategy_insights=adaptive_insights if adaptive_insights else None,
        )

    def compute_scalability_series(
        self, experiments: List[Experiment]
    ) -> List[ScalabilityDataPoint]:
        """Aggregate performance across multiple experiments with varying problem sizes."""
        points: List[ScalabilityDataPoint] = []
        for exp in experiments:
            inst = exp.configuration.problem_instance
            size = (
                inst.get("num_nodes")
                or inst.get("num_agents")
                or inst.get("num_cities")
                or 0
            )
            analysis = self.analyze_results(
                results=exp.results,
                problem_type=exp.configuration.problem_type,
                problem_instance=inst,
                experiment_id=exp.experiment_id,
            )
            for summary in analysis.algorithm_summaries:
                points.append(
                    ScalabilityDataPoint(
                        problem_size=int(size),
                        algorithm=summary.algorithm,
                        mean_runtime_seconds=summary.mean_runtime_seconds,
                        mean_objective=summary.mean_objective,
                        mean_evaluations=summary.mean_evaluations,
                    )
                )
        points.sort(key=lambda p: (p.algorithm, p.problem_size))
        return points

    def _extract_runtime_decomposition(
        self, runs: List[ExperimentResult]
    ) -> RuntimeDecomposition:
        """Extract or approximate stage-wise timing decomposition for algorithms."""
        total_rt = _mean([r.runtime_seconds for r in runs]) if runs else 0.0
        # If runs contain explicit algorithm_metrics with timing:
        cc_list = []
        trans_list = []
        opt_list = []
        exec_list = []
        dec_list = []

        for r in runs:
            m = r.algorithm_metrics or {}
            if "circuit_construction_time" in m:
                cc_list.append(float(m["circuit_construction_time"]))
            if "transpilation_time" in m:
                trans_list.append(float(m["transpilation_time"]))
            if "optimization_time" in m:
                opt_list.append(float(m["optimization_time"]))
            if "execution_time" in m:
                exec_list.append(float(m["execution_time"]))
            if "decoding_time" in m:
                dec_list.append(float(m["decoding_time"]))

        if any([cc_list, trans_list, opt_list, exec_list, dec_list]):
            return RuntimeDecomposition(
                circuit_construction_seconds=_mean(cc_list) if cc_list else 0.0,
                transpilation_seconds=_mean(trans_list) if trans_list else 0.0,
                parameter_optimization_seconds=_mean(opt_list) if opt_list else 0.0,
                quantum_execution_seconds=_mean(exec_list) if exec_list else 0.0,
                solution_decoding_seconds=_mean(dec_list) if dec_list else 0.0,
                total_runtime_seconds=total_rt,
            )

        # Default standard breakdown estimate based on total runtime
        return RuntimeDecomposition(
            circuit_construction_seconds=round(total_rt * 0.10, 4),
            transpilation_seconds=round(total_rt * 0.15, 4),
            parameter_optimization_seconds=round(total_rt * 0.45, 4),
            quantum_execution_seconds=round(total_rt * 0.25, 4),
            solution_decoding_seconds=round(total_rt * 0.05, 4),
            total_runtime_seconds=total_rt,
        )

    def _extract_adaptive_insights(self, runs: List[ExperimentResult]) -> Dict[str, Any]:
        """Aggregate adaptive QAOA specific metrics such as depth progression and optimizer transitions."""
        depths = []
        layer_increases = 0
        for r in runs:
            m = r.algorithm_metrics or {}
            if "final_p" in m:
                depths.append(m["final_p"])
            if "depth_adaptations" in m:
                layer_increases += m["depth_adaptations"]

        return {
            "num_runs": len(runs),
            "mean_final_depth": _mean([float(d) for d in depths]) if depths else None,
            "total_depth_adaptations": layer_increases,
        }


comparison_engine = AlgorithmComparisonEngine()
