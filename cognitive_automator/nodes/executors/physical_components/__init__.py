"""
=============================================================================
 __INIT__.PY (physical_components)
=============================================================================
This module is a microservice component for physical_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .mouse import execute_mouse
from .navigator import execute_navigator
from .keyboard import execute_keyboard
from .file_drop import execute_file_drop
from .clipboard import execute_clipboard

__all__ = ["execute_mouse", "execute_navigator", "execute_keyboard", "execute_file_drop", "execute_clipboard"]
