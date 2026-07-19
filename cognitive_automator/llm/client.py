"""
client.py — Provider-agnostic LLM client (OpenRouter only).

This file handles all outbound network communication with Large Language Models.
It routes all calls through OpenRouter's OpenAI-compatible endpoint. It handles API key resolution, HTTP session management, schema injection for structured responses, and utilizes the `tenacity` library to provide exponential backoff retries for network resilience.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from cognitive_automator.graph_model import LLMProvider

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class LLMResponse:
    text: str
    model: str
    provider: LLMProvider
    prompt_tokens: int = 0
    completion_tokens: int = 0
    raw: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Base client
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# OpenRouter adapter (OpenAI-compatible, multi-model)
# ---------------------------------------------------------------------------

class OpenRouterClient(BaseLLMClient):
    """Calls OpenRouter's OpenAI-compatible endpoint.

    Uses OPENROUTER_API_KEY from env by default. Passes response_format=json_object
    for structured calls and injects the schema into the system prompt
    for broader model compatibility.
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key_env: str = "OPENROUTER_API_KEY", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            raise ImportError("pip install openai")
        api_key = os.environ.get(api_key_env, "")
        self._client = OpenAI(
            api_key=api_key,
            base_url=self.BASE_URL,
            timeout=self.timeout,
            default_headers={"X-Title": "Cognitive Automator"},
        )

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def complete(
        self,
        user_prompt: str,
        system_prompt: str = "",
        response_schema: dict[str, Any] | None = None,
        images_b64: list[str] | None = None,
    ) -> LLMResponse:
        import json as _json

        messages: list[dict[str, Any]] = []

        # When a schema is requested, inject it into the system prompt for
        # compatibility with models that don't support strict JSON schema.
        effective_system = system_prompt
        if response_schema:
            schema_hint = (
                "\n\nYou MUST respond with valid JSON that matches this schema exactly:\n"
                + _json.dumps(response_schema, indent=2)
            )
            effective_system = (effective_system or "") + schema_hint

        if effective_system:
            messages.append({"role": "system", "content": effective_system})

        if images_b64:
            user_content: list[dict[str, Any]] = []
            # Text first is often more reliable
            user_content.append({"type": "text", "text": user_prompt})
            for img in images_b64:
                user_content.append({
                    "type": "image_url", 
                    "image_url": {
                        "url": f"data:image/png;base64,{img}",
                        "detail": "high"
                    }
                })
            messages.append({"role": "user", "content": user_content})
        else:
            messages.append({"role": "user", "content": user_prompt})

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        # if response_schema:
        #     kwargs["response_format"] = {"type": "json_object"}

        response = self._client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content or ""
        log.debug("OpenRouter response: %s", content[:200])

        return LLMResponse(
            text=content,
            model=self.model,
            provider=self.provider,
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            raw=response.model_dump(),
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_client(
    provider: LLMProvider,
    model: str,
    temperature: float = 0.0,
    max_tokens: int = 1024,
    timeout: float = 30.0,
    max_retries: int = 3,
    openrouter_api_key_env: str = "OPENROUTER_API_KEY",
) -> BaseLLMClient:
    """Always returns an OpenRouterClient."""
    common = dict(model=model, temperature=temperature, max_tokens=max_tokens,
                  timeout=timeout, max_retries=max_retries, provider=provider)
    return OpenRouterClient(api_key_env=openrouter_api_key_env, **common)
