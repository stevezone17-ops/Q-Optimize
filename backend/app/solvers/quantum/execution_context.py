"""Execution context, resource monitoring, and cooperative cancellation for quantum workflows."""

import time
import threading
from typing import Optional
from backend.app.solvers.quantum.exceptions import ExecutionTimeoutError, CancellationError


class QuantumExecutionContext:
    """Thread-safe context managing runtime limits, cancellation tokens, and timers."""

    def __init__(
        self,
        time_limit_seconds: float = 60.0,
        cancellation_token: Optional[threading.Event] = None
    ):
        self.time_limit_seconds = time_limit_seconds
        self.cancellation_token = cancellation_token or threading.Event()
        self.start_time: float = time.perf_counter()
        self._eval_count: int = 0

    @property
    def elapsed_seconds(self) -> float:
        return time.perf_counter() - self.start_time

    @property
    def eval_count(self) -> int:
        return self._eval_count

    def record_evaluation(self) -> int:
        self._eval_count += 1
        return self._eval_count

    def check_status(self) -> None:
        """Verify whether execution should continue or abort immediately."""
        if self.cancellation_token.is_set():
            raise CancellationError("Quantum optimization was cancelled by user request.")
        
        if self.elapsed_seconds > self.time_limit_seconds:
            raise ExecutionTimeoutError(
                f"Quantum execution timed out after {self.elapsed_seconds:.2f}s "
                f"(limit: {self.time_limit_seconds:.1f}s)."
            )

    def cancel(self) -> None:
        """Trigger cooperative cancellation."""
        self.cancellation_token.set()
