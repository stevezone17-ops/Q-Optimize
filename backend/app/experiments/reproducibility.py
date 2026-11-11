"""Experiment reproducibility, config hashing, and exact re-execution / replay manager."""

from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field

from backend.app.experiments.models import (
    Experiment,
    ExperimentConfiguration,
    ExperimentStatus,
)
from backend.app.experiments.registry import experiment_registry
from backend.app.experiments.experiment_runner import experiment_runner
from backend.app.experiments.experiment_metadata import capture_metadata
from backend.app.experiments.experiment_exceptions import ExperimentNotFoundError


class ReplayMode(str):
    EXACT_CONFIG = "exact_config"
    FIXED_SEED = "fixed_seed"
    APPROXIMATE = "approximate"


class ReplayResult(BaseModel):
    original_experiment_id: str
    replayed_experiment_id: str
    is_exact_match: bool
    reproducibility_hash: str
    original_best_objective: Optional[float] = None
    replayed_best_objective: Optional[float] = None
    relative_difference_pct: Optional[float] = None


class ExperimentReproducibilityManager:
    """Manages experiment provenance, integrity verification, and re-execution replay."""

    def replay_experiment(
        self,
        experiment_id: str,
        preserve_seeds: bool = True,
    ) -> Experiment:
        """
        Re-execute an experiment using identical configuration and stored random seeds.
        Returns the freshly re-executed Experiment instance.
        """
        original: Experiment = experiment_registry.get(experiment_id)

        # Clone configuration
        config_dict = original.configuration.model_dump()
        if not preserve_seeds:
            config_dict["seeds"] = None

        new_config = ExperimentConfiguration.model_validate(config_dict)
        new_metadata = capture_metadata(new_config)

        replayed = Experiment(
            experiment_id=str(uuid.uuid4()),
            name=f"Replay: {original.name}",
            configuration=new_config,
            status=ExperimentStatus.DRAFT,
            metadata=new_metadata,
        )
        experiment_registry.save(replayed)

        # Run synchronously
        executed = experiment_runner.run_experiment(replayed)
        return executed

    def verify_reproducibility(
        self, original_id: str, replayed_id: str
    ) -> ReplayResult:
        """Compare results between original and replayed experiments."""
        orig = experiment_registry.get(original_id)
        rep = experiment_registry.get(replayed_id)

        orig_objs = [r.objective_value for r in orig.results if r.objective_value is not None]
        rep_objs = [r.objective_value for r in rep.results if r.objective_value is not None]

        orig_best = max(orig_objs) if orig_objs else None
        rep_best = max(rep_objs) if rep_objs else None

        is_exact = False
        diff_pct = None

        if orig_best is not None and rep_best is not None:
            if orig_best == rep_best:
                is_exact = True
                diff_pct = 0.0
            elif orig_best != 0:
                diff_pct = abs(rep_best - orig_best) / abs(orig_best) * 100.0

        return ReplayResult(
            original_experiment_id=original_id,
            replayed_experiment_id=replayed_id,
            is_exact_match=is_exact,
            reproducibility_hash=orig.metadata.reproducibility_hash,
            original_best_objective=orig_best,
            replayed_best_objective=rep_best,
            relative_difference_pct=diff_pct,
        )


reproducibility_manager = ExperimentReproducibilityManager()
