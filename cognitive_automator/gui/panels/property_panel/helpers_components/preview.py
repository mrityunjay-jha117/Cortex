"""
=============================================================================
 PREVIEW.PY (helpers_components)
=============================================================================
This module is a microservice component for helpers_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from typing import Any
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen

class PreviewHelpers:
    def _refresh_locate_preview(self, node: Any) -> None:
        if not self._locate_full_pixmap or not self._locate_img_label:
            return
        
        # Draw crosshair on a copy
        pm = self._locate_full_pixmap.copy()
        painter = QPainter(pm)
        painter.setPen(QPen(Qt.GlobalColor.red, 2))
        
        # Robust attribute check
        x_off = getattr(node, "x_offset", 0)
        y_off = getattr(node, "y_offset", 0)
        
        cx = pm.width() // 2 + x_off
        cy = pm.height() // 2 + y_off
        
        # Draw crosshair
        painter.drawLine(cx - 10, cy, cx + 10, cy)
        painter.drawLine(cx, cy - 10, cx, cy + 10)
        painter.end()
        
        # Scale for display
        scaled = pm.scaled(180, 120, Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
        self._locate_img_label.setPixmap(scaled)
