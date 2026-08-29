from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


class BrowserDriver(ABC):
    """Abstract base class defining the contract for any browser engine."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish a connection to the browser."""

    @abstractmethod
    async def close(self) -> None:
        """Close the browser connection."""

    @abstractmethod
    async def send_message(self, text: str) -> AsyncGenerator[str, None]:
        """Send a message to ChatGPT and yield the streamed response chunks."""

    @abstractmethod
    async def get_memories(self) -> list[dict]:
        """Fetch memories from the backend."""

    @abstractmethod
    async def get_projects(self) -> list[dict]:
        """Fetch projects from the backend."""
