"""
=============================================================================
 PAINTER_CONTENT.PY (node_components)
=============================================================================
This module is a microservice component for node_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QBrush
from cortex.gui.canvas.base import NODE_W, APP_ACCENT, _elide
from cortex.graph_model import ForLoopNode, FileDropNode

class NodePainterContent:
    @staticmethod
    def _draw_content(node_item, painter, header_h: int, h: int) -> None:
        painter.setPen(QColor("#000000"))
        font2 = QFont("Courier New", 11, QFont.Weight.Bold)
        painter.setFont(font2)
        label = node_item.node.label or node_item.node.id[:8]
        label_w = NODE_W - 16
        
        param_str = ""
        if isinstance(node_item.node, ForLoopNode):
            param_str = f"({node_item.node.start} to {node_item.node.end}, step {node_item.node.step})"
        elif isinstance(node_item.node, FileDropNode):
            param_str = f"Path: {_elide(node_item.node.file_path, 100)}"

        if param_str:
            painter.drawText(QRectF(8, header_h + 2, label_w, 20),
                             Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                             _elide(label, label_w - 8))
            painter.setPen(QColor(APP_ACCENT))
            painter.setFont(QFont("Courier New", 10, QFont.Weight.Normal))
            painter.drawText(QRectF(8, header_h + 22, label_w, 20),
                             Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                             param_str)
        else:
            painter.drawText(QRectF(8, header_h + 4, label_w, h - header_h - 8),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                             _elide(label, label_w - 8))

        if not node_item.node.enabled:
            painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(QRectF(0, 0, NODE_W, h))

        painter.setPen(QColor("#000000"))
        label_font = QFont("Courier New", 9, QFont.Weight.Bold)
        painter.setFont(label_font)
        for port in node_item._output_ports + node_item._input_ports:
            if port.label:
                px, py = port.pos().x(), port.pos().y()
                if px == 0:
                    rect = QRectF(px + 8, py - 8, 40, 16)
                    align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                elif px == NODE_W:
                    rect = QRectF(px - 48, py - 8, 40, 16)
                    align = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                elif py == 0:
                    rect = QRectF(px - 35, py + 8, 70, 16)
                    align = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop
                else:
                    rect = QRectF(px - 35, py - 24, 70, 16)
                    align = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom
                
                painter.drawText(rect, align, port.label)
