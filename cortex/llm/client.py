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

__all__ =  .......
Ye karta kya hai?
Python package ke bahar se koi likhe
from llm_client import *
To Python ko kaise pata chalega kya import karna hai?
Isi liye
__all__
batata hai package ki public cheeze kya hain.
=============================================================================
"""

from .client_components import LLMResponse, BaseLLMClient, OpenRouterClient, create_client
__all__ = ["LLMResponse", "BaseLLMClient", "OpenRouterClient", "create_client"]
