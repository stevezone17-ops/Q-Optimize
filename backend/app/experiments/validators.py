"""Validation and anomaly detection for benchmark experiments and trial records."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.experiments.models import Experiment, ExperimentResult


class ValidationIssue(BaseModel):
    severity: str  # "error", "warning", "info"
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ValidationReport(BaseModel):
    experiment_id: str
    is_valid: bool
    num_issues: int
    issues: List[ValidationIssue] = Field(default_factory=list)
    outliers_detected: List[Dict[str, Any]] = Field(default_factory=list)


class BenchmarkValidator:
    """Validates experiment integrity, detects anomalies, and flags statistical outliers."""

    def validate_experiment(self, experiment: Experiment) -> ValidationReport:
        issues: List[ValidationIssue] = []
        outliers: List[Dict[str, Any]] = []

        # 1. Check for expected results
        expected_total = len(experiment.configuration.algorithms) * experiment.configuration.num_trials
        actual_total = len(experiment.results)

        if actual_total < expected_total:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    code="MISSING_TRIALS",
                    message=f"Expected {expected_total} trial results, found {actual_total}.",
                    details={"expected": expected_total, "actual": actual_total},
                )
            )

        # 2. Check for duplicate trials per algorithm
        seen_trials = set()
        for r in experiment.results:
            key = (r.algorithm, r.trial_index)
            if key in seen_trials:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="DUPLICATE_TRIAL",
                        message=f"Duplicate result for {r.algorithm} trial {r.trial_index}.",
                        details={"algorithm": r.algorithm, "trial_index": r.trial_index},
                    )
                )
            seen_trials.add(key)

        # 3. Check for failed trials or invalid values
        for r in experiment.results:
            if r.status == "failed" or r.error:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        code="TRIAL_EXECUTION_FAILED",
                        message=f"Trial {r.trial_index} for {r.algorithm} failed: {r.error}",
                        details={"algorithm": r.algorithm, "trial_index": r.trial_index, "error": r.error},
                    )
                )
            elif r.objective_value is None:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="NULL_OBJECTIVE",
                        message=f"Trial {r.trial_index} for {r.algorithm} has null objective value.",
                        details={"algorithm": r.algorithm, "trial_index": r.trial_index},
                    )
                )

        # 4. Outlier detection per algorithm using IQR (Tukey's Fences)
        # We flag outliers for researcher review without deleting them!
        by_algo: Dict[str, List[ExperimentResult]] = {}
        for r in experiment.results:
            if r.objective_value is not None:
                by_algo.setdefault(r.algorithm, []).append(r)

        for algo, runs in by_algo.items():
            if len(runs) >= 4:
                vals = sorted(r.objective_value for r in runs if r.objective_value is not None)
                n = len(vals)
                q1 = vals[n // 4]
                q3 = vals[(3 * n) // 4]
                iqr = q3 - q1
                if iqr > 0:
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    for r in runs:
                        if r.objective_value is not None and (r.objective_value < lower_bound or r.objective_value > upper_bound):
                            outliers.append({
                                "algorithm": algo,
                                "trial_index": r.trial_index,
                                "value": r.objective_value,
                                "lower_bound": lower_bound,
                                "upper_bound": upper_bound,
                                "note": "Flagged by IQR method for inspection; preserved in dataset.",
                            })

        # Calculate validity: valid if no error severity issues
        has_errors = any(i.severity == "error" for i in issues)
        return ValidationReport(
            experiment_id=experiment.experiment_id,
            is_valid=not has_errors,
            num_issues=len(issues),
            issues=issues,
            outliers_detected=outliers,
        )


benchmark_validator = BenchmarkValidator()
