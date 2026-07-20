"""
=============================================================================
 MOUSE.PY (screen_region_selector_components)
=============================================================================
This module is a microservice component for screen_region_selector_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtGui import QMouseEvent
from PyQt6.QtCore import Qt, QRect

_HANDLE_CURSORS = [
    Qt.CursorShape.SizeFDiagCursor,
    Qt.CursorShape.SizeVerCursor,
    Qt.CursorShape.SizeBDiagCursor,
    Qt.CursorShape.SizeHorCursor,
    Qt.CursorShape.SizeFDiagCursor,
    Qt.CursorShape.SizeVerCursor,
    Qt.CursorShape.SizeBDiagCursor,
    Qt.CursorShape.SizeHorCursor,
]

class MouseMixin:
    def mousePressEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        
        # Right-click to set click target point
        if event.button() == Qt.MouseButton.RightButton:
            if self._rect.normalized().contains(pos):
                self._click_point = pos
                self.update() # type: ignore
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        h = self._hit_handle(pos)
        if h is not None:
            self._active_handle = h
            self._drag_start = pos
            self._rect_at_drag = QRect(self._rect)
        elif self._rect.normalized().contains(pos):
            self._dragging_body = True
            self._drag_start = pos
            self._rect_at_drag = QRect(self._rect)
        else:
            # Draw a new rectangle from scratch
            self._rect = QRect(pos, pos)
            self._drag_start = pos
            self._rect_at_drag = QRect(self._rect)
            self._active_handle = 4   # treat as BR drag so user draws outward
            self._click_point = None  # reset click point on new rect

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        buttons = event.buttons()

        if buttons & Qt.MouseButton.LeftButton:
            if self._active_handle is not None and self._drag_start is not None:
                self._apply_handle(self._active_handle, pos)
            elif self._dragging_body and self._drag_start is not None:
                delta = pos - self._drag_start
                self._rect = self._rect_at_drag.translated(delta)  # type: ignore[operator]
        else:
            # Hover cursor
            h = self._hit_handle(pos)
            if h is not None:
                self.setCursor(_HANDLE_CURSORS[h]) # type: ignore
            elif self._rect.normalized().contains(pos):
                self.setCursor(Qt.CursorShape.SizeAllCursor) # type: ignore
            else:
                self.setCursor(Qt.CursorShape.CrossCursor) # type: ignore
            return

        self._refresh_controls()
        self.update() # type: ignore

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._active_handle = None
        self._dragging_body = False
        self._drag_start = None
        self._rect_at_drag = None
