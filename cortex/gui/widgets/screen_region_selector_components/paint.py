"""
=============================================================================
 PAINT.PY (screen_region_selector_components)
=============================================================================
This module is a microservice component for screen_region_selector_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPaintEvent
from PyQt6.QtCore import Qt

class PaintMixin:
    def paintEvent(self, _event: QPaintEvent) -> None:
        p = QPainter(self) # type: ignore
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dark vignette outside selection
        p.fillRect(self.rect(), QColor(0, 0, 0, 130)) # type: ignore

        # Punch out the selection area to show real screen behind
        r = self._rect.normalized()
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        p.fillRect(r, QColor(0, 0, 0, 0))
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        # Dotted border
        pen = QPen(QColor(255, 255, 255, 220), 2, Qt.PenStyle.CustomDashLine)
        pen.setDashPattern([6.0, 4.0])
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(r)

        # Resize handles
        p.setPen(QPen(QColor(255, 255, 255, 200), 1))
        p.setBrush(QBrush(QColor("#7B61FF")))
        for hr in self._handle_rects():
            p.drawRect(hr)

        # Click point crosshair (Red)
        if self._click_point and r.contains(self._click_point):
            p.setPen(QPen(QColor("#FF4C4C"), 2))
            cp = self._click_point
            p.drawLine(cp.x() - 8, cp.y(), cp.x() + 8, cp.y())
            p.drawLine(cp.x(), cp.y() - 8, cp.x(), cp.y() + 8)
            p.drawEllipse(cp, 4, 4)

        p.end()
