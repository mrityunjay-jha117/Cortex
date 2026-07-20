"""
=============================================================================
 GUI CONSTANTS
=============================================================================
This module centrally defines all styling and layout constants for the UI.
It holds colors, fonts, dimensions, and theme settings.

Key Features:
1. Ensures consistent aesthetics across all widgets and canvas items.
2. Makes theme adjustments centralized and easy to update.

Think of this module as the style guide and color palette for the app.
=============================================================================
"""

from .constants_components import (
    APP_BG, APP_SURFACE, APP_SURFACE2, APP_BORDER, APP_TEXT, APP_TEXT_DIM,
    APP_ACCENT, APP_SUCCESS, APP_WARNING, APP_ERROR,
    NODE_COLORS, NODE_CATEGORY_LABELS,
    MAIN_STYLESHEET
)

__all__ = [
    "APP_BG", "APP_SURFACE", "APP_SURFACE2", "APP_BORDER", "APP_TEXT", "APP_TEXT_DIM",
    "APP_ACCENT", "APP_SUCCESS", "APP_WARNING", "APP_ERROR",
    "NODE_COLORS", "NODE_CATEGORY_LABELS",
    "MAIN_STYLESHEET"
]
