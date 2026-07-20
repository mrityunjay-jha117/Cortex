"""
=============================================================================
 __INIT__.PY (structured_components)
=============================================================================
This module is a microservice component for structured_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .judgment import run_judgment
from .extraction import run_extraction
from .generative import run_generative
from .vision import run_ocr, run_vision_extraction

__all__ = ["run_judgment", "run_extraction", "run_generative", "run_ocr", "run_vision_extraction"]
