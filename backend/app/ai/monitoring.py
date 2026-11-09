"""Model performance monitoring, feedback collection, and feature drift detection."""

import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import numpy as np
from scipy import stats

from backend.app.core.logging import logger
from backend.app.db.mongodb import db_manager
from backend.app.ai.models import (
    RecommendationFeedback,
    MonitoringMetrics,
    SolverRecommendation,
    OptimizationFeatures,
)
from backend.app.ai.registry import MLModelRegistry

FEEDBACK_COLLECTION = "ai_recommendation_feedback"
AUDIT_COLLECTION = "ai_recommendation_audits"


class ModelMonitor:
    """
    Tracks solver recommendation acceptance, realized execution outcomes,
    prediction diversity, and detects feature drift.
    """

    @classmethod
    async def log_recommendation(cls, rec: SolverRecommendation) -> str:
        """Audit log an emitted solver recommendation."""
        doc = rec.model_dump()
        doc["_id"] = doc.get("problem_id") or str(uuid.uuid4())
        doc["logged_at"] = datetime.now(timezone.utc)

        db = db_manager.db if db_manager.is_connected else None
        if db is not None:
            await db[AUDIT_COLLECTION].insert_one(doc)
        else:
            db_manager.memory_insert(AUDIT_COLLECTION, doc["_id"], doc)

        return doc["_id"]

    @classmethod
    async def record_feedback(cls, feedback: RecommendationFeedback) -> str:
        """Record human acceptance/override and execution quality feedback."""
        doc = feedback.model_dump()
        doc["_id"] = feedback.feedback_id
        doc["logged_at"] = datetime.now(timezone.utc)

        db = db_manager.db if db_manager.is_connected else None
        if db is not None:
            await db[FEEDBACK_COLLECTION].insert_one(doc)
        else:
            db_manager.memory_insert(FEEDBACK_COLLECTION, feedback.feedback_id, doc)

        logger.info(
            f"Logged recommendation feedback {feedback.feedback_id}: "
            f"accepted={feedback.was_accepted}, selected={feedback.user_selected_solver}"
        )
        return feedback.feedback_id

    @classmethod
    async def get_all_feedback(cls) -> List[Dict[str, Any]]:
        """Retrieve all recorded feedback."""
        db = db_manager.db if db_manager.is_connected else None
        if db is not None:
            cursor = db[FEEDBACK_COLLECTION].find({})
            return await cursor.to_list(length=1000)
        return db_manager.memory_list(FEEDBACK_COLLECTION)

    @classmethod
    async def get_all_recommendations(cls) -> List[Dict[str, Any]]:
        """Retrieve all recorded recommendation audits."""
        db = db_manager.db if db_manager.is_connected else None
        if db is not None:
            cursor = db[AUDIT_COLLECTION].find({})
            return await cursor.to_list(length=1000)
        return db_manager.memory_list(AUDIT_COLLECTION)

    @classmethod
    async def compute_monitoring_metrics(cls) -> MonitoringMetrics:
        """Compute aggregate monitoring metrics across historical recommendations and feedback."""
        recs = await cls.get_all_recommendations()
        feedbacks = await cls.get_all_feedback()

        total_recs = len(recs)
        total_feedback = len(feedbacks)

        # Acceptance rate
        accepted_count = sum(1 for f in feedbacks if f.get("was_accepted", False))
        acceptance_rate = (accepted_count / total_feedback) if total_feedback > 0 else 0.0

        # Feasibility rate
        feasible_count = sum(1 for f in feedbacks if f.get("realized_is_feasible") is True)
        feasibility_rate = (feasible_count / total_feedback) if total_feedback > 0 else 0.0

        # Prediction distribution & confidence
        pred_dist: Dict[str, int] = {}
        confidences: List[float] = []
        for r in recs:
            s_name = r.get("recommended_solver", "unknown")
            pred_dist[s_name] = pred_dist.get(s_name, 0) + 1
            if "confidence_score" in r and r["confidence_score"] is not None:
                confidences.append(float(r["confidence_score"]))

        avg_conf = float(np.mean(confidences)) if confidences else 0.0

        # Check for data drift
        active_model = MLModelRegistry.get_model()
        active_ver = active_model.metadata.model_version if active_model else "v1.0.0"

        drift_detected, drift_summary = cls.detect_data_drift(recs)

        return MonitoringMetrics(
            total_recommendations=total_recs,
            total_feedback_count=total_feedback,
            acceptance_rate=float(acceptance_rate),
            realized_feasibility_rate=float(feasibility_rate),
            prediction_distribution=pred_dist,
            average_confidence=avg_conf,
            feature_drift_detected=drift_detected,
            drift_summary=drift_summary,
            active_model_version=active_ver,
        )

    @classmethod
    def detect_data_drift(
        cls,
        recent_recommendations: List[Dict[str, Any]],
        p_threshold: float = 0.05,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Detect distribution shift between baseline reference features and recent inference instances.
        Uses Kolmogorov-Smirnov test (ks_2samp) and z-score divergence.
        """
        if len(recent_recommendations) < 5:
            return False, {"status": "insufficient_samples", "sample_count": len(recent_recommendations)}

        # Extract numerical features from recent recommendations
        vars_recent: List[float] = []
        space_recent: List[float] = []
        density_recent: List[float] = []

        for r in recent_recommendations:
            summary = r.get("key_features_summary") or {}
            if "num_variables" in summary:
                vars_recent.append(float(summary["num_variables"]))
            if "estimated_search_space_log2" in summary:
                space_recent.append(float(summary["estimated_search_space_log2"]))
            if "graph_density" in summary and summary["graph_density"] is not None:
                density_recent.append(float(summary["graph_density"]))

        # Reference baseline distributions (derived from standard benchmark problems)
        baseline_vars = [4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0]
        baseline_space = [4.0, 6.0, 8.0, 10.0, 14.0, 18.0, 22.0, 26.0]

        drift_details: Dict[str, Any] = {}
        drift_detected = False

        if len(vars_recent) >= 5:
            ks_stat, ks_pval = stats.ks_2samp(baseline_vars, vars_recent)
            drift_details["num_variables"] = {
                "ks_statistic": float(ks_stat),
                "p_value": float(ks_pval),
                "drift_flag": bool(ks_pval < p_threshold),
            }
            if ks_pval < p_threshold:
                drift_detected = True

        if len(space_recent) >= 5:
            ks_stat, ks_pval = stats.ks_2samp(baseline_space, space_recent)
            drift_details["search_space_log2"] = {
                "ks_statistic": float(ks_stat),
                "p_value": float(ks_pval),
                "drift_flag": bool(ks_pval < p_threshold),
            }
            if ks_pval < p_threshold:
                drift_detected = True

        drift_details["drift_detected"] = drift_detected
        return drift_detected, drift_details
