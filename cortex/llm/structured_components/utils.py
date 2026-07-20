"""
=============================================================================
 UTILS.PY (structured_components)
=============================================================================
This module is a microservice component for structured_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

import base64
import logging
from io import BytesIO
from typing import Any
from cortex.graph_model import LLMConfig, LLMProvider
from cortex.llm.client import BaseLLMClient, create_client

log = logging.getLogger(__name__)

def _make_client(node: Any, task_type: str, llm_config: LLMConfig) -> BaseLLMClient:
    return create_client(
        provider=LLMProvider.OPENROUTER,
        model=node.model,
        temperature=getattr(node, "temperature", 0.0),
        max_tokens=getattr(node, "max_tokens", 2048),
        timeout=llm_config.request_timeout,
        max_retries=llm_config.max_retries,
        openrouter_api_key_env=llm_config.openrouter_api_key_env,
    )

def _get_images_from_context(node: Any, context: dict[str, Any]) -> list[str] | None:
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
    from PIL import Image
    try:
        img_data = base64.b64decode(b64_data)
        img = Image.open(BytesIO(img_data))
        w, h = img.size
        
        if w <= max_dimension and h <= max_dimension:
            return [b64_data]
            
        log.info("Image too large (%dx%d). Tiling for better extraction...", w, h)
        tiles = []
        
        original_resized = img.copy()
        original_resized.thumbnail((1024, 1024))
        buf = BytesIO()
        original_resized.save(buf, format="PNG")
        tiles.append(base64.b64encode(buf.getvalue()).decode())

        overlap = 100
        for y in range(0, h, max_dimension - overlap):
            for x in range(0, w, max_dimension - overlap):
                box = (x, y, min(x + max_dimension, w), min(y + max_dimension, h))
                tile = img.crop(box)
                buf = BytesIO()
                tile.save(buf, format="PNG")
                tiles.append(base64.b64encode(buf.getvalue()).decode())
                
        log.info("Created %d tiles from large image.", len(tiles))
        return tiles[:10]
    except Exception as exc:
        log.warning("Image tiling failed: %s", exc)
        return [b64_data]

def _capture_region_b64(bbox: tuple[int, int, int, int]) -> str:
    try:
        from PIL import ImageGrab  # type: ignore
        img = ImageGrab.grab(bbox=bbox)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as exc:  # noqa: BLE001
        log.error("Screen capture error: %s", exc)
        return ""
