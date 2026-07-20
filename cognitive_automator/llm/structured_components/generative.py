"""
=============================================================================
 GENERATIVE.PY (structured_components)
=============================================================================
This module is a microservice component for structured_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from typing import Any
from cognitive_automator.graph_model import LLMGenerativeNode, LLMConfig
from cognitive_automator.llm.templates import render_prompt
from .utils import _make_client

def run_generative(
    node: LLMGenerativeNode,
    context: dict[str, Any],
    llm_config: LLMConfig,
) -> str:
    client = _make_client(node, "extraction", llm_config)
    prompt = render_prompt(node.prompt_template, context)
    response = client.complete(user_prompt=prompt, system_prompt=node.system_prompt)
    return response.text
