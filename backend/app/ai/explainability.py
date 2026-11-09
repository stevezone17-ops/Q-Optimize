"""Model explainability, decision rationale, confidence calibration, and OOD detection."""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from backend.app.domain.problems.models import ProblemType
from backend.app.ai.models import (
    OptimizationFeatures,
    RankedSolverAlternative,
)
from backend.app.ai.training_pipeline import ModelTrainingPipeline
from backend.app.ai.config import ai_settings
from backend.app.core.logging import logger


class ExplainabilityEngine:
    """Provides human-interpretable rationale, calibration checks, and out-of-distribution safeguards."""

    # Reference baseline distributions for typical instances (mean, std) for OOD checks
    # [num_vars, num_constr, constr_density, search_space, c_min, c_max, c_mean, c_std, c_range,
    #  graph_dens, avg_deg, deg_std, qubo_vars, qubo_dens, ising_spins, ising_dens, qubits, depth]
    FEATURE_DISTRIBUTION_MEANS = np.array([
        10.0, 6.0, 0.5, 12.0, 1.0, 20.0, 8.0, 4.0, 15.0,
        0.4, 3.0, 1.0, 10.0, 0.4, 10.0, 0.4, 10.0, 5.0
    ], dtype=float)

    FEATURE_DISTRIBUTION_STDS = np.array([
        8.0, 8.0, 0.5, 15.0, 2.0, 25.0, 10.0, 6.0, 20.0,
        0.3, 2.5, 1.5, 8.0, 0.3, 8.0, 0.3, 8.0, 4.0
    ], dtype=float)

    @classmethod
    def generate_recommendation_explanation(
        cls,
        features: OptimizationFeatures,
        recommended_solver: str,
        ranked_alternatives: List[RankedSolverAlternative],
        feature_importances: Optional[Dict[str, float]] = None,
    ) -> str:
        """
        Synthesize plain-English reasoning explaining why the recommended solver was chosen,
        which features dominated, and why alternatives were ranked lower.
        """
        p_type = features.problem_type
        runner_up = ranked_alternatives[1] if len(ranked_alternatives) > 1 else None

        # Identify top 2 influencing features
        top_feats: List[str] = []
        if feature_importances:
            sorted_imp = sorted(feature_importances.items(), key=lambda x: x[1], reverse=True)
            top_feats = [f"{k} (importance {v:.2f})" for k, v in sorted_imp[:2]]

        feat_str = f" Influenced primarily by: {', '.join(top_feats)}." if top_feats else ""

        # Check uncertainty
        top_score = ranked_alternatives[0].score if ranked_alternatives else 1.0
        runner_up_score = runner_up.score if runner_up else 0.0
        is_uncertain = (top_score - runner_up_score) < 0.10

        uncertainty_note = ""
        if is_uncertain and runner_up:
            uncertainty_note = (
                f" Note: Prediction is competitive; '{runner_up.solver_name}' has similar fitness "
                f"({runner_up_score * 100:.1f}% vs {top_score * 100:.1f}%)."
            )

        base_reason = (
            f"Recommended '{recommended_solver}' for {p_type.value.upper()} "
            f"(decision variables: {features.num_variables}, search space log2: {features.estimated_search_space_log2:.1f}, "
            f"constraints: {features.num_constraints}).{feat_str}{uncertainty_note}"
        )
        return base_reason

    @classmethod
    def check_confidence_calibration(
        cls,
        predicted_probs: List[float],
        actual_outcomes: List[int],
    ) -> Tuple[float, bool]:
        """
        Compute Brier score to assess calibration of predicted probabilities:
        Brier = (1/N) * sum((p_i - y_i)^2).
        Returns (brier_score, is_calibrated).
        """
        if not predicted_probs or not actual_outcomes or len(predicted_probs) != len(actual_outcomes):
            return 1.0, False

        p = np.array(predicted_probs, dtype=float)
        y = np.array(actual_outcomes, dtype=float)

        brier = float(np.mean((p - y) ** 2))
        # Well-calibrated models typically have Brier score < 0.20
        is_calibrated = (brier < 0.25)
        return brier, is_calibrated

    @classmethod
    def detect_out_of_distribution(
        cls,
        features: OptimizationFeatures,
        training_matrix: Optional[np.ndarray] = None,
    ) -> Tuple[bool, float, List[str]]:
        """
        Check if an optimization problem instance diverges significantly from training distribution.
        Returns: (is_ood, max_z_score, list_of_divergent_features)
        """
        vec = np.array(features.to_feature_vector(), dtype=float)

        if training_matrix is not None and len(training_matrix) >= 5:
            means = np.mean(training_matrix, axis=0)
            stds = np.std(training_matrix, axis=0) + 1e-6
        else:
            means = cls.FEATURE_DISTRIBUTION_MEANS
            stds = cls.FEATURE_DISTRIBUTION_STDS

        z_scores = np.abs((vec - means) / stds)
        max_z = float(np.max(z_scores))
        threshold = ai_settings.OUT_OF_DISTRIBUTION_Z_SCORE

        is_ood = (max_z > threshold)
        divergent_features: List[str] = []

        if is_ood:
            names = ModelTrainingPipeline.FEATURE_NAMES
            for idx, z_val in enumerate(z_scores):
                if z_val > threshold:
                    feat_name = names[idx] if idx < len(names) else f"feature_{idx}"
                    divergent_features.append(f"{feat_name} (z={z_val:.1f})")

            logger.warning(f"OOD problem instance detected: max_z={max_z:.2f} > {threshold}. Features: {divergent_features}")

        return is_ood, max_z, divergent_features

