"""
=============================================================================
 __INIT__.PY (screen_region_selector_components)
=============================================================================
This module is a microservice component for screen_region_selector_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .geometry import GeometryMixin
from .paint import PaintMixin
from .mouse import MouseMixin
from .keyboard import KeyboardMixin

__all__ = ["GeometryMixin", "PaintMixin", "MouseMixin", "KeyboardMixin"]
