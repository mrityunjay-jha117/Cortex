"""
gui/canvas/port.py — Canvas Port Graphics

This file defines the connection points (ports) attached to nodes.
It handles the logic for clicking and dragging out new edges from outputs to inputs, enforcing connection rules and visually representing connection states.
"""
from .base import *
class PortItem(QGraphicsItem):
    def __init__(self, node_item: "NodeItem", is_output: bool, label: str = "",
                 edge_label: EdgeLabel = EdgeLabel.DEFAULT, parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self.node_item = node_item
        self.is_output = is_output
        self.label = label
        self.edge_label = edge_label
        self._hovered = False
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        tip = "Drag to connect"
        self.setToolTip(tip)

    def boundingRect(self) -> QRectF:
        r = PORT_RADIUS + 6   # Much larger hit area to prevent accidental node moves
        return QRectF(-r, -r, r * 2, r * 2)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem,
              widget: QWidget | None = None) -> None:
        colors = NODE_COLORS.get(self.node_item.node.category.value, NODE_COLORS["physical"])
        color = QColor(colors["border"])
        
        # Visual distinction
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color if self._hovered else QColor(APP_BG)))
        
        if self.is_output:
            painter.drawEllipse(QRectF(-PORT_RADIUS, -PORT_RADIUS, PORT_RADIUS * 2, PORT_RADIUS * 2))
        else:
            painter.drawRect(QRectF(-PORT_RADIUS, -PORT_RADIUS, PORT_RADIUS * 2, PORT_RADIUS * 2))

    def hoverEnterEvent(self, event: Any) -> None:
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: Any) -> None:
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def center_scene_pos(self) -> QPointF:
        return self.mapToScene(QPointF(0, 0))
