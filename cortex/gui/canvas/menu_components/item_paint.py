"""
=============================================================================
 ITEM_PAINT.PY (menu_components)
=============================================================================
This module is a microservice component for menu_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

import PyQt6.QtGui as QtGui
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath

class AnimatedMenuItemPaint:
    def paintEvent(self, event):
        painter = QPainter(self) # type: ignore
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self._is_pressed: # type: ignore
            bg_color = QColor("#f2f2f2")
            y_offset = 2
            bottom_depth = 0
        elif self.underMouse(): # type: ignore
            bg_color = QColor("#ffffff")
            y_offset = -1
            bottom_depth = 3
        else:
            bg_color = QColor("#ffffff")
            y_offset = 0
            bottom_depth = 2

        rect = self.rect() # type: ignore
        rect.adjust(2, 2 + y_offset, -2, -2 - (3 - bottom_depth))
        
        path = QPainterPath()
        path.addRect(float(rect.x()), float(rect.y()), float(rect.width()), float(rect.height() + bottom_depth))
        painter.fillPath(path, QColor("#a0a0a0"))
        
        path_top = QPainterPath()
        path_top.addRect(float(rect.x()), float(rect.y()), float(rect.width()), float(rect.height()))
        painter.fillPath(path_top, bg_color)
        
        pen = QtGui.QPen(QColor("#d4d4d4"))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawPath(path_top)
        
        painter.setPen(QColor("#000000"))
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(font)
        text_rect = QRect(rect.x() + 12, rect.y(), rect.width() - 34, rect.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text) # type: ignore

        if self.is_submenu: # type: ignore
            arrow_rect = QRect(rect.width() - 20, rect.y(), 15, rect.height())
            painter.setPen(QColor("#666666"))
            painter.drawText(arrow_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, "▶")
