"""
=============================================================================
 MENU.PY (menu_components)
=============================================================================
This module is a microservice component for menu_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .menu_base import AnimatedMenuBase
from .menu_build import AnimatedMenuBuild
from .menu_events import AnimatedMenuEvents

class AnimatedMenu(AnimatedMenuBuild, AnimatedMenuEvents, AnimatedMenuBase):
    pass

__all__ = ["AnimatedMenu"]
