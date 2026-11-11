"""Simple async experiment scheduler — submits experiments to background threads."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from backend.app.experiments.models import Experiment, ExperimentStatus
from backend.app.experiments.registry import experiment_registry
from backend.app.experiments.experiment_runner import experiment_runner
from backend.app.experiments.experiment_status import validate_transition
from backend.app.core.logging import logger

_scheduler_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="exp-scheduler")


async def schedule_experiment(experiment: Experiment) -> Experiment:
    """
    Enqueue an experiment for async execution in the thread pool.
    Returns the experiment immediately in QUEUED state;
    the actual run proceeds in the background.
    """
    # Transition: DRAFT → VALIDATING → QUEUED
    if experiment.status == ExperimentStatus.DRAFT:
        validate_transition(experiment.status, ExperimentStatus.VALIDATING)
        experiment.status = ExperimentStatus.VALIDATING
        experiment_registry.update(experiment)

    validate_transition(experiment.status, ExperimentStatus.QUEUED)
    experiment.status = ExperimentStatus.QUEUED
    experiment_registry.update(experiment)
    logger.info(f"Scheduled experiment '{experiment.experiment_id}'")

    loop = asyncio.get_event_loop()
    loop.run_in_executor(_scheduler_executor, _execute_sync, experiment.experiment_id)
    return experiment


def _execute_sync(experiment_id: str) -> None:
    """Synchronous wrapper called from the thread pool."""
    try:
        experiment = experiment_registry.get(experiment_id)
        logger.info(f"Executing experiment '{experiment_id}' in thread pool")
        experiment_runner.run_experiment(experiment)
        logger.info(f"Experiment '{experiment_id}' finished with status '{experiment.status}'")
    except Exception as exc:
        logger.error(f"Experiment '{experiment_id}' crashed: {exc}", exc_info=True)
        try:
            exp = experiment_registry.get(experiment_id)
            exp.status = ExperimentStatus.FAILED
            exp.error_message = str(exc)
            experiment_registry.update(exp)
        except Exception:
            pass
