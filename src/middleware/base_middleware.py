"""
Base middleware infrastructure for orchestration hooks
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class MiddlewareHook(Enum):
    """Orchestration hook points where middleware can execute"""
    PRE_ARCHITECT = "pre_architect"
    POST_ARCHITECT = "post_architect"
    PRE_CODER = "pre_coder"
    POST_CODER = "post_coder"
    PRE_REVIEWER = "pre_reviewer"
    POST_REVIEWER = "post_reviewer"
    PRE_REFINER = "pre_refiner"
    POST_REFINER = "post_refiner"
    PRE_DOCUMENTER = "pre_documenter"
    POST_DOCUMENTER = "post_documenter"


@dataclass
class MiddlewareContext:
    """Context passed to middleware execution"""
    hook: MiddlewareHook
    stage_name: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseMiddleware(ABC):
    """
    Base class for middleware that can hook into orchestration stages.

    Middleware can:
    - Inspect stage inputs/outputs
    - Run additional processing (evaluation, logging, etc.)
    - Optionally block/gate stage progression
    - Inject additional data into workflow
    """

    def __init__(self, enabled: bool = True):
        """
        Initialize middleware.

        Args:
            enabled: Whether this middleware is active
        """
        self.enabled = enabled

    @abstractmethod
    def execute(self, context: MiddlewareContext) -> Dict[str, Any]:
        """
        Execute middleware logic.

        Args:
            context: Middleware execution context

        Returns:
            Dict with middleware results. Can include:
            - 'passed': bool (whether to allow progression)
            - 'data': dict (additional data to inject)
            - 'metadata': dict (logging/telemetry data)
        """
        pass

    def should_execute(self, hook: MiddlewareHook) -> bool:
        """
        Determine if middleware should run at this hook.

        Args:
            hook: The orchestration hook point

        Returns:
            True if middleware should execute
        """
        return self.enabled and hook in self.get_hooks()

    @abstractmethod
    def get_hooks(self) -> list[MiddlewareHook]:
        """
        Return list of hooks this middleware subscribes to.

        Returns:
            List of MiddlewareHook values
        """
        pass

    def get_name(self) -> str:
        """Get middleware name for logging"""
        return self.__class__.__name__
