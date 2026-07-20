"""
=============================================================================
 COMPUTER VISION NODES
=============================================================================
This module defines nodes that process visual information.
It models screenshot capture, image matching, and OCR tasks.

Key Features:
1. Defines properties for regions of interest and confidence thresholds.
2. Provides schema for nodes that "see" the screen.

Think of this module as the digital eyes of Cortex.
=============================================================================
"""

from typing import Literal, Any
from pydantic import BaseModel, Field
from .enums import NodeCategory, LLMProvider, MouseAction
from .base import BaseNode

class LocateElementNode(BaseNode):
    category: Literal[NodeCategory.VISION] = NodeCategory.VISION
    reference_image_b64: str = ""
    confidence: float = 0.75
    grayscale: bool = False
    region: tuple[int, int, int, int] | None = None
    timeout_seconds: float = 10.0
    find_all: bool = False
    x_offset: int = 0
    y_offset: int = 0
    x_coord: int | None = None
    y_coord: int | None = None
    use_fallback: bool = False
    auto_heal: bool = False
    fallback_prompt: str = ""
    fallback_provider_override: LLMProvider | None = None
    fallback_model_override: str | None = None
    output_key: str = "located_xy"

class LocateAndClickNode(LocateElementNode):
    action: MouseAction = MouseAction.CLICK
    button: str = "left"
    duration: float = 0.0
    wait_after_click: float = 0.3

class VisionImageNode(BaseNode):
    category: Literal[NodeCategory.VISION] = NodeCategory.VISION
    file_path: str = ""
    output_key: str = "loaded_image"

class GenerativeOCRNode(BaseNode):
    category: Literal[NodeCategory.VISION] = NodeCategory.VISION
    bbox: tuple[int, int, int, int] = (0, 0, 100, 100)
    system_prompt: str = "Extract all text exactly as displayed on screen. Return raw text only, no commentary."
    provider: LLMProvider = LLMProvider.OPENROUTER
    model: str = "openai/gpt-4o"
    output_key: str = "ocr_text"

class VisionExtractionNode(BaseNode):
    category: Literal[NodeCategory.VISION] = NodeCategory.VISION
    bbox: tuple[int, int, int, int] = (0, 0, 100, 100)
    prompt_template: str = "Extract the table from this image."
    system_prompt: str = "You are a precise data extraction assistant. Extract the requested information as valid JSON only."
    output_schema: dict[str, Any] = Field(default_factory=dict)
    provider: LLMProvider = LLMProvider.OPENROUTER
    model: str = "qwen/qwen-2-vl-72b-instruct"
    temperature: float = 0.0
    max_tokens: int = 2048
    output_key: str = "vision_data"
