"""
=============================================================================
 JUDGMENT.PY (structured_components)
=============================================================================
This module is a microservice component for structured_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

import json
import re
from typing import Any
from cognitive_automator.graph_model import LLMJudgmentNode, LLMConfig
from cognitive_automator.llm.client import LLMResponse
from cognitive_automator.llm.templates import render_prompt
from .utils import _make_client, _get_images_from_context

JUDGMENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "result": {"type": "boolean"},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "reasoning": {"type": "string"},
    },
    "required": ["result", "confidence", "reasoning"],
    "additionalProperties": False,
}

def run_judgment(
    node: LLMJudgmentNode,
    context: dict[str, Any],
    llm_config: LLMConfig,
) -> dict[str, Any]:
    client = _make_client(node, "logical", llm_config)
    prompt = render_prompt(node.prompt_template, context)
    images = _get_images_from_context(node, context)
    response: LLMResponse = client.complete(
        user_prompt=prompt,
        system_prompt=node.system_prompt,
        response_schema=JUDGMENT_SCHEMA,
        images_b64=images,
    )
    return _parse_judgment(response.text)

def _parse_judgment(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        clean_text = text
        if text.startswith("```"):
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                clean_text = match.group(1)
        data = json.loads(clean_text)
    except json.JSONDecodeError:
        upper = text.upper()
        if re.search(r'\bYES\b|\bTRUE\b', upper):
            return {"result": True, "confidence": 0.5, "reasoning": text}
        if re.search(r'\bNO\b|\bFALSE\b', upper):
            return {"result": False, "confidence": 0.5, "reasoning": text}
        raise ValueError(f"LLM judgment response is not valid JSON and cannot be parsed: {text[:200]}")

    if "result" not in data:
        raise ValueError(f"LLM judgment missing 'result' key. Got: {data}")
    data["result"] = bool(data["result"])
    data.setdefault("confidence", 1.0)
    data.setdefault("reasoning", "")
    return data
