"""
=============================================================================
 PAINTER_BASE.PY (node_components)
=============================================================================
This module is a microservice component for node_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QPen, QBrush
from cortex.gui.canvas.base import NODE_W, NODE_COLORS

class NodePainterBase:
    @staticmethod
    def bounding_rect(node_item) -> QRectF:
        return QRectF(-10, -10, NODE_W + 20, node_item.node_h + 20)

    @staticmethod
    def _draw_background_and_border(node_item, painter, h: int) -> tuple[QColor, QColor]:
        colors = NODE_COLORS.get(node_item.node.category.value, NODE_COLORS["physical"])
        
        header_color_str = node_item.node.color or colors["header"]
        border_color_str = node_item.node.color or colors["border"]
        header_color = QColor(header_color_str)
        border_color = QColor(border_color_str)

        if node_item._executing:
            painter.setPen(QPen(QColor("#000000"), 2.0, Qt.PenStyle.DashLine))
        elif node_item.isSelected():
            painter.setPen(QPen(QColor("#000000"), 3.0))
        elif getattr(node_item, "_is_hovered", False):
            painter.setPen(QPen(QColor("#000000"), 2.0))
        elif node_item._success is True:
            painter.setPen(QPen(QColor("#00C9A7"), 1.5))
        elif node_item._success is False:
            painter.setPen(QPen(QColor("#FF6B6B"), 1.5))
        else:
            painter.setPen(QPen(border_color, 1.0))

        painter.setBrush(QBrush(QColor(colors["bg"])))
        painter.drawRect(QRectF(0, 0, NODE_W, h))
        return header_color, border_color
