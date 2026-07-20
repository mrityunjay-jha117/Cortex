"""
=============================================================================
 PAINTER_HEADER.PY (node_components)
=============================================================================
This module is a microservice component for node_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QPen, QBrush, QPainterPath, QFont
from cognitive_automator.gui.canvas.base import NODE_W

class NodePainterHeader:
    @staticmethod
    def _draw_header(node_item, painter, header_color: QColor) -> int:
        header_h = 24
        painter.setBrush(QBrush(header_color))
        painter.setPen(Qt.PenStyle.NoPen)

        path = QPainterPath()
        path.moveTo(0, 0)
        path.lineTo(NODE_W, 0)
        path.lineTo(NODE_W, header_h)
        path.lineTo(0, header_h)
        path.lineTo(0, 0)
        painter.drawPath(path)
        
        painter.setPen(QPen(QColor("#E5E7EB"), 1.0))
        painter.drawLine(0, header_h, NODE_W, header_h)

        header_text_color = QColor("#FFFFFF")
        if header_color.lightness() > 180:
            header_text_color = QColor("#1A1A1A")
        painter.setPen(header_text_color)
        
        font = QFont("Courier New", 10, QFont.Weight.Bold)
        painter.setFont(font)
        type_name = type(node_item.node).__name__.replace("Node", "").upper()
        painter.drawText(QRectF(8, 2, NODE_W - 16, header_h - 4),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, type_name)
        return header_h
