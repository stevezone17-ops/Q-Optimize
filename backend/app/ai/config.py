"""AI and Machine Learning Module Configuration Settings."""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    """Configuration for AI assistants, feature engineering, and solver recommenders."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Module versioning
    AI_MODULE_VERSION: str = "1.0.0"
    FEATURE_SCHEMA_VERSION: str = "v1.0.0"
    DEFAULT_MODEL_VERSION: str = "v1.0.0"

    # LLM Provider Configuration
    LLM_PROVIDER: str = "gemini"  # "gemini" or "mock" or "deterministic"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    LLM_TIMEOUT_SECONDS: float = 15.0
    LLM_MAX_RETRIES: int = 2
    LLM_MAX_INPUT_LENGTH: int = 4000

    # ML Recommender Configuration
    DEFAULT_CLASSIFIER: str = "random_forest"  # "random_forest", "gradient_boosting", "extra_trees", "decision_tree"
    MIN_TRAINING_SAMPLES_PER_CLASS: int = 3
    MIN_TOTAL_TRAINING_SAMPLES: int = 15
    CONFIDENCE_CALIBRATION_THRESHOLD: float = 0.65
    OUT_OF_DISTRIBUTION_Z_SCORE: float = 3.5

    # Storage Paths
    MODEL_STORAGE_DIR: str = "backend/app/ai/artifacts"
    DATASET_STORAGE_DIR: str = "backend/app/ai/datasets"

    # Supported Solvers for Recommendation
    SUPPORTED_SOLVERS: List[str] = [
        "exact",
        "genetic_algorithm",
        "simulated_annealing",
        "standard_qaoa",
        "adaptive_qaoa",
    ]


ai_settings = AISettings()
