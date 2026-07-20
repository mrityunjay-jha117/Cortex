"""
=============================================================================
 __INIT__.PY (view_components)
=============================================================================
This module is a microservice component for view_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .mouse import handle_wheel_event, handle_mouse_press, handle_mouse_move, handle_mouse_release
from .keyboard import handle_key_press, duplicate_selected
from .context_menu import build_and_exec_menu

__all__ = [
    "handle_wheel_event", "handle_mouse_press", "handle_mouse_move", "handle_mouse_release",
    "handle_key_press", "build_and_exec_menu", "duplicate_selected"
]
