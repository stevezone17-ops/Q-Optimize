"""Background worker interface specification for long-running solver jobs."""

from abc import ABC, abstractmethod


class IJobQueue(ABC):
    """Job queue interface for scheduling asynchronous solver experiments."""

    @abstractmethod
    def enqueue_experiment(self, experiment_id: str) -> str:
        raise NotImplementedError("Background job queue is scheduled for Phase 8.")
