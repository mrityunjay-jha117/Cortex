"""
=============================================================================
 VISION EXECUTOR
=============================================================================
This module runs computer vision tasks on captured images.
It handles template matching to find buttons or icons on the screen.

Key Features:
1. Uses OpenCV to locate images within a larger screenshot.
2. Returns coordinates that can be passed to physical mouse nodes.

Think of this module as the detective looking for clues in a photograph.
=============================================================================
"""

from .vision_components import (
    execute_locate_element, run_vlm_fallback, execute_locate_and_click, 
    execute_vision_image, execute_generative_ocr, execute_vision_extraction
)

__all__ = ["execute_locate_element", "run_vlm_fallback", "execute_locate_and_click", 
           "execute_vision_image", "execute_generative_ocr", "execute_vision_extraction"]
