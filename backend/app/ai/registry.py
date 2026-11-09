"""Model and service registries for AI and Machine Learning components."""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from backend.app.ai.models import ModelMetadata
from backend.app.ai.interfaces import IMLRecommenderModel, ILLMProvider, IFeatureExtractor
from backend.app.ai.exceptions import ModelNotFoundError
from backend.app.ai.config import ai_settings
from backend.app.core.logging import logger


class MLModelRegistry:
    """Registry maintaining active and historical machine learning models."""

    _models: Dict[str, IMLRecommenderModel] = {}
    _metadata: Dict[str, ModelMetadata] = {}
    _active_model_id: Optional[str] = None

    @classmethod
    def register_model(
        cls,
        model_id: str,
        model: IMLRecommenderModel,
        metadata: ModelMetadata,
        set_active: bool = False,
    ) -> None:
        """Register a model instance with its metadata."""
        cls._models[model_id] = model
        cls._metadata[model_id] = metadata
        if set_active or cls._active_model_id is None:
            cls.set_active_model(model_id)
        logger.info(f"Registered ML model '{model_id}' (version: {metadata.model_version}, active={metadata.is_active})")

    @classmethod
    def get_model(cls, model_id: Optional[str] = None) -> Optional[IMLRecommenderModel]:
        """Retrieve model by ID or return current active model."""
        target_id = model_id or cls._active_model_id
        if not target_id:
            return None
        return cls._models.get(target_id)

    @classmethod
    def get_metadata(cls, model_id: Optional[str] = None) -> Optional[ModelMetadata]:
        """Retrieve metadata for a model."""
        target_id = model_id or cls._active_model_id
        if not target_id:
            return None
        return cls._metadata.get(target_id)

    @classmethod
    def set_active_model(cls, model_id: str) -> None:
        """Mark a model as currently active for inference."""
        if model_id not in cls._models:
            raise ModelNotFoundError(f"Model ID '{model_id}' is not registered.")

        # Deactivate all others
        for m_id, meta in cls._metadata.items():
            meta.is_active = (m_id == model_id)

        cls._active_model_id = model_id
        logger.info(f"Active ML recommendation model set to '{model_id}'")

    @classmethod
    def list_models(cls) -> List[ModelMetadata]:
        """List metadata for all registered models."""
        return list(cls._metadata.values())

    @classmethod
    def is_active_model_trained(cls) -> bool:
        """Check whether the active model is trained and ready for inference."""
        active_meta = cls.get_metadata()
        return active_meta is not None and active_meta.is_trained

    @classmethod
    def clear(cls) -> None:
        """Reset registry (useful for testing)."""
        cls._models.clear()
        cls._metadata.clear()
        cls._active_model_id = None


class AIServiceRegistry:
    """Registry for AI services, LLM providers, and feature extractors."""

    _feature_extractor: Optional[IFeatureExtractor] = None
    _llm_providers: Dict[str, ILLMProvider] = {}
    _active_provider_name: str = ai_settings.LLM_PROVIDER

    @classmethod
    def register_feature_extractor(cls, extractor: IFeatureExtractor) -> None:
        """Register the primary feature extractor."""
        cls._feature_extractor = extractor
        logger.info("Registered primary optimization feature extractor")

    @classmethod
    def get_feature_extractor(cls) -> Optional[IFeatureExtractor]:
        """Get the registered feature extractor."""
        return cls._feature_extractor

    @classmethod
    def register_llm_provider(cls, name: str, provider: ILLMProvider) -> None:
        """Register an LLM provider."""
        cls._llm_providers[name] = provider
        logger.info(f"Registered LLM provider: {name}")

    @classmethod
    def get_llm_provider(cls, name: Optional[str] = None) -> Optional[ILLMProvider]:
        """Retrieve the requested or active LLM provider."""
        target = name or cls._active_provider_name
        return cls._llm_providers.get(target)

    @classmethod
    def set_active_llm_provider(cls, name: str) -> None:
        """Set active LLM provider."""
        if name not in cls._llm_providers:
            logger.warning(f"LLM provider '{name}' not found; keeping current provider")
            return
        cls._active_provider_name = name

