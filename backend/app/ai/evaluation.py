"""Evaluation metrics engine for solver recommendation models, measuring classification and regret."""

from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime, timezone
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from backend.app.domain.problems.models import ProblemType
from backend.app.ai.models import (
    ModelEvaluationResult,
    TrainingSample,
    ExperimentRecord,
    SolverCandidate,
)
from backend.app.ai.interfaces import IMLRecommenderModel, IModelEvaluator
from backend.app.ai.training_pipeline import ModelTrainingPipeline
from backend.app.core.logging import logger


class SolverRecommendationEvaluator(IModelEvaluator):
    """
    Evaluates recommendation models on holdout test instances across
    both classification metrics and empirical regret metrics.
    """

    TARGET_CLASSES: List[str] = ModelTrainingPipeline.TARGET_CLASSES

    def evaluate(
        self,
        model: IMLRecommenderModel,
        test_records: List[ExperimentRecord],
    ) -> ModelEvaluationResult:
        """
        Evaluate model against holdout experiment records.
        If test_records is a list of TrainingSample, evaluate directly.
        """
        # Group records by instance if raw experiment records
        samples = self._records_to_samples(test_records)
        return self.evaluate_samples(model, samples)

    def evaluate_samples(
        self,
        model: IMLRecommenderModel,
        test_samples: List[TrainingSample],
    ) -> ModelEvaluationResult:
        """Evaluate model against holdout TrainingSample objects."""
        if not test_samples:
            return ModelEvaluationResult(
                model_id=model.metadata.model_id,
                model_version=model.metadata.model_version,
                dataset_version="empty",
                sample_count=0,
                accuracy=0.0,
                macro_precision=0.0,
                macro_recall=0.0,
                macro_f1=0.0,
            )

        y_true: List[str] = []
        y_pred: List[str] = []
        probs_list: List[Dict[str, float]] = []

        runtime_regrets: List[float] = []
        objective_regrets: List[float] = []
        feasibility_violations = 0
        budget_violations = 0

        for sample in test_samples:
            vec = sample.feature_vector or sample.features.to_feature_vector()
            pred = model.predict(vec)
            probs = model.predict_proba(vec)

            y_true.append(sample.best_solver_label)
            y_pred.append(pred)
            probs_list.append(probs)

            # Regret calculations from sample.solver_evaluations
            evals = sample.solver_evaluations
            if evals:
                # 1. Feasibility regret: did recommended solver produce infeasible when feasible was possible?
                rec_eval = evals.get(pred, {})
                rec_feasible = rec_eval.get("is_feasible", True)
                any_feasible = any(ev.get("is_feasible", False) for ev in evals.values())
                if any_feasible and not rec_feasible:
                    feasibility_violations += 1

                # 2. Objective regret: % difference relative to best achieved objective
                rec_obj = rec_eval.get("objective_value")
                is_max = (sample.problem_type == ProblemType.MAX_CUT)
                valid_objs = [ev.get("objective_value") for ev in evals.values() if ev.get("objective_value") is not None]

                if rec_obj is not None and valid_objs:
                    best_obj = max(valid_objs) if is_max else min(valid_objs)
                    denom = abs(best_obj) + 1e-9
                    obj_diff = (best_obj - rec_obj) if is_max else (rec_obj - best_obj)
                    pct_regret = max(0.0, (obj_diff / denom) * 100.0)
                    objective_regrets.append(pct_regret)

                # 3. Runtime regret: excess runtime vs fastest feasible solver
                feasible_runtimes = [ev.get("runtime_seconds", 0.0) for ev in evals.values() if ev.get("is_feasible", True)]
                if feasible_runtimes and rec_eval:
                    fastest = min(feasible_runtimes)
                    rec_runtime = rec_eval.get("runtime_seconds", 0.0)
                    runtime_regrets.append(max(0.0, (rec_runtime - fastest) * 1000.0))  # ms

                # 4. Budget violation: check if runtime exceeded time limit if specified
                t_limit = sample.features.time_limit_seconds
                if t_limit and rec_eval.get("runtime_seconds", 0.0) > t_limit:
                    budget_violations += 1

        y_true_arr = np.array(y_true, dtype=str)
        y_pred_arr = np.array(y_pred, dtype=str)

        # Classification metrics
        acc = float(accuracy_score(y_true_arr, y_pred_arr))
        prec = float(precision_score(y_true_arr, y_pred_arr, average="macro", zero_division=0))
        rec = float(recall_score(y_true_arr, y_pred_arr, average="macro", zero_division=0))
        f1 = float(f1_score(y_true_arr, y_pred_arr, average="macro", zero_division=0))

        # Top-2 accuracy: true label in top 2 predicted probabilities
        top_2_hits = 0
        for actual, p_dist in zip(y_true, probs_list):
            sorted_classes = [c for c, _ in sorted(p_dist.items(), key=lambda x: x[1], reverse=True)[:2]]
            if actual in sorted_classes:
                top_2_hits += 1
        top_2_acc = float(top_2_hits / len(test_samples)) if test_samples else 0.0

        # Confusion matrix
        cm = confusion_matrix(y_true_arr, y_pred_arr, labels=self.TARGET_CLASSES)
        cm_dict: Dict[str, Dict[str, int]] = {}
        for i, actual_cls in enumerate(self.TARGET_CLASSES):
            cm_dict[actual_cls] = {}
            for j, pred_cls in enumerate(self.TARGET_CLASSES):
                cm_dict[actual_cls][pred_cls] = int(cm[i, j])

        mean_rt_regret = float(np.mean(runtime_regrets)) if runtime_regrets else 0.0
        mean_obj_regret = float(np.mean(objective_regrets)) if objective_regrets else 0.0
        feas_rate = float(feasibility_violations / len(test_samples)) if test_samples else 0.0
        budget_rate = float(budget_violations / len(test_samples)) if test_samples else 0.0

        meta = model.metadata
        return ModelEvaluationResult(
            model_id=meta.model_id,
            model_version=meta.model_version,
            dataset_version="holdout_test",
            evaluated_at=datetime.now(timezone.utc),
            sample_count=len(test_samples),
            accuracy=acc,
            macro_precision=prec,
            macro_recall=rec,
            macro_f1=f1,
            top_2_accuracy=top_2_acc,
            confusion_matrix=cm_dict,
            mean_runtime_regret_ms=mean_rt_regret,
            mean_objective_regret_percent=mean_obj_regret,
            feasibility_violation_rate=feas_rate,
            resource_budget_violation_rate=budget_rate,
            recommendation_coverage=1.0,
        )

    def _records_to_samples(self, records: List[Any]) -> List[TrainingSample]:
        """Convert list of records or samples into TrainingSample list."""
        if not records:
            return []
        if isinstance(records[0], TrainingSample):
            return records
        from backend.app.ai.dataset_builder import ExperimentDatasetBuilder
        samples, _ = ExperimentDatasetBuilder.build_dataset(records)
        return samples
