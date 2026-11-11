"""Reproducibility metadata capture for experiments."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from typing import Any, Dict

from backend.app.experiments.models import ExperimentConfiguration, ExperimentMetadata


def _safe_version(module_name: str) -> str:
    try:
        import importlib.metadata
        return importlib.metadata.version(module_name)
    except Exception:
        return "unknown"


def capture_metadata(configuration: ExperimentConfiguration) -> ExperimentMetadata:
    """Capture system and library versions for reproducibility."""
    return ExperimentMetadata(
        python_version=sys.version,
        platform=platform.platform(),
        qiskit_version=_safe_version("qiskit"),
        numpy_version=_safe_version("numpy"),
        scipy_version=_safe_version("scipy"),
        reproducibility_hash=compute_config_hash(configuration),
    )


def compute_config_hash(configuration: ExperimentConfiguration) -> str:
    """Compute a stable SHA-256 hash of the experiment configuration for reproducibility."""
    config_dict: Dict[str, Any] = {
        "problem_type": configuration.problem_type,
        "problem_instance": _canonical(configuration.problem_instance),
        "algorithms": sorted(a.value for a in configuration.algorithms),
        "num_trials": configuration.num_trials,
        "seeds": sorted(configuration.seeds) if configuration.seeds else None,
        "resource_budget": configuration.resource_budget.model_dump(),
        "algorithm_configs": {
            k: _canonical(v) for k, v in sorted(configuration.algorithm_configs.items())
        },
    }
    serialized = json.dumps(config_dict, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


def _canonical(obj: Any) -> Any:
    """Recursively sort dicts by key so hashing is order-independent."""
    if isinstance(obj, dict):
        return {k: _canonical(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [_canonical(i) for i in obj]
    return obj
