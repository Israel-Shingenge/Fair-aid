from dataclasses import dataclass
from typing import Optional, Protocol

class LLMError(Exception):
    """Any failure to get text from the model (network, 5xx, safety block, bad response)."""

class LLMRateLimited(LLMError):
    def __init__(self, message: str, retry_after: Optional[float] = None, daily: bool = False):
        super().__init__(message)
        self.retry_after = retry_after
        self.daily = daily

class LLMClient(Protocol):
    def generate_json(self, system: str, prompt: str) -> str:
        """Return the model's raw JSON text for ``prompt``. Raises ``LLMError`` / ``LLMRateLimited``."""
