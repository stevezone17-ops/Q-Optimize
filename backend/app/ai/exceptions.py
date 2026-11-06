"""Domain-specific exceptions for the AI and Machine Learning module."""

from typing import Optional, Dict, Any


class AIError(Exception):
    """Base exception for all AI/ML module errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class FeatureExtractionError(AIError):
    """Raised when feature extraction fails on an optimization problem instance."""
    pass


class ModelNotTrainedError(AIError):
    """Raised when inference is requested on an untrained ML model."""
    pass


class ModelNotFoundError(AIError):
    """Raised when a requested model ID or version is not found in the registry."""
    pass


class InferenceError(AIError):
    """Raised when inference fails during prediction or scoring."""
    pass


class DataQualityError(AIError):
    """Raised when training data fails quality or integrity constraints."""
    pass


class InsufficientDataError(AIError):
    """Raised when dataset size does not meet the minimum threshold for training."""
    pass


class OutOfDistributionError(AIError):
    """Raised when a problem instance falls significantly outside training distribution."""
    pass


class LLMProviderError(AIError):
    """Raised when communication with an external LLM provider fails."""
    pass


class NaturalLanguageParsingError(AIError):
    """Raised when natural language text cannot be interpreted into a valid problem draft."""
    pass
