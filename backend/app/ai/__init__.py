"""AI and Machine Learning Intelligence Layer for Q-Optimize."""

from backend.app.ai.models import (
    AIRequest,
    AIResponse,
    OptimizationFeatures,
    SolverRecommendation,
    RankedSolverAlternative,
    ModelMetadata,
    TrainingDatasetMetadata,
    ModelEvaluationResult,
    ExperimentRecord,
    RecommendationFeedback,
    RecommendationSource,
    SolverCandidate,
)
from backend.app.ai.config import ai_settings
from backend.app.ai.exceptions import (
    AIError,
    FeatureExtractionError,
    ModelNotTrainedError,
    ModelNotFoundError,
    InferenceError,
    DataQualityError,
    InsufficientDataError,
    OutOfDistributionError,
    LLMProviderError,
    NaturalLanguageParsingError,
)
from backend.app.ai.interfaces import (
    IFeatureExtractor,
    IMLRecommenderModel,
    ISolverRecommender,
    IModelTrainer,
    IModelEvaluator,
    ILLMProvider,
)
from backend.app.ai.registry import MLModelRegistry, AIServiceRegistry
from backend.app.ai.data_access import ExperimentDataAccess

__all__ = [
    "AIRequest",
    "AIResponse",
    "OptimizationFeatures",
    "SolverRecommendation",
    "RankedSolverAlternative",
    "ModelMetadata",
    "TrainingDatasetMetadata",
    "ModelEvaluationResult",
    "ExperimentRecord",
    "RecommendationFeedback",
    "RecommendationSource",
    "SolverCandidate",
    "ai_settings",
    "AIError",
    "FeatureExtractionError",
    "ModelNotTrainedError",
    "ModelNotFoundError",
    "InferenceError",
    "DataQualityError",
    "InsufficientDataError",
    "OutOfDistributionError",
    "LLMProviderError",
    "NaturalLanguageParsingError",
    "IFeatureExtractor",
    "IMLRecommenderModel",
    "ISolverRecommender",
    "IModelTrainer",
    "IModelEvaluator",
    "ILLMProvider",
    "MLModelRegistry",
    "AIServiceRegistry",
    "ExperimentDataAccess",
]
