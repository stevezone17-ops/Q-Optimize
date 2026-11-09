"""Reusable machine learning training and evaluation pipeline with group-aware splitting."""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from backend.app.ai.models import (
    TrainingSample,
    ModelMetadata,
    ModelEvaluationResult,
    SolverCandidate,
)
from backend.app.ai.exceptions import InsufficientDataError, DataQualityError
from backend.app.ai.config import ai_settings
from backend.app.core.logging import logger


class ModelTrainingPipeline:
    """Manages feature preparation, group-aware cross-validation, and model training."""

    FEATURE_NAMES: List[str] = [
        "num_variables",
        "num_constraints",
        "constraint_density",
        "estimated_search_space_log2",
        "coeff_min",
        "coeff_max",
        "coeff_mean",
        "coeff_std",
        "coeff_range",
        "graph_density",
        "avg_degree",
        "degree_std",
        "qubo_num_binary_vars",
        "qubo_interaction_density",
        "ising_num_spins",
        "ising_coupling_density",
        "required_qubits",
        "estimated_circuit_depth_p1",
    ]

    TARGET_CLASSES: List[str] = [
        SolverCandidate.EXACT.value,
        SolverCandidate.GENETIC_ALGORITHM.value,
        SolverCandidate.SIMULATED_ANNEALING.value,
        SolverCandidate.STANDARD_QAOA.value,
        SolverCandidate.ADAPTIVE_QAOA.value,
    ]

    @classmethod
    def prepare_data_matrices(
        cls,
        samples: List[TrainingSample],
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Extract feature matrix X, target vector y, and group instance array.
        Enforces minimum dataset size constraint.
        """
        if not samples:
            raise InsufficientDataError("Cannot train recommendation model on an empty dataset.")

        if len(samples) < ai_settings.MIN_TOTAL_TRAINING_SAMPLES:
            raise InsufficientDataError(
                f"Insufficient training samples: found {len(samples)}, but at least "
                f"{ai_settings.MIN_TOTAL_TRAINING_SAMPLES} samples are required."
            )

        X_list: List[List[float]] = []
        y_list: List[str] = []
        groups_list: List[str] = []

        for s in samples:
            vec = s.feature_vector or s.features.to_feature_vector()
            X_list.append(vec)
            y_list.append(s.best_solver_label)
            groups_list.append(s.instance_id)

        X = np.array(X_list, dtype=float)
        y = np.array(y_list, dtype=object)
        groups = np.array(groups_list, dtype=object)

        # Impute NaNs or infinities with median/0
        X = np.nan_to_num(X, nan=0.0, posinf=1e6, neginf=-1e6)

        return X, y, groups

    @classmethod
    def split_group_aware(
        cls,
        X: np.ndarray,
        y: np.ndarray,
        groups: np.ndarray,
        test_size: float = 0.25,
        random_state: int = 42,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Perform group-aware splitting to guarantee trials derived from the same
        underlying problem instance never leak across training and test sets.
        """
        unique_groups = np.unique(groups)
        if len(unique_groups) < 2:
            raise DataQualityError("Cannot split dataset with fewer than 2 unique problem instances.")

        gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
        train_idx, test_idx = next(gss.split(X, y, groups=groups))

        # Verify zero group leakage
        train_groups = set(groups[train_idx])
        test_groups = set(groups[test_idx])
        intersection = train_groups.intersection(test_groups)
        if intersection:
            raise DataQualityError(f"Data leakage detected! Shared groups in train/test: {intersection}")

        logger.info(f"Group-aware split: {len(train_idx)} train samples ({len(train_groups)} groups), "
                    f"{len(test_idx)} test samples ({len(test_groups)} groups)")

        return X[train_idx], X[test_idx], y[train_idx], y[test_idx]

    @classmethod
    def compute_evaluation_metrics(
        cls,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        target_classes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Compute standard multiclass classification metrics and confusion matrix."""
        classes = target_classes or cls.TARGET_CLASSES

        acc = float(accuracy_score(y_true, y_pred))
        prec = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
        rec = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
        f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred, labels=classes)
        cm_dict: Dict[str, Dict[str, int]] = {}
        for i, actual_cls in enumerate(classes):
            cm_dict[actual_cls] = {}
            for j, pred_cls in enumerate(classes):
                cm_dict[actual_cls][pred_cls] = int(cm[i, j])

        return {
            "accuracy": acc,
            "macro_precision": prec,
            "macro_recall": rec,
            "macro_f1": f1,
            "confusion_matrix": cm_dict,
        }

