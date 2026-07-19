"""
=============================================================================
 CANVAS EDGES
=============================================================================
This module handles the visual rendering of connections between nodes.
It draws cubic bezier curves or lines linking output ports to input ports.

Key Features:
1. Renders smooth paths mapping data and flow execution.
2. Manages dynamic updates when connected nodes are moved.

Think of this module as the digital string connecting the cans.
=============================================================================
"""

from .base import *
from .port import PortItem
class EdgeItem(QGraphicsPathItem):
    def __init__(self, source_port: PortItem, target_port: PortItem,
                 label: EdgeLabel = EdgeLabel.DEFAULT) -> None:
        super().__init__()
        self.source_port = source_port
        self.target_port = target_port
        self.label = label
        self.setZValue(-1)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self._update_path()

        edge_colors = {
            EdgeLabel.DEFAULT: "#555577",
            EdgeLabel.TRUE: "#00C9A7",
            EdgeLabel.FALSE: "#FF6B6B",
            EdgeLabel.LOOP_BODY: "#FFC107",
            EdgeLabel.LOOP_END: "#7B61FF",
            EdgeLabel.DATA_BIND: "#00BCD4",
            EdgeLabel.ERROR: "#FF4444",
        }
        color = edge_colors.get(label, "#555577")
        self._base_pen = QPen(QColor(color), 2, Qt.PenStyle.SolidLine)
        self.setPen(self._base_pen)
        self.setToolTip("Select + Delete to remove this connection")

    def _highlight_pen(self) -> QPen:
        return QPen(self._base_pen.color(), 4, Qt.PenStyle.SolidLine)

    def hoverEnterEvent(self, event: Any) -> None:
        if not self.isSelected():
            self.setPen(self._highlight_pen())
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: Any) -> None:
        if not self.isSelected():
            self.setPen(self._base_pen)
        super().hoverLeaveEvent(event)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.setPen(self._highlight_pen() if value else self._base_pen)
        return super().itemChange(change, value)

    def _update_path(self) -> None:
        p1 = self.source_port.center_scene_pos()
        p2 = self.target_port.center_scene_pos()
        
        # Smart tangents based on port position
        # source_port and target_port are PortItems
        def get_tangent(port: PortItem, start_pos: QPointF, end_pos: QPointF) -> QPointF:
            # Local position determines which side it's on
            lx, ly = port.pos().x(), port.pos().y()
            node_w = NODE_W
            node_h = port.node_item.node_h
            
            # Default to horizontal right
            vec = QPointF(1, 0)
            if lx <= 0: # Left
                vec = QPointF(-1, 0)
            elif lx >= node_w: # Right
                vec = QPointF(1, 0)
            elif ly <= 0: # Top
                vec = QPointF(0, -1)
            elif ly >= node_h: # Bottom
                vec = QPointF(0, 1)
            
            strength = max(abs(end_pos.x() - start_pos.x()), abs(end_pos.y() - start_pos.y())) * 0.4
            return start_pos + vec * strength

        ctrl1 = get_tangent(self.source_port, p1, p2)
        ctrl2 = get_tangent(self.target_port, p2, p1)
        
        path = QPainterPath(p1)
        path.cubicTo(ctrl1, ctrl2, p2)
        self.setPath(path)

    def update_path(self) -> None:
        self._update_path()
