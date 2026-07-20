"""
=============================================================================
 OPENROUTER.PY (client_components)
=============================================================================
This module is a microservice component for client_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

import logging
import os
from typing import Any
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .base import BaseLLMClient
from .response import LLMResponse

log = logging.getLogger(__name__)

class OpenRouterClient(BaseLLMClient):
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
            default_headers={"X-Title": "Cortex"},
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
