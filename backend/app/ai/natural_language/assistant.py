"""Natural Language Optimization Assistant coordinating parsing, entity extraction, and Phase 2 validation."""

from typing import Dict, Any, List, Optional

from backend.app.domain.problems.models import ProblemType, ValidationStatus
from backend.app.ai.models import ProblemDraftProposal
from backend.app.ai.natural_language.provider import (
    ILLMProvider,
    DeterministicFallbackParser,
    GeminiLLMProvider,
    MockLLMProvider,
)
from backend.app.ai.registry import AIServiceRegistry
from backend.app.ai.exceptions import NaturalLanguageParsingError
from backend.app.services.problem_service import ProblemService
from backend.app.ai.config import ai_settings
from backend.app.core.logging import logger


class NaturalLanguageAssistant:
    """
    Intelligent assistant translating ordinary language descriptions into
    mathematically verified canonical problem draft proposals.
    """

    def __init__(self, default_provider: Optional[ILLMProvider] = None):
        self._fallback_provider = DeterministicFallbackParser()
        self._provider = default_provider or GeminiLLMProvider()

    async def parse_problem_description(
        self,
        text: str,
        problem_type_hint: Optional[ProblemType] = None,
        provider_name: Optional[str] = None,
    ) -> ProblemDraftProposal:
        """
        Convert ordinary language description into a structured, validated problem draft.
        Never bypasses Phase 2 mathematical validation.
        """
        # 1. Input validation & sanitization
        clean_text = text.strip() if text else ""
        if len(clean_text) < 5:
            raise NaturalLanguageParsingError("Problem description is too short. Please provide at least 5 characters.")

        if len(clean_text) > ai_settings.LLM_MAX_INPUT_LENGTH:
            raise NaturalLanguageParsingError(
                f"Problem description exceeds maximum input length of {ai_settings.LLM_MAX_INPUT_LENGTH} characters."
            )

        # 2. Select provider
        provider = self._select_provider(provider_name)

        # 3. Generate structured draft proposal
        logger.info(f"Parsing natural language description using provider '{provider.provider_name}'")
        raw_draft = await provider.generate_draft(clean_text, problem_type_hint=problem_type_hint)

        is_supported = raw_draft.get("is_supported", True)
        raw_prob_type = raw_draft.get("problem_type")

        prob_type: Optional[ProblemType] = None
        if raw_prob_type:
            if isinstance(raw_prob_type, ProblemType):
                prob_type = raw_prob_type
            else:
                try:
                    prob_type = ProblemType(str(raw_prob_type).lower())
                except ValueError:
                    prob_type = None

        suggested_instance = raw_draft.get("suggested_instance") or {}

        # 4. Independent Phase 2 mathematical validation
        validation_status = "NOT_VALIDATED"
        is_math_valid = False
        validation_issues: List[str] = []

        if is_supported and prob_type and suggested_instance:
            try:
                val_res = ProblemService.validate_problem_definition(prob_type, suggested_instance)
                is_math_valid = val_res.is_valid
                validation_status = val_res.status.value
                validation_issues = val_res.issues
                logger.info(f"Phase 2 validation check for draft: valid={is_math_valid}, status={validation_status}")
            except Exception as val_err:
                validation_status = "INVALID"
                is_math_valid = False
                validation_issues.append(f"Phase 2 validation error: {str(val_err)}")

        return ProblemDraftProposal(
            problem_type=prob_type,
            is_supported=is_supported,
            name=raw_draft.get("title") or "Proposed Problem Draft",
            description=raw_draft.get("description") or clean_text[:120],
            entities=raw_draft.get("entities") or {},
            objective=raw_draft.get("objective") or {},
            constraints=raw_draft.get("constraints") or [],
            suggested_instance=suggested_instance,
            missing_information=raw_draft.get("missing_information") or [],
            assumptions=raw_draft.get("assumptions") or [],
            confidence_score=float(raw_draft.get("confidence_score", 0.85)),
            is_mathematically_valid=is_math_valid,
            validation_status=validation_status,
            validation_issues=validation_issues,
            requires_user_confirmation=True,
            provider_used=provider.provider_name,
        )

    def _select_provider(self, requested_name: Optional[str]) -> ILLMProvider:
        """Select appropriate LLM or fallback provider."""
        if requested_name:
            reg_provider = AIServiceRegistry.get_llm_provider(requested_name)
            if reg_provider and reg_provider.is_available():
                return reg_provider

        if self._provider.is_available():
            return self._provider

        return self._fallback_provider


default_nl_assistant = NaturalLanguageAssistant()
AIServiceRegistry.register_llm_provider("gemini", GeminiLLMProvider())
AIServiceRegistry.register_llm_provider("deterministic_fallback", DeterministicFallbackParser())

