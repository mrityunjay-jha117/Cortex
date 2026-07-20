"""
=============================================================================
 __INIT__.PY (client_components)
=============================================================================
This module is a microservice component for client_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .response import LLMResponse
from .base import BaseLLMClient
from .openrouter import OpenRouterClient
from .factory import create_client

__all__ = ["LLMResponse", "BaseLLMClient", "OpenRouterClient", "create_client"]
