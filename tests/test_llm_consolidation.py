"""
tests/test_llm_consolidation.py — Verifies that all LLM calls route through OpenRouter.
"""

from __future__ import annotations

import pytest
from cognitive_automator.graph_model import LLMProvider, LLMConfig
from cognitive_automator.llm.client import create_client, OpenRouterClient
from cognitive_automator.llm.structured import _make_client

def test_llm_provider_enum_is_simplified() -> None:
    # Ensure ONLY OpenRouter is present
    assert len(LLMProvider) == 1
    assert LLMProvider.OPENROUTER == "openrouter"

def test_llm_config_defaults_to_openrouter() -> None:
    config = LLMConfig()
    assert config.default_provider == LLMProvider.OPENROUTER
    assert config.openrouter_api_key_env == "OPENROUTER_API_KEY"
    # Ensure old keys are gone (Pydantic will not have them)
    assert not hasattr(config, "openai_api_key_env")
    assert not hasattr(config, "ollama_base_url")

def test_create_client_always_returns_openrouter(monkeypatch: pytest.MonkeyPatch) -> None:
    # Mock OpenRouterClient.__init__ to avoid needing an API key or openai lib
    monkeypatch.setattr(OpenRouterClient, "__init__", lambda *args, **kwargs: None)
    
    # Even if we pass something (though we can only pass LLMProvider.OPENROUTER now)
    client = create_client(
        provider=LLMProvider.OPENROUTER,
        model="openai/gpt-4o",
    )
    assert isinstance(client, OpenRouterClient)

def test_make_client_uses_openrouter_and_node_model() -> None:
    class MockNode:
        provider = LLMProvider.OPENROUTER
        model = "anthropic/claude-3"
        temperature = 0.5
        max_tokens = 512

    config = LLMConfig()
    # Mock create_client to verify parameters
    received_params = {}
    def mock_create_client(**kwargs):
        received_params.update(kwargs)
        return "mock_client"

    import cognitive_automator.llm.structured as structured
    
    # We use a more direct approach since _make_client calls create_client
    # which is imported into structured.py
    
    original_create_client = structured.create_client
    structured.create_client = mock_create_client
    try:
        _make_client(MockNode(), "extraction", config)
        assert received_params["provider"] == LLMProvider.OPENROUTER
        assert received_params["model"] == "anthropic/claude-3"
        assert received_params["temperature"] == 0.5
    finally:
        structured.create_client = original_create_client
