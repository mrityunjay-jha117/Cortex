"""
=============================================================================
 __INIT__.PY (vision_components)
=============================================================================
This module is a microservice component for vision_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .screenshotter import ScreenshotterMixin
from .ocr import OCRMixin
from .extraction import VisionExtractionMixin

class VisionBuilders(ScreenshotterMixin, OCRMixin, VisionExtractionMixin):
    pass

__all__ = ["VisionBuilders"]
