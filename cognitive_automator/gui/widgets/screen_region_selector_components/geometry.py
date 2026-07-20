"""
=============================================================================
 GEOMETRY.PY (screen_region_selector_components)
=============================================================================
This module is a microservice component for screen_region_selector_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtCore import QRect, QPoint
from typing import List, Optional

_HANDLE_SIZE = 10
_HALF = _HANDLE_SIZE // 2

class GeometryMixin:
    def _handle_rects(self) -> List[QRect]:
        r = self._rect.normalized()
        cx = r.left() + r.width() // 2
        cy = r.top() + r.height() // 2
        s, h = _HANDLE_SIZE, _HALF
        return [
            QRect(r.left() - h,  r.top() - h,    s, s),  # 0 TL
            QRect(cx - h,        r.top() - h,    s, s),  # 1 T
            QRect(r.right() - h, r.top() - h,    s, s),  # 2 TR
            QRect(r.right() - h, cy - h,          s, s),  # 3 R
            QRect(r.right() - h, r.bottom() - h,  s, s),  # 4 BR
            QRect(cx - h,        r.bottom() - h,  s, s),  # 5 B
            QRect(r.left() - h,  r.bottom() - h,  s, s),  # 6 BL
            QRect(r.left() - h,  cy - h,          s, s),  # 7 L
        ]

    def _hit_handle(self, pos: QPoint) -> Optional[int]:
        for i, hr in enumerate(self._handle_rects()):
            if hr.contains(pos):
                return i
        return None

    def _apply_handle(self, handle: int, pos: QPoint) -> None:
        r = QRect(self._rect_at_drag)  # type: ignore[arg-type]
        if handle == 0:
            r.setTopLeft(pos)
        elif handle == 1:
            r.setTop(pos.y())
        elif handle == 2:
            r.setTopRight(pos)
        elif handle == 3:
            r.setRight(pos.x())
        elif handle == 4:
            r.setBottomRight(pos)
        elif handle == 5:
            r.setBottom(pos.y())
        elif handle == 6:
            r.setBottomLeft(pos)
        elif handle == 7:
            r.setLeft(pos.x())
        self._rect = r
