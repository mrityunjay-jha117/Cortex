import re

file_path = "cognitive_automator/gui/canvas/node.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add setAcceptHoverEvents(True) and shadow updates
content = content.replace(
    "self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)\n        self.setPos(node.x, node.y)",
    "self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)\n        self.setAcceptHoverEvents(True)\n        self.setPos(node.x, node.y)"
)

content = content.replace(
    "shadow.setBlurRadius(12)\n        shadow.setXOffset(0)\n        shadow.setYOffset(3)\n        shadow.setColor(QColor(0, 0, 0, 20))\n        self.setGraphicsEffect(shadow)",
    "self.shadow = QGraphicsDropShadowEffect()\n        self.shadow.setBlurRadius(6)\n        self.shadow.setXOffset(0)\n        self.shadow.setYOffset(4)\n        self.shadow.setColor(QColor(0, 0, 0, 13))\n        self.setGraphicsEffect(self.shadow)"
)

# 2. Update border pen colors
old_border = """        if self._executing:
            painter.setPen(QPen(QColor("#FFFFFF"), 2.5, Qt.PenStyle.DashLine))
        elif self.isSelected():
            painter.setPen(QPen(QColor(APP_ACCENT), 2))
        elif self._success is True:
            painter.setPen(QPen(QColor("#00C9A7"), 1.5))
        elif self._success is False:
            painter.setPen(QPen(QColor("#FF6B6B"), 1.5))
        else:
            painter.setPen(QPen(border_color, 1.5))"""

new_border = """        if self._executing:
            painter.setPen(QPen(QColor("#111827"), 2.0, Qt.PenStyle.DashLine))
        elif self.isSelected():
            painter.setPen(QPen(QColor("#111827"), 2.0))
        elif getattr(self, "_is_hovered", False):
            painter.setPen(QPen(QColor("#D1D5DB"), 1.0))
        elif self._success is True:
            painter.setPen(QPen(QColor("#00C9A7"), 1.5))
        elif self._success is False:
            painter.setPen(QPen(QColor("#FF6B6B"), 1.5))
        else:
            painter.setPen(QPen(border_color, 1.0))"""
            
content = content.replace(old_border, new_border)

# 3. Update header drawing
old_header = """        header_grad = QLinearGradient(0, 0, NODE_W, 0)
        header_grad.setColorAt(0, header_color)
        header_grad.setColorAt(1, header_color.darker(110))
        painter.setBrush(QBrush(header_grad))
        painter.setPen(Qt.PenStyle.NoPen)

        path = QPainterPath()
        path.moveTo(12, 0)
        path.lineTo(NODE_W - 12, 0)
        path.quadTo(NODE_W, 0, NODE_W, 12)
        path.lineTo(NODE_W, header_h)
        path.lineTo(0, header_h)
        path.lineTo(0, 12)
        path.quadTo(0, 0, 12, 0)
        painter.drawPath(path)"""

new_header = """        painter.setBrush(QBrush(header_color))
        painter.setPen(Qt.PenStyle.NoPen)

        path = QPainterPath()
        path.moveTo(12, 0)
        path.lineTo(NODE_W - 12, 0)
        path.quadTo(NODE_W, 0, NODE_W, 12)
        path.lineTo(NODE_W, header_h)
        path.lineTo(0, header_h)
        path.lineTo(0, 12)
        path.quadTo(0, 0, 12, 0)
        painter.drawPath(path)
        
        painter.setPen(QPen(QColor("#E5E7EB"), 1.0))
        painter.drawLine(0, header_h, NODE_W, header_h)"""

content = content.replace(old_header, new_header)

# 4. Add hover methods at the end
hover_methods = """

    def hoverEnterEvent(self, event: Any) -> None:
        self._is_hovered = True
        self.shadow.setBlurRadius(15)
        self.shadow.setYOffset(10)
        self.shadow.setColor(QColor(0, 0, 0, 20))
        
        transform = QTransform()
        transform.translate(NODE_W/2, self.node_h/2)
        transform.scale(1.02, 1.02)
        transform.translate(-NODE_W/2, -self.node_h/2)
        self.setTransform(transform)
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: Any) -> None:
        self._is_hovered = False
        self.shadow.setBlurRadius(6)
        self.shadow.setYOffset(4)
        self.shadow.setColor(QColor(0, 0, 0, 13))
        
        self.setTransform(QTransform())
        self.update()
        super().hoverLeaveEvent(event)
"""
content += hover_methods

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
