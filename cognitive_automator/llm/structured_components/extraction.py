"""
=============================================================================
 EXTRACTION.PY (structured_components)
=============================================================================
This module is a microservice component for structured_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

import json
import logging
import os
import re
from typing import Any
from cognitive_automator.graph_model import LLMExtractionNode, LLMConfig
from cognitive_automator.llm.templates import render_prompt
from .utils import _make_client, _get_images_from_context

log = logging.getLogger(__name__)

def run_extraction(
    node: LLMExtractionNode,
    context: dict[str, Any],
    llm_config: LLMConfig,
) -> dict[str, Any]:
    client = _make_client(node, "extraction", llm_config)
    prompt = render_prompt(node.prompt_template, context)
    images = _get_images_from_context(node, context)
    
    log.info("--- LLM EXTRACTION START ---")
    log.info("Node ID: %s", node.id)

    if os.environ.get("DEBUG_COG_LLM"):
        log.info("USER PROMPT:\n%s", prompt)

    log.info("--- RENDERED PROMPT (TRUNCATED) ---")
    log.info("%s...", prompt[:500])
    log.info("-----------------------------------")
    
    response = client.complete(
        user_prompt=prompt,
        system_prompt=node.system_prompt,
        response_schema=node.output_schema or None,
        images_b64=images,
    )
    
    log.info("Raw Response Received (first 200 chars): %s", response.text[:200])
    log.info("--- LLM EXTRACTION END ---")

    try:
        text = response.text.strip()
        if text.startswith("```"):
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM extraction did not return valid JSON: {response.text[:200]}") from exc
