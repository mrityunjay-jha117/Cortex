"""
=============================================================================
 LOCATE_FALLBACK.PY (vision_components)
=============================================================================
This module is a microservice component for vision_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .base import *

def run_vlm_fallback(img_b64: str, prompt: str,
                     provider: LLMProvider, model: str, config: LLMConfig) -> dict[str, tuple[float, float]] | None:
    from cortex.llm.client import create_client
    import json
    import re

    system_prompt = (
        "You are an expert UI automation assistant. Your task is to locate elements on a screen and determine the exact click point for interaction.\n"
        "When asked to find an element, return a JSON list of objects containing:\n"
        "- \"bbox_2d\": [ymin, xmin, ymax, xmax] (normalized 0-1000)\n"
        "- \"point\": [y, x] (normalized 0-1000) - The EXACT point to click for interaction. Usually the center, but adjust if the description implies a specific part.\n"
        "- \"label\": element description.\n"
        "Example: [{\"bbox_2d\": [100, 200, 300, 400], \"point\": [200, 300], \"label\": \"login button\"}]"
    )

    client = create_client(
        provider=provider,
        model=model,
        temperature=0.0,
        max_tokens=512,
        timeout=config.request_timeout,
        openrouter_api_key_env=config.openrouter_api_key_env,
    )

    response = client.complete(
        user_prompt=f"Task: {prompt}\nReturn the bounding box and exact click point for this element.",
        system_prompt=system_prompt,
        images_b64=[img_b64]
    )

    text = response.text.strip()
    log.debug("VLM Fallback Raw Response: %s", text)

    if "```" in text:
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            text = match.group(1)

    try:
        data = json.loads(text)
        if not isinstance(data, list) or len(data) == 0:
            return None
        
        item = data[0]
        point = item.get("point")
        bbox = item.get("bbox_2d")

        if not bbox or len(bbox) != 4:
            return None
            
        xmin, ymin, xmax, ymax = bbox
        cx_norm = (xmin + xmax) / 2.0
        cy_norm = (ymin + ymax) / 2.0

        if point and len(point) == 2:
            px_norm, py_norm = point
            click_pt = (float(px_norm), float(py_norm))
        else:
            click_pt = (float(cx_norm), float(cy_norm))
            
        return {
            "click": click_pt,
            "center": (float(cx_norm), float(cy_norm)),
            "bbox_raw": (float(xmin), float(ymin), float(xmax), float(ymax))
        }
    except Exception as e:
        log.error("Failed to parse VLM fallback response: %s", e)
        return None
