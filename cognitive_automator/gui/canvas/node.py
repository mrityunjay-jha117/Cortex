"""
=============================================================================
 CANVAS NODES
=============================================================================
This module handles the visual representation of action nodes.
It draws the rounded rectangles, titles, and icons for each step in the graph.

Key Features:
1. Manages drag-and-drop movement within the scene.
2. Organizes input and output ports visually on the node body.

Think of this module as the physical sticky notes placed on a whiteboard.
=============================================================================
"""

from .base import *
from .base import _elide
from .port import PortItem
from .edge import EdgeItem
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

        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)
        self.shadow.setXOffset(4)
        self.shadow.setYOffset(4)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(self.shadow)

        # Dynamic height for complex nodes
        from cognitive_automator.graph_model import ForLoopNode
        self.node_h = NODE_H + 20 if isinstance(node, ForLoopNode) else NODE_H

        # Ports
        colors = NODE_COLORS.get(node.category.value, NODE_COLORS["physical"])
        self._input_ports: list[PortItem] = []
        self._output_ports: list[PortItem] = []
        self._setup_ports()

    def _setup_ports(self) -> None:
        from cognitive_automator.graph_model import (
            LLMJudgmentNode, BranchNode, IterateNode, DynamicIterateNode,
            CompareNode,
        )
        node = self.node
        h = self.node_h
        
        # Default input (Left)
        if isinstance(node, GlobalStartNode):
            self._input_ports = []
            self._input_port = None
        elif not isinstance(node, ForLoopNode):
            in_port = PortItem(self, is_output=False, parent=self)
            in_port.setPos(0, h / 2)
            self._input_ports = [in_port]
            self._input_port = in_port # legacy
        else:
            # ForLoopNode specialized inputs
            # Left: In (from previous node)
            left_in = PortItem(self, is_output=False, label="In", parent=self)
            left_in.setPos(0, h / 2)
            
            # Bottom Right: Back-link from loop end
            back_in = PortItem(self, is_output=False, label="Back", parent=self)
            back_in.setPos(NODE_W * 0.75, h)
            
            # Top: Data Bind (from CSV Loader)
            data_in = PortItem(self, is_output=False, label="Data", edge_label=EdgeLabel.DEFAULT, parent=self)
            data_in.setPos(NODE_W / 2, 0)
            
            self._input_ports = [left_in, back_in, data_in]
            self._input_port = left_in

        # Output ports
        if isinstance(node, GlobalEndNode):
            self._output_ports = []
        elif isinstance(node, (LLMJudgmentNode, BranchNode, CompareNode)):
            t_port = PortItem(self, is_output=True, label="T", edge_label=EdgeLabel.TRUE, parent=self)
            t_port.setPos(NODE_W, h * 0.35)
            f_port = PortItem(self, is_output=True, label="F", edge_label=EdgeLabel.FALSE, parent=self)
            f_port.setPos(NODE_W, h * 0.65)
            self._output_ports = [t_port, f_port]
        elif isinstance(node, ForLoopNode):
            # Bottom Left: Body (start loop)
            body_port = PortItem(self, is_output=True, label="↻ Body", edge_label=EdgeLabel.LOOP_BODY, parent=self)
            body_port.setPos(NODE_W * 0.25, h)
            
            # Right: End (finished)
            end_port = PortItem(self, is_output=True, label=" End", edge_label=EdgeLabel.LOOP_END, parent=self)
            end_port.setPos(NODE_W, h / 2)
            
            self._output_ports = [body_port, end_port]
        elif isinstance(node, (IterateNode, DynamicIterateNode)):
            body_port = PortItem(self, is_output=True, label="↻", edge_label=EdgeLabel.LOOP_BODY, parent=self)
            body_port.setPos(NODE_W, h * 0.35)
            end_port = PortItem(self, is_output=True, label="", edge_label=EdgeLabel.LOOP_END, parent=self)
            end_port.setPos(NODE_W, h * 0.65)
            self._output_ports = [body_port, end_port]
        else:
            default_port = PortItem(self, is_output=True, label="", edge_label=EdgeLabel.DEFAULT, parent=self)
            default_port.setPos(NODE_W, h / 2)
            self._output_ports = [default_port]

    def boundingRect(self) -> QRectF:
        return QRectF(-10, -10, NODE_W + 20, self.node_h + 20)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem,
              widget: QWidget | None = None) -> None:
        colors = NODE_COLORS.get(self.node.category.value, NODE_COLORS["physical"])
        h = self.node_h
        
        # Determine base colors (custom color override)
        header_color_str = self.node.color or colors["header"]
        border_color_str = self.node.color or colors["border"]
        header_color = QColor(header_color_str)
        border_color = QColor(border_color_str)

        # Selection / execution state overrides border
        if self._executing:
            painter.setPen(QPen(QColor("#000000"), 2.0, Qt.PenStyle.DashLine))
        elif self.isSelected():
            painter.setPen(QPen(QColor("#000000"), 3.0)) # thicker black for selection
        elif getattr(self, "_is_hovered", False):
            painter.setPen(QPen(QColor("#000000"), 2.0)) # thicker black for hover
        elif self._success is True:
            painter.setPen(QPen(QColor("#00C9A7"), 1.5))
        elif self._success is False:
            painter.setPen(QPen(QColor("#FF6B6B"), 1.5))
        else:
            painter.setPen(QPen(border_color, 1.0))

        # Background
        painter.setBrush(QBrush(QColor(colors["bg"])))
        painter.drawRect(QRectF(0, 0, NODE_W, h))

        # Header stripe
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

        # Header text
        header_text_color = QColor("#FFFFFF")
        if header_color.lightness() > 180:
            header_text_color = QColor("#1A1A1A")
        painter.setPen(header_text_color)
        
        font = QFont("Courier New", 10, QFont.Weight.Bold)
        painter.setFont(font)
        type_name = type(self.node).__name__.replace("Node", "").upper()
        painter.drawText(QRectF(8, 2, NODE_W - 16, header_h - 4),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, type_name)

        # Node label
        painter.setPen(QColor("#000000"))
        font2 = QFont("Courier New", 11, QFont.Weight.Bold)
        painter.setFont(font2)
        label = self.node.label or self.node.id[:8]
        label_w = NODE_W - 16
        
        # Display parameters for specific nodes
        param_str = ""
        from cognitive_automator.graph_model import ForLoopNode, FileDropNode
        if isinstance(self.node, ForLoopNode):
            param_str = f"({self.node.start} to {self.node.end}, step {self.node.step})"
        elif isinstance(self.node, FileDropNode):
            param_str = f"Path: {_elide(self.node.file_path, 100)}"

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

        # Disabled overlay
        if not self.node.enabled:
            painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(QRectF(0, 0, NODE_W, h))

        # Port labels for multi-port nodes
        painter.setPen(QColor("#000000"))
        label_font = QFont("Courier New", 9, QFont.Weight.Bold)
        painter.setFont(label_font)
        for port in self._output_ports + self._input_ports:
            if port.label:
                # Adjust position based on side
                px, py = port.pos().x(), port.pos().y()
                if px == 0: # Left
                    rect = QRectF(px + 8, py - 8, 40, 16)
                    align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                elif px == NODE_W: # Right
                    rect = QRectF(px - 48, py - 8, 40, 16)
                    align = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                elif py == 0: # Top
                    rect = QRectF(px - 35, py + 8, 70, 16)
                    align = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop
                else: # Bottom
                    rect = QRectF(px - 35, py - 24, 70, 16)
                    align = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom
                
                painter.drawText(rect, align, port.label)

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
