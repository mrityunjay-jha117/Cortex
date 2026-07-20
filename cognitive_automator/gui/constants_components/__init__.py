"""
=============================================================================
 __INIT__.PY (constants_components)
=============================================================================
This module is a microservice component for constants_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .colors import APP_BG, APP_SURFACE, APP_SURFACE2, APP_BORDER, APP_TEXT, APP_TEXT_DIM, APP_ACCENT, APP_SUCCESS, APP_WARNING, APP_ERROR
from .nodes import NODE_COLORS, NODE_CATEGORY_LABELS
from .stylesheet import MAIN_STYLESHEET

__all__ = [
    "APP_BG", "APP_SURFACE", "APP_SURFACE2", "APP_BORDER", "APP_TEXT", "APP_TEXT_DIM",
    "APP_ACCENT", "APP_SUCCESS", "APP_WARNING", "APP_ERROR",
    "NODE_COLORS", "NODE_CATEGORY_LABELS",
    "MAIN_STYLESHEET"
]
