"""
=============================================================================
 VISION.PY (structured_components)
=============================================================================
This module is a microservice component for structured_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

import json
import logging
import re
from typing import Any
from cognitive_automator.graph_model import GenerativeOCRNode, VisionExtractionNode, LLMConfig
from cognitive_automator.llm.templates import render_prompt
from .utils import _make_client, _capture_region_b64

log = logging.getLogger(__name__)

def run_ocr(
    node: GenerativeOCRNode,
    llm_config: LLMConfig,
) -> str:
    image_b64 = _capture_region_b64(node.bbox)
    if not image_b64:
        log.warning("Screen capture failed for bbox %s; returning empty OCR text.", node.bbox)
        return ""

    client = _make_client(node, "extraction", llm_config)
    response = client.complete(
        user_prompt="Extract all visible text from this screen capture.",
        system_prompt=node.system_prompt,
        images_b64=[image_b64],
    )
    return response.text.strip()

def run_vision_extraction(
    node: VisionExtractionNode,
    context: dict[str, Any],
    llm_config: LLMConfig,
) -> dict[str, Any]:
    image_b64 = _capture_region_b64(node.bbox)
    if not image_b64:
        raise ValueError(f"Screen capture failed for bbox {node.bbox}")

    client = _make_client(node, "extraction", llm_config)
    prompt = render_prompt(node.prompt_template, context)
    
    response = client.complete(
        user_prompt=prompt,
        system_prompt=node.system_prompt,
        images_b64=[image_b64],
        response_schema=node.output_schema or None,
    )
    try:
        text = response.text.strip()
        if text.startswith("```"):
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Vision extraction did not return valid JSON: {response.text[:200]}") from exc
