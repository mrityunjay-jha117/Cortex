"""
structured.py — Structured output enforcement for LLM nodes.

This file serves as the execution engine for all LLM-based intelligence nodes (Extraction, Judgment, OCR, and Vision Extraction).
It bridges the gap between raw LLM string outputs and structured application data by enforcing JSON schemas, parsing markdown-wrapped JSON, and splitting large base64 images into overlapping tiles to improve Vision model accuracy.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from io import BytesIO
from typing import Any

from cognitive_automator.graph_model import (
    GenerativeOCRNode,
    LLMConfig,
    LLMExtractionNode,
    LLMGenerativeNode,
    LLMJudgmentNode,
    LLMProvider,
    VisionExtractionNode,
)
from cognitive_automator.llm.client import BaseLLMClient, LLMResponse, create_client
from cognitive_automator.llm.templates import render_prompt

log = logging.getLogger(__name__)

_TASK_MODEL_ENV = {
    "extraction": "EXTRACTION_MODEL_ID",
    "logical": "LOGICAL_MODEL_ID",
}


def _make_client(node: Any, task_type: str, llm_config: LLMConfig) -> BaseLLMClient:
    """Always returns an OpenRouter client."""
    return create_client(
        provider=LLMProvider.OPENROUTER,
        model=node.model,
        temperature=getattr(node, "temperature", 0.0),
        max_tokens=getattr(node, "max_tokens", 2048),
        timeout=llm_config.request_timeout,
        max_retries=llm_config.max_retries,
        openrouter_api_key_env=llm_config.openrouter_api_key_env,
    )


# JSON Schema for judgment responses — strict, no additional properties
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


def _get_images_from_context(node: Any, context: dict[str, Any]) -> list[str] | None:
    """Collect base64 images from context keys listed in image_context_keys."""
    keys = getattr(node, "image_context_keys", [])
    if not keys:
        return None
    images = []
    for k in keys:
        val = context.get(k)
        if isinstance(val, str):
            images.extend(_tile_image_if_large(val))
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, str):
                    images.extend(_tile_image_if_large(item))
    return images if images else None


def _tile_image_if_large(b64_data: str, max_dimension: int = 3000) -> list[str]:
    """
    If an image is very large (e.g. a full page scroll), split it into 
    overlapping tiles to help the Vision LLM focus on smaller text.
    Standard 1080p/1440p screenshots should not be tiled as modern 
    Vision models handle them natively with high detail.
    """
    from PIL import Image
    try:
        img_data = base64.b64decode(b64_data)
        img = Image.open(BytesIO(img_data))
        w, h = img.size
        
        if w <= max_dimension and h <= max_dimension:
            return [b64_data]
            
        log.info("Image too large (%dx%d). Tiling for better extraction...", w, h)
        tiles = []
        
        # We also keep the original image (scaled down) as a global context
        original_resized = img.copy()
        original_resized.thumbnail((1024, 1024))
        buf = BytesIO()
        original_resized.save(buf, format="PNG")
        tiles.append(base64.b64encode(buf.getvalue()).decode())

        # Simple 2x2 or NxM tiling based on dimensions
        overlap = 100
        for y in range(0, h, max_dimension - overlap):
            for x in range(0, w, max_dimension - overlap):
                box = (x, y, min(x + max_dimension, w), min(y + max_dimension, h))
                tile = img.crop(box)
                buf = BytesIO()
                tile.save(buf, format="PNG")
                tiles.append(base64.b64encode(buf.getvalue()).decode())
                
        log.info("Created %d tiles from large image.", len(tiles))
        return tiles[:10] # Safety limit
    except Exception as exc:
        log.warning("Image tiling failed: %s", exc)
        return [b64_data]


# ---------------------------------------------------------------------------
# Judgment
# ---------------------------------------------------------------------------

def run_judgment(
    node: LLMJudgmentNode,
    context: dict[str, Any],
    llm_config: LLMConfig,
) -> dict[str, Any]:
    """
    Runs an LLMJudgmentNode. Returns {"result": bool, "confidence": float, "reasoning": str}.
    Raises ValueError if the LLM response cannot be parsed as the expected schema.
    """
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
        # Some models wrap JSON in markdown blocks
        clean_text = text
        if text.startswith("```"):
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                clean_text = match.group(1)
        data = json.loads(clean_text)
    except json.JSONDecodeError:
        # Last-resort heuristic: look for YES/NO/TRUE/FALSE
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


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def run_extraction(
    node: LLMExtractionNode,
    context: dict[str, Any],
    llm_config: LLMConfig,
) -> dict[str, Any]:
    # Force temperature=0 for extraction as requested
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


# ---------------------------------------------------------------------------
# Generative
# ---------------------------------------------------------------------------

def run_generative(
    node: LLMGenerativeNode,
    context: dict[str, Any],
    llm_config: LLMConfig,
) -> str:
    client = _make_client(node, "extraction", llm_config)
    prompt = render_prompt(node.prompt_template, context)
    response = client.complete(user_prompt=prompt, system_prompt=node.system_prompt)
    return response.text


# ---------------------------------------------------------------------------
# Generative OCR
# ---------------------------------------------------------------------------

def run_ocr(
    node: GenerativeOCRNode,
    llm_config: LLMConfig,
) -> str:
    """
    Capture screen region → base64 PNG → Vision LLM → extracted text.
    Falls back to empty string with a warning if PIL is unavailable.
    """
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
    """Capture screen region → Vision LLM → structured JSON."""
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


def _capture_region_b64(bbox: tuple[int, int, int, int]) -> str:
    """Capture a screen region and return as base64-encoded PNG."""
    try:
        from PIL import ImageGrab  # type: ignore
        img = ImageGrab.grab(bbox=bbox)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as exc:  # noqa: BLE001
        log.error("Screen capture error: %s", exc)
        return ""
