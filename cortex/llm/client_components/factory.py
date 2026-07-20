"""
=============================================================================
 FACTORY.PY (client_components)
=============================================================================
This module is a microservice component for client_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from cortex.graph_model import LLMProvider
from .base import BaseLLMClient
from .openrouter import OpenRouterClient

def create_client(
    provider: LLMProvider,
    model: str,
    temperature: float = 0.0,
    max_tokens: int = 1024,
    timeout: float = 30.0,
    max_retries: int = 3,
    openrouter_api_key_env: str = "OPENROUTER_API_KEY",
) -> BaseLLMClient:
    common = dict(model=model, temperature=temperature, max_tokens=max_tokens,
                  timeout=timeout, max_retries=max_retries, provider=provider)
    return OpenRouterClient(api_key_env=openrouter_api_key_env, **common)
