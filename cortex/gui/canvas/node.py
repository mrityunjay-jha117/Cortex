from .base import *
from .port import PortItem
from .edge import EdgeItem
from .node_components.ports import setup_node_ports
from .node_components.painter import NodePainter
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QTransform
from cortex.graph_model import ForLoopNode

class NodeItem(QGraphicsObject):
    selected_changed = pyqtSignal(object)   # emits self

    def __init__(self, node: AnyNode, parent: QGraphicsItem | None = None) -> None:  # type: ignore[type-arg]
        super().__init__(parent)
        self.node = node
        self._executing = False
        self._success: bool | None = None

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setPos(node.x, node.y)

        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)
        self.shadow.setXOffset(4)
        self.shadow.setYOffset(4)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(self.shadow)

        # Dynamic height for complex nodes
        self.node_h = NODE_H + 20 if isinstance(node, ForLoopNode) else NODE_H

        # Ports
        self._input_ports: list[PortItem] = []
        self._output_ports: list[PortItem] = []
        setup_node_ports(self)

    def boundingRect(self) -> QRectF:
        return NodePainter.bounding_rect(self)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem,
              widget: QWidget | None = None) -> None:
        NodePainter.paint(self, painter, option, widget)

    def set_executing(self, executing: bool) -> None:
        self._executing = executing
        self._success = None
        self.update()

    def set_result(self, success: bool) -> None:
        self._executing = False
        self._success = success
        self.update()

    def reset_state(self) -> None:
        self._executing = False
        self._success = None
        self.update()

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.node.x = self.pos().x()
            self.node.y = self.pos().y()
            # Notify scene to redraw edges
            if self.scene():
                self.scene().update()  # type: ignore[union-attr]
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if value:
                self.selected_changed.emit(self)
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event: Any) -> None:
        """Double-click → open property panel (scene handles this via signal)."""
        if self.scene():
            from .scene import GraphScene
            cast_scene: GraphScene = self.scene()  # type: ignore[assignment]
            cast_scene.node_double_clicked.emit(self.node.id)

    def hoverEnterEvent(self, event: Any) -> None:
        self._is_hovered = True
        self.shadow.setXOffset(6)
        self.shadow.setYOffset(6)
        
        transform = QTransform()
        transform.translate(NODE_W/2, self.node_h/2)
        transform.scale(1.02, 1.02)
        transform.translate(-NODE_W/2, -self.node_h/2)
        self.setTransform(transform)
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: Any) -> None:
        self._is_hovered = False
        self.shadow.setXOffset(4)
        self.shadow.setYOffset(4)
        
        self.setTransform(QTransform())
        self.update()
        super().hoverLeaveEvent(event)
