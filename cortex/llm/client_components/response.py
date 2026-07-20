"""
=============================================================================
 RESPONSE.PY (client_components)
=============================================================================
This module is a microservice component for client_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from dataclasses import dataclass, field
from typing import Any
from cortex.graph_model import LLMProvider

@dataclass
class LLMResponse:
    text: str
    model: str
    provider: LLMProvider
    prompt_tokens: int = 0
    completion_tokens: int = 0
    raw: dict[str, Any] = field(default_factory=dict)
