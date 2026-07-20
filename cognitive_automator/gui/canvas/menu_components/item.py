"""
=============================================================================
 ITEM.PY (menu_components)
=============================================================================
This module is a microservice component for menu_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .item_base import AnimatedMenuItemBase
from .item_paint import AnimatedMenuItemPaint
from .item_events import AnimatedMenuItemEvents

class AnimatedMenuItem(AnimatedMenuItemBase, AnimatedMenuItemPaint, AnimatedMenuItemEvents):
    pass

__all__ = ["AnimatedMenuItem"]
