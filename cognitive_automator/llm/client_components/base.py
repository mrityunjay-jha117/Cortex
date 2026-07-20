"""
=============================================================================
 BASE.PY (client_components)
=============================================================================
This module is a microservice component for client_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from abc import ABC, abstractmethod
from typing import Any
from cognitive_automator.graph_model import LLMProvider
from .response import LLMResponse

class BaseLLMClient(ABC):
    def __init__(self, model: str, temperature: float, max_tokens: int,
                 timeout: float, max_retries: int, provider: LLMProvider) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.provider = provider

    @abstractmethod
    def complete(
        self,
        user_prompt: str,
        system_prompt: str = "",
        response_schema: dict[str, Any] | None = None,
        images_b64: list[str] | None = None,
    ) -> LLMResponse:
        ...
