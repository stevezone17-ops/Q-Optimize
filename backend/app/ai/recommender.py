"""Machine learning and rule-based solver recommendation engine with safety filtering."""

import os
import pickle
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.tree import DecisionTreeClassifier

from backend.app.domain.problems.models import ProblemType
from backend.app.ai.models import (
    OptimizationFeatures,
    SolverRecommendation,
    RankedSolverAlternative,
    ModelMetadata,
    RecommendationSource,
    SolverCandidate,
)
from backend.app.ai.interfaces import IMLRecommenderModel, ISolverRecommender
from backend.app.ai.exceptions import ModelNotTrainedError, InferenceError
from backend.app.ai.registry import MLModelRegistry, AIServiceRegistry
from backend.app.ai.feature_extraction import default_feature_extractor
from backend.app.ai.config import ai_settings
from backend.app.core.logging import logger


class MLSolverRecommenderModel(IMLRecommenderModel):
    """
    Scikit-learn based solver recommendation model with probability estimation
    and feature importance analysis.
    """

    def __init__(
        self,
        model_id: str = "rf_solver_recommender",
        model_version: str = "v1.0.0",
        algorithm_name: str = "random_forest",
        hyperparameters: Optional[Dict[str, Any]] = None,
    ):
        self._model_id = model_id
        self._model_version = model_version
        self._algorithm_name = algorithm_name
        self._hyperparams = hyperparameters or {
            "n_estimators": 100,
            "max_depth": 6,
            "random_state": 42,
        }

        self._clf = self._instantiate_classifier()
        self._is_trained = False
        self._feature_names: List[str] = []
        self._target_classes: List[str] = []

    def _instantiate_classifier(self):
        alg = self._algorithm_name.lower()
        if alg == "gradient_boosting":
            return GradientBoostingClassifier(**self._hyperparams)
        elif alg == "extra_trees":
            return ExtraTreesClassifier(**self._hyperparams)
        elif alg == "decision_tree":
            dt_params = {k: v for k, v in self._hyperparams.items() if k != "n_estimators"}
            return DecisionTreeClassifier(**dt_params)
        else:
            return RandomForestClassifier(**self._hyperparams)

    @property
    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            model_id=self._model_id,
            model_version=self._model_version,
            algorithm_name=self._algorithm_name,
            hyperparameters=self._hyperparams,
            feature_schema_version=ai_settings.FEATURE_SCHEMA_VERSION,
            features_list=self._feature_names,
            target_classes=self._target_classes,
            is_trained=self._is_trained,
            is_active=False,
        )

    def train(
        self,
        X: List[List[float]],
        y: List[str],
        feature_names: List[str],
        target_classes: List[str],
    ) -> ModelMetadata:
        """Fit model weights on training data."""
        self._feature_names = feature_names
        self._target_classes = target_classes

        X_arr = np.array(X, dtype=float)
        y_arr = np.array(y, dtype=str)

        self._clf.fit(X_arr, y_arr)
        self._is_trained = True

        logger.info(f"Model '{self._model_id}' successfully fitted on {len(X)} samples across {len(self._target_classes)} classes.")
        return self.metadata

    def predict(self, feature_vector: List[float]) -> str:
        """Predict preferred solver label."""
        if not self._is_trained:
            raise ModelNotTrainedError(f"Model '{self._model_id}' is not trained.")

        X = np.array([feature_vector], dtype=float)
        pred = self._clf.predict(X)[0]
        return str(pred)

    def predict_proba(self, feature_vector: List[float]) -> Dict[str, float]:
        """Predict confidence distribution across known classes."""
        if not self._is_trained:
            raise ModelNotTrainedError(f"Model '{self._model_id}' is not trained.")

        X = np.array([feature_vector], dtype=float)
        probs = self._clf.predict_proba(X)[0]
        classes = self._clf.classes_

        return {str(cls_name): float(prob) for cls_name, prob in zip(classes, probs)}

    def get_feature_importances(self) -> Dict[str, float]:
        """Retrieve feature importance weights if available."""
        if not self._is_trained or not hasattr(self._clf, "feature_importances_"):
            return {}

        importances = self._clf.feature_importances_
        names = self._feature_names or [f"feat_{i}" for i in range(len(importances))]
        return {name: float(imp) for name, imp in zip(names, importances)}

    def save(self, filepath: str) -> None:
        """Serialize model artifact to disk."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        artifact = {
            "model_id": self._model_id,
            "model_version": self._model_version,
            "algorithm_name": self._algorithm_name,
            "hyperparameters": self._hyperparams,
            "is_trained": self._is_trained,
            "feature_names": self._feature_names,
            "target_classes": self._target_classes,
            "classifier": self._clf,
        }
        with open(filepath, "wb") as f:
            pickle.dump(artifact, f)
        logger.info(f"Serialized model artifact to '{filepath}'")

    def load(self, filepath: str) -> None:
        """Deserialize model artifact from disk."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model artifact file '{filepath}' does not exist.")

        with open(filepath, "rb") as f:
            artifact = pickle.load(f)

        self._model_id = artifact["model_id"]
        self._model_version = artifact["model_version"]
        self._algorithm_name = artifact["algorithm_name"]
        self._hyperparams = artifact["hyperparameters"]
        self._is_trained = artifact["is_trained"]
        self._feature_names = artifact["feature_names"]
        self._target_classes = artifact["target_classes"]
        self._clf = artifact["classifier"]
        logger.info(f"Loaded model artifact from '{filepath}'")


class RuleBasedSolverRecommender:
    """
    Expert system implementing transparent, deterministic recommendations
    grounded in computational complexity and empirical solver limits.
    """

    @classmethod
    def recommend(
        cls,
        problem_type: ProblemType,
        features: OptimizationFeatures,
        user_constraints: Optional[Dict[str, Any]] = None,
    ) -> SolverRecommendation:
        """Produce expert rule-based solver recommendation with safety bounds."""
        n_vars = features.num_variables
        constraints = user_constraints or {}
        time_limit = constraints.get("time_limit_seconds")

        ranked: List[RankedSolverAlternative] = []
        rec_solver = SolverCandidate.EXACT.value
        explanation = ""
        confidence = 0.90

        if problem_type == ProblemType.ASSIGNMENT:
            # Hungarian algorithm solves LAP in O(n^3) polynomial time
            rec_solver = SolverCandidate.EXACT.value
            explanation = (
                f"For the Linear Assignment Problem with {features.num_agents} agents and {features.num_tasks} tasks, "
                f"the exact Hungarian algorithm runs in polynomial time O(n³) and guarantees the proven optimal matching."
            )
            confidence = 0.98
            ranked = [
                RankedSolverAlternative(
                    solver_name=SolverCandidate.EXACT.value,
                    score=0.98,
                    rank=1,
                    is_compatible=True,
                    reason="Exact polynomial-time Hungarian solver guarantees global optimum.",
                    estimated_runtime_class="fast",
                ),
                RankedSolverAlternative(
                    solver_name=SolverCandidate.SIMULATED_ANNEALING.value,
                    score=0.75,
                    rank=2,
                    is_compatible=True,
                    reason="Heuristic pairwise swap annealing provides fast feasible candidate tours.",
                    estimated_runtime_class="fast",
                ),
                RankedSolverAlternative(
                    solver_name=SolverCandidate.GENETIC_ALGORITHM.value,
                    score=0.70,
                    rank=3,
                    is_compatible=True,
                    reason="Order Crossover (OX) maintains permutation feasibility.",
                    estimated_runtime_class="moderate",
                ),
            ]

        elif problem_type == ProblemType.MAX_CUT:
            if features.num_vertices <= 16:
                rec_solver = SolverCandidate.EXACT.value
                explanation = (
                    f"Graph has {features.num_vertices} vertices. Symmetry-reduced binary search over 2^(n-1) states "
                    f"({1 << (features.num_vertices - 1)} evaluations) guarantees the global maximum cut with minimal runtime."
                )
                confidence = 0.95
                ranked = [
                    RankedSolverAlternative(
                        solver_name=SolverCandidate.EXACT.value,
                        score=0.95,
                        rank=1,
                        is_compatible=True,
                        reason="Exact binary search guarantees global optimum for n <= 18 vertices.",
                        estimated_runtime_class="fast",
                    ),
                    RankedSolverAlternative(
                        solver_name=SolverCandidate.ADAPTIVE_QAOA.value,
                        score=0.82,
                        rank=2,
                        is_compatible=(features.num_vertices <= 20),
                        reason="Adaptive depth progression mitigates barren plateaus on graph partitioning.",
                        estimated_runtime_class="moderate",
                    ),
                    RankedSolverAlternative(
                        solver_name=SolverCandidate.SIMULATED_ANNEALING.value,
                        score=0.80,
                        rank=3,
                        is_compatible=True,
                        reason="1-flip Metropolis annealing explores unconstrained binary space efficiently.",
                        estimated_runtime_class="fast",
                    ),
                ]
            elif features.num_vertices <= 20:
                rec_solver = SolverCandidate.ADAPTIVE_QAOA.value
                explanation = (
                    f"Graph has {features.num_vertices} vertices, exceeding fast exact limits but within classical Aer quantum "
                    f"simulation limits (n <= 20 qubits). Adaptive QAOA dynamically explores layer depths with warm-start initializers."
                )
                confidence = 0.85
                ranked = [
                    RankedSolverAlternative(
                        solver_name=SolverCandidate.ADAPTIVE_QAOA.value,
                        score=0.85,
                        rank=1,
                        is_compatible=True,
                        reason="Adaptive QAOA with dynamic depth and Fourier initialization.",
                        estimated_runtime_class="moderate",
                    ),
                    RankedSolverAlternative(
                        solver_name=SolverCandidate.SIMULATED_ANNEALING.value,
                        score=0.83,
                        rank=2,
                        is_compatible=True,
                        reason="Fast heuristic exploration with exponential cooling schedule.",
                        estimated_runtime_class="fast",
                    ),
                    RankedSolverAlternative(
                        solver_name=SolverCandidate.GENETIC_ALGORITHM.value,
                        score=0.78,
                        rank=3,
                        is_compatible=True,
                        reason="Population-based binary crossover and bit-flip mutation.",
                        estimated_runtime_class="moderate",
                    ),
                ]
            else:
                rec_solver = SolverCandidate.SIMULATED_ANNEALING.value
                explanation = (
                    f"Graph has {features.num_vertices} vertices. Classical heuristic simulated annealing is recommended "
                    f"to avoid exponential runtime explosions while efficiently maximizing cut weight."
                )
                confidence = 0.88
                ranked = [
                    RankedSolverAlternative(
                        solver_name=SolverCandidate.SIMULATED_ANNEALING.value,
                        score=0.88,
                        rank=1,
                        is_compatible=True,
                        reason="Metropolis cooling avoids local minima on large unconstrained graphs.",
                        estimated_runtime_class="fast",
                    ),
                    RankedSolverAlternative(
                        solver_name=SolverCandidate.GENETIC_ALGORITHM.value,
                        score=0.82,
                        rank=2,
                        is_compatible=True,
                        reason="Evolutionary search over binary chromosomes.",
                        estimated_runtime_class="moderate",
                    ),
                ]

        elif problem_type == ProblemType.TSP:
            if features.num_cities <= 9:
                rec_solver = SolverCandidate.EXACT.value
                explanation = (
                    f"Problem instance has {features.num_cities} cities. Permutation enumeration evaluating (n-1)! = "
                    f"{math.factorial(features.num_cities - 1)} Hamiltonian cycles guarantees the proven shortest tour."
                )
                confidence = 0.95
                ranked = [
                    RankedSolverAlternative(
                        solver_name=SolverCandidate.EXACT.value,
                        score=0.95,
                        rank=1,
                        is_compatible=True,
                        reason="Exact permutation solver guarantees optimal tour for n <= 10 cities.",
                        estimated_runtime_class="fast",
                    ),
                    RankedSolverAlternative(
                        solver_name=SolverCandidate.SIMULATED_ANNEALING.value,
                        score=0.84,
                        rank=2,
                        is_compatible=True,
                        reason="2-opt edge inversion neighborhood moves provide rapid tour improvements.",
                        estimated_runtime_class="fast",
                    ),
                    RankedSolverAlternative(
                        solver_name=SolverCandidate.GENETIC_ALGORITHM.value,
                        score=0.80,
                        rank=3,
                        is_compatible=True,
                        reason="Order Crossover (OX) with 2-opt mutation preserves valid tour cycles.",
                        estimated_runtime_class="moderate",
                    ),
                ]
            else:
                rec_solver = SolverCandidate.SIMULATED_ANNEALING.value
                explanation = (
                    f"Problem instance has {features.num_cities} cities. Permutation search space exceeds exact enumeration limits. "
                    f"Simulated Annealing using 2-opt edge inversions is recommended for superior tour quality under fixed time budgets."
                )
                confidence = 0.89
                ranked = [
                    RankedSolverAlternative(
                        solver_name=SolverCandidate.SIMULATED_ANNEALING.value,
                        score=0.89,
                        rank=1,
                        is_compatible=True,
                        reason="2-opt edge swap neighborhood moves excel on Euclidean and metric TSP.",
                        estimated_runtime_class="fast",
                    ),
                    RankedSolverAlternative(
                        solver_name=SolverCandidate.GENETIC_ALGORITHM.value,
                        score=0.83,
                        rank=2,
                        is_compatible=True,
                        reason="Order Crossover (OX) with inversion mutation maintains tour feasibility.",
                        estimated_runtime_class="moderate",
                    ),
                ]

        return SolverRecommendation(
            problem_type=problem_type,
            recommended_solver=rec_solver,
            confidence_score=confidence,
            is_confidence_calibrated=False,
            recommendation_source=RecommendationSource.RULE_BASED,
            ranked_alternatives=ranked,
            explanation=explanation,
            key_features_summary={
                "num_variables": features.num_variables,
                "num_constraints": features.num_constraints,
                "estimated_search_space_log2": features.estimated_search_space_log2,
            },
            resource_considerations={
                "required_qubits": features.required_qubits,
                "quantum_simulator_compatible": (features.required_qubits <= 20),
            },
            known_limitations=[
                "Rule-based recommendations reflect standard optimization guidelines and do not guarantee global optimality on non-exact solvers.",
                "Classical CPU simulation of quantum circuits is bounded to n <= 20 qubits.",
            ],
        )


class IntelligentSolverRecommender(ISolverRecommender):
    """
    Unified high-level recommendation coordinator integrating ML predictions,
    expert rule fallbacks, and strict safety filtering.
    """

    async def recommend_solver(
        self,
        problem_type: ProblemType,
        instance_data: Dict[str, Any],
        problem_id: Optional[str] = None,
        formulation_data: Optional[Dict[str, Any]] = None,
        user_constraints: Optional[Dict[str, Any]] = None,
    ) -> SolverRecommendation:
        """Produce an intelligent, safeguarded solver recommendation with explanations."""
        # 1. Deterministic feature extraction
        features = default_feature_extractor.extract_features(
            problem_type=problem_type,
            instance_data=instance_data,
            formulation_data=formulation_data,
            resource_budget=user_constraints,
        )

        # 2. Check if active ML model is trained and available
        active_model = MLModelRegistry.get_model()
        is_trained = MLModelRegistry.is_active_model_trained()

        if not active_model or not is_trained:
            logger.info("Active ML model is not trained. Delegating to expert rule-based recommender.")
            rec = RuleBasedSolverRecommender.recommend(problem_type, features, user_constraints)
            rec.problem_id = problem_id
            return self._apply_safety_filters(rec, features, user_constraints)

        # 3. Predict via ML model
        try:
            vec = features.to_feature_vector()
            pred_solver = active_model.predict(vec)
            prob_dict = active_model.predict_proba(vec)

            # Sort candidate classes by predicted probability
            sorted_classes = sorted(prob_dict.items(), key=lambda x: x[1], reverse=True)
            top_prob = prob_dict.get(pred_solver, 0.5)

            ranked_alts: List[RankedSolverAlternative] = []
            for rank_idx, (s_name, prob_val) in enumerate(sorted_classes, start=1):
                ranked_alts.append(
                    RankedSolverAlternative(
                        solver_name=s_name,
                        score=float(prob_val),
                        rank=rank_idx,
                        is_compatible=True,  # Will be refined in safety filter
                        reason=f"Predicted suitability {prob_val * 100:.1f}% based on historical benchmark distributions.",
                    )
                )

            model_meta = active_model.metadata
            rec = SolverRecommendation(
                problem_id=problem_id,
                problem_type=problem_type,
                recommended_solver=pred_solver,
                confidence_score=float(top_prob),
                is_confidence_calibrated=False,
                recommendation_source=RecommendationSource.ML_MODEL,
                ranked_alternatives=ranked_alts,
                explanation=(
                    f"ML model '{model_meta.model_id}' ({model_meta.algorithm_name}) selected '{pred_solver}' "
                    f"with {top_prob * 100:.1f}% score based on problem characteristics (variables: {features.num_variables}, "
                    f"search space log2: {features.estimated_search_space_log2:.1f})."
                ),
                key_features_summary={
                    "num_variables": features.num_variables,
                    "graph_density": features.graph_density,
                    "estimated_search_space_log2": features.estimated_search_space_log2,
                },
                resource_considerations={
                    "required_qubits": features.required_qubits,
                    "circuit_depth_estimate": features.estimated_circuit_depth_p1,
                },
                model_version=model_meta.model_version,
                known_limitations=[
                    "ML predictions reflect learned empirical performance and do not guarantee optimal execution outcomes.",
                ],
            )
            return self._apply_safety_filters(rec, features, user_constraints)

        except Exception as e:
            logger.warning(f"ML inference failed ({e}). Falling back to rule-based recommendation.")
            rec = RuleBasedSolverRecommender.recommend(problem_type, features, user_constraints)
            rec.problem_id = problem_id
            rec.recommendation_source = RecommendationSource.FALLBACK
            return self._apply_safety_filters(rec, features, user_constraints)

    @classmethod
    def _apply_safety_filters(
        cls,
        rec: SolverRecommendation,
        features: OptimizationFeatures,
        user_constraints: Optional[Dict[str, Any]],
    ) -> SolverRecommendation:
        """
        Enforce strict safety ceilings:
        1. Exact solver filtered out if MaxCut n > 18 or TSP n > 10.
        2. Quantum solvers filtered out if required qubits > 20.
        """
        constraints = user_constraints or {}
        time_limit = constraints.get("time_limit_seconds")

        # Mark compatibility on all ranked alternatives
        filtered_ranked: List[RankedSolverAlternative] = []
        for alt in rec.ranked_alternatives:
            s_name = alt.solver_name
            is_compat = True
            reason = alt.reason

            # Exact limits
            if s_name == SolverCandidate.EXACT.value:
                if rec.problem_type == ProblemType.MAX_CUT and features.num_vertices > 18:
                    is_compat = False
                    reason = f"ExactSolver disabled: graph vertices ({features.num_vertices}) exceed safety limit (n <= 18)."
                elif rec.problem_type == ProblemType.TSP and features.num_cities > 10:
                    is_compat = False
                    reason = f"ExactSolver disabled: cities ({features.num_cities}) exceed factorial limit (n <= 10)."

            # Quantum limits
            if s_name in [SolverCandidate.STANDARD_QAOA.value, SolverCandidate.ADAPTIVE_QAOA.value]:
                if features.required_qubits > 20:
                    is_compat = False
                    reason = f"Quantum simulator disabled: required qubits ({features.required_qubits}) exceed CPU simulation ceiling (n <= 20)."

            alt.is_compatible = is_compat
            alt.reason = reason
            filtered_ranked.append(alt)

        rec.ranked_alternatives = filtered_ranked

        # If primary recommended solver became incompatible, switch to highest compatible alternative
        primary_compat = any(a.solver_name == rec.recommended_solver and a.is_compatible for a in filtered_ranked)
        if not primary_compat:
            compat_alts = [a for a in filtered_ranked if a.is_compatible]
            if compat_alts:
                compat_alts.sort(key=lambda x: x.score, reverse=True)
                new_rec = compat_alts[0]
                rec.explanation += f" (Note: Original recommendation overridden by safety filter to '{new_rec.solver_name}')."
                rec.recommended_solver = new_rec.solver_name
                rec.confidence_score = new_rec.score

        return rec


default_solver_recommender = IntelligentSolverRecommender()
