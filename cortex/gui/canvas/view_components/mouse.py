"""
=============================================================================
 MOUSE.PY (view_components)
=============================================================================
This module is a microservice component for view_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from typing import Any
from PyQt6.QtCore import Qt

def handle_wheel_event(view, event: Any) -> bool:
    zoom_in_factor = 1.15
    zoom_out_factor = 1 / zoom_in_factor
    
    if event.angleDelta().y() > 0:
        zoom_factor = zoom_in_factor
    else:
        zoom_factor = zoom_out_factor
        
    view.scale(zoom_factor, zoom_factor)
    return True

def handle_mouse_press(view, event: Any) -> bool:
    is_shift = event.modifiers() & Qt.KeyboardModifier.ShiftModifier
    if event.button() == Qt.MouseButton.MiddleButton or \
       (event.button() == Qt.MouseButton.LeftButton and is_shift):
        view._is_panning = True
        view._last_pan_pos = event.position()
        view.setCursor(Qt.CursorShape.ClosedHandCursor)
        return True
    return False

def handle_mouse_move(view, event: Any) -> bool:
    if view._is_panning:
        delta = event.position() - view._last_pan_pos
        view._last_pan_pos = event.position()
        view.horizontalScrollBar().setValue(int(view.horizontalScrollBar().value() - delta.x()))
        view.verticalScrollBar().setValue(int(view.verticalScrollBar().value() - delta.y()))
        return True
    return False

def handle_mouse_release(view, event: Any) -> bool:
    if view._is_panning:
        view._is_panning = False
        view.setCursor(Qt.CursorShape.ArrowCursor)
        return True
    return False
