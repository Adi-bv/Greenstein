from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseTool(ABC):
    """Abstract base class for all tools that an agent can use."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A description of what the tool does, used by the master agent to decide when to use it."""
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """
        Executes the tool's logic.

        Args:
            **kwargs: The arguments required by the tool, which will vary.

        Returns:
            The result of the tool's execution.
        """
        pass
