from abc import ABC, abstractmethod

from src.storage.models import PipelineState


class PipelineOrchestrator(ABC):
    """Abstract interface for pipeline orchestration. Implementations are swappable."""

    @abstractmethod
    async def invoke(self, state: PipelineState) -> PipelineState:
        """Execute the full agent pipeline and return final state."""
        ...
