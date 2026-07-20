"""
=============================================================================
 STRUCTURED LLM OUTPUTS
=============================================================================
This module ensures that LLM responses adhere to strict JSON formats.
It handles schema validation and parses raw text into programmatic data structures.

Key Features:
1. Injects JSON-forcing instructions into prompts.
2. Validates AI outputs against Pydantic models to prevent runtime crashes.

Think of this module as the strict schoolteacher grading the AI's homework.
=============================================================================
"""

from .structured_components import run_judgment, run_extraction, run_generative, run_ocr, run_vision_extraction

__all__ = ["run_judgment", "run_extraction", "run_generative", "run_ocr", "run_vision_extraction"]
