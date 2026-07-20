"""
=============================================================================
 __INIT__.PY (vision_components)
=============================================================================
This module is a microservice component for vision_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .locate_core import execute_locate_element
from .locate_fallback import run_vlm_fallback
from .locate_click import execute_locate_and_click
from .vision_image import execute_vision_image
from .ocr import execute_generative_ocr
from .extraction import execute_vision_extraction

__all__ = ["execute_locate_element", "run_vlm_fallback", "execute_locate_and_click", 
           "execute_vision_image", "execute_generative_ocr", "execute_vision_extraction"]
