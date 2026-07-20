"""
=============================================================================
 __INIT__.PY (menu_components)
=============================================================================
This module is a microservice component for menu_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .item import AnimatedMenuItem
from .menu import AnimatedMenu

__all__ = ["AnimatedMenuItem", "AnimatedMenu"]
