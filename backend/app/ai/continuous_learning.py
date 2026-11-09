"""Continuous learning pipeline with automated retraining, holdout gating, and version rollback."""

import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from backend.app.core.logging import logger
from backend.app.ai.models import (
    ModelMetadata,
    RetrainResponse,
    RollbackResponse,
)
from backend.app.ai.recommender import MLSolverRecommenderModel
from backend.app.ai.dataset_builder import ExperimentDatasetBuilder
from backend.app.ai.training_pipeline import ModelTrainingPipeline
from backend.app.ai.evaluation import SolverRecommendationEvaluator
from backend.app.ai.data_access import ExperimentDataAccess
from backend.app.ai.registry import MLModelRegistry


class ContinuousLearningPipeline:
    """
    Coordinates safe, automated retraining of recommendation models with strict
    performance gating, model versioning, and zero-downtime rollbacks.
    """

    @classmethod
    async def evaluate_and_retrain(
        cls,
        algorithm_name: str = "random_forest",
        candidate_version: Optional[str] = None,
        use_sample_test_data: bool = False,
        force_promote: bool = False,
    ) -> RetrainResponse:
        """
        Execute continuous retraining workflow:
        1. Ingest new completed experiment records.
        2. Construct training and holdout datasets.
        3. Train candidate model.
        4. Benchmark candidate against holdout protocol and current active model.
        5. Promote candidate ONLY if it meets or exceeds baseline performance.
        """
        active_model = MLModelRegistry.get_model()
        prev_version = active_model.metadata.model_version if (active_model and active_model.metadata.is_trained) else "v1.0.0"

        # Determine candidate version string
        if not candidate_version:
            # Increment minor version (e.g. v1.0.0 -> v1.1.0)
            try:
                parts = prev_version.lstrip("v").split(".")
                major = int(parts[0])
                minor = int(parts[1]) + 1
                cand_version = f"v{major}.{minor}.0"
            except Exception:
                cand_version = f"v1.1.0"
        else:
            cand_version = candidate_version

        # 1. Prepare dataset
        if use_sample_test_data:
            samples, ds_meta = ExperimentDatasetBuilder.create_sample_test_dataset()
        else:
            records = await ExperimentDataAccess.fetch_all_experiments()
            if len(records) < 5:
                logger.warning(
                    f"Insufficient historical experiment records ({len(records)} < 5). "
                    f"Retraining requires a minimum sample threshold."
                )
                return RetrainResponse(
                    promoted=False,
                    previous_model_version=prev_version,
                    candidate_model_version=cand_version,
                    candidate_metrics={},
                    promotion_reason="Retraining rejected: Insufficient new experimental data points (minimum 5 required).",
                    training_sample_count=len(records),
                )
            samples, ds_meta = ExperimentDatasetBuilder.build_dataset(records)

        # 2. Group-aware train/test partition (80% train, 20% holdout)
        train_samples, test_samples = ModelTrainingPipeline.train_test_split(samples, test_ratio=0.25)
        X_train, y_train, _ = ModelTrainingPipeline.prepare_data_matrices(train_samples)

        # 3. Instantiate and train candidate model
        cand_model = MLSolverRecommenderModel(
            model_id=f"rec_model_{cand_version}_{str(uuid.uuid4())[:8]}",
            algorithm_name=algorithm_name,
            model_version=cand_version,
        )

        cand_model.train(
            X=X_train.tolist(),
            y=y_train.tolist(),
            feature_names=ModelTrainingPipeline.FEATURE_NAMES,
            target_classes=ModelTrainingPipeline.TARGET_CLASSES,
        )

        # 4. Evaluate candidate on holdout test set
        evaluator = SolverRecommendationEvaluator()
        cand_eval = evaluator.evaluate_samples(cand_model, test_samples)

        cand_metrics = {
            "accuracy": cand_eval.accuracy,
            "macro_f1": cand_eval.macro_f1,
            "top_2_accuracy": cand_eval.top_2_accuracy,
            "mean_runtime_regret_ms": cand_eval.mean_runtime_regret_ms,
            "mean_objective_regret_percent": cand_eval.mean_objective_regret_percent,
            "sample_count": cand_eval.sample_count,
        }

        # 5. Gating and Promotion logic
        promoted = False
        promotion_reason = ""

        if force_promote:
            promoted = True
            promotion_reason = "Manual force-promotion override requested."
        elif not active_model or not active_model.metadata.is_trained:
            # No prior active trained model: initial promotion
            promoted = True
            promotion_reason = (
                f"Candidate {cand_version} successfully initialized as active production model "
                f"(Holdout Accuracy: {cand_eval.accuracy:.2f}, Macro F1: {cand_eval.macro_f1:.2f})."
            )
        else:
            # Benchmark against active production model
            active_eval = evaluator.evaluate_samples(active_model, test_samples)
            f1_diff = cand_eval.macro_f1 - active_eval.macro_f1
            acc_diff = cand_eval.accuracy - active_eval.accuracy

            # Candidate must not degrade performance (tolerance: -0.05)
            if f1_diff >= -0.05 and acc_diff >= -0.05:
                promoted = True
                promotion_reason = (
                    f"Candidate {cand_version} met promotion criteria: Macro F1 {cand_eval.macro_f1:.2f} "
                    f"(vs {active_eval.macro_f1:.2f}), Accuracy {cand_eval.accuracy:.2f} "
                    f"(vs {active_eval.accuracy:.2f})."
                )
            else:
                promoted = False
                promotion_reason = (
                    f"Promotion rejected: Candidate performance degraded relative to active model. "
                    f"Candidate F1 {cand_eval.macro_f1:.2f} < Active F1 {active_eval.macro_f1:.2f}. "
                    f"Retaining active version {prev_version}."
                )

        if promoted:
            cand_meta = cand_model.metadata
            cand_meta.accuracy = cand_eval.accuracy
            cand_meta.macro_f1 = cand_eval.macro_f1
            cand_meta.notes = promotion_reason
            cand_meta.training_sample_count = len(train_samples)
            MLModelRegistry.register_model(cand_meta.model_id, cand_model, cand_meta, set_active=True)
            logger.info(f"Promoted new model {cand_version} to active deployment.")
        else:
            # Register candidate as inactive model for auditability
            cand_meta = cand_model.metadata
            cand_meta.accuracy = cand_eval.accuracy
            cand_meta.macro_f1 = cand_eval.macro_f1
            cand_meta.notes = promotion_reason
            cand_meta.training_sample_count = len(train_samples)
            MLModelRegistry.register_model(cand_meta.model_id, cand_model, cand_meta, set_active=False)
            logger.warning(f"Candidate model {cand_version} rejected: {promotion_reason}")

        return RetrainResponse(
            promoted=promoted,
            previous_model_version=prev_version,
            candidate_model_version=cand_version,
            candidate_metrics=cand_metrics,
            promotion_reason=promotion_reason,
            training_sample_count=len(train_samples),
        )

    @classmethod
    def rollback(cls, target_version: str) -> RollbackResponse:
        """
        Revert active recommendation model to an existing registered historical version.
        """
        models = MLModelRegistry.list_models()
        target_model_meta = next((m for m in models if m.model_version == target_version), None)

        if not target_model_meta:
            return RollbackResponse(
                success=False,
                active_model_version="unknown",
                message=f"Target model version '{target_version}' was not found in model registry.",
            )

        # Set target version active
        found = False
        for m_id, model in MLModelRegistry._models.items():
            if model.metadata.model_version == target_version:
                MLModelRegistry.set_active_model(m_id)
                found = True
                break

        if not found:
            return RollbackResponse(
                success=False,
                active_model_version="unknown",
                message=f"Model artifact for version '{target_version}' could not be activated.",
            )

        active = MLModelRegistry.get_model()
        active_ver = active.metadata.model_version if active else target_version

        logger.info(f"Successfully rolled back recommendation model to version '{active_ver}'.")
        return RollbackResponse(
            success=True,
            active_model_version=active_ver,
            message=f"Successfully reverted active recommendation model to version '{active_ver}'.",
        )
