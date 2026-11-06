"""Abstract interfaces and protocol definitions for AI and ML components."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple

from backend.app.domain.problems.models import ProblemType
from backend.app.ai.models import (
    OptimizationFeatures,
    SolverRecommendation,
    ModelMetadata,
    ModelEvaluationResult,
    TrainingDatasetMetadata,
    ExperimentRecord,
)


class IFeatureExtractor(ABC):
    """Protocol for extracting standardized numeric and categorical features from problem instances."""

    @abstractmethod
    def extract_features(
        self,
        problem_type: ProblemType,
        instance_data: Dict[str, Any],
        formulation_data: Optional[Dict[str, Any]] = None,
        resource_budget: Optional[Dict[str, Any]] = None,
    ) -> OptimizationFeatures:
        """Extract deterministic feature vector from canonical problem instance."""
        pass


class IMLRecommenderModel(ABC):
    """Protocol for an underlying machine learning solver recommendation model."""

    @property
    @abstractmethod
    def metadata(self) -> ModelMetadata:
        """Retrieve model metadata."""
        pass

    @abstractmethod
    def train(
        self,
        X: List[List[float]],
        y: List[str],
        feature_names: List[str],
        target_classes: List[str],
    ) -> ModelMetadata:
        """Fit model weights on prepared training data."""
        pass

    @abstractmethod
    def predict(self, feature_vector: List[float]) -> str:
        """Predict the most suitable solver label for a given feature vector."""
        pass

    @abstractmethod
    def predict_proba(self, feature_vector: List[float]) -> Dict[str, float]:
        """Predict probability or match score distribution across all candidate solvers."""
        pass

    @abstractmethod
    def get_feature_importances(self) -> Dict[str, float]:
        """Retrieve feature importance weights if supported by model architecture."""
        pass

    @abstractmethod
    def save(self, filepath: str) -> None:
        """Serialize model to disk."""
        pass

    @abstractmethod
    def load(self, filepath: str) -> None:
        """Deserialize model from disk."""
        pass


class ISolverRecommender(ABC):
    """High-level recommendation service combining ML prediction, expert rules, and safeguards."""

    @abstractmethod
    async def recommend_solver(
        self,
        problem_type: ProblemType,
        instance_data: Dict[str, Any],
        problem_id: Optional[str] = None,
        formulation_data: Optional[Dict[str, Any]] = None,
        user_constraints: Optional[Dict[str, Any]] = None,
    ) -> SolverRecommendation:
        """Produce an intelligent, safeguarded solver recommendation with explanations."""
        pass


class IModelTrainer(ABC):
    """Protocol for executing model training pipelines with cross-validation and hyperparameter tuning."""

    @abstractmethod
    def train_candidate_model(
        self,
        records: List[ExperimentRecord],
        algorithm: str = "random_forest",
        model_version: str = "v1.0.0",
    ) -> Tuple[IMLRecommenderModel, ModelEvaluationResult, TrainingDatasetMetadata]:
        """Train and evaluate a candidate recommendation model on experiment records."""
        pass


class IModelEvaluator(ABC):
    """Protocol for evaluating classification and regret metrics on holdout test datasets."""

    @abstractmethod
    def evaluate(
        self,
        model: IMLRecommenderModel,
        test_records: List[ExperimentRecord],
    ) -> ModelEvaluationResult:
        """Compute comprehensive evaluation metrics including regret and budget violations."""
        pass


class ILLMProvider(ABC):
    """Protocol for interacting with external or local natural language model providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier (e.g. gemini, mock, deterministic)."""
        pass

    @abstractmethod
    async def generate_draft(
        self,
        prompt: str,
        problem_type_hint: Optional[ProblemType] = None,
    ) -> Dict[str, Any]:
        """Parse natural language into a structured problem proposal draft."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and reachable."""
        pass
