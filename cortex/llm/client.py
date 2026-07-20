"""
=============================================================================
 LLM CLIENT
=============================================================================
This module implements the HTTP clients used to communicate with AI providers.
It manages API keys, network requests, and handles timeouts or retries.

Key Features:
1. Translates internal prompt structures into provider-specific API payloads.
2. Handles asynchronous network requests to OpenAI, Anthropic, or OpenRouter.

Think of this module as the diplomat negotiating with foreign AI servers.
=============================================================================
"""

from .client_components import LLMResponse, BaseLLMClient, OpenRouterClient, create_client

__all__ = ["LLMResponse", "BaseLLMClient", "OpenRouterClient", "create_client"]
