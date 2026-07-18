"""
gui/canvas.py — Visual node graph editor using PyQt6 QGraphicsScene/View.

Nodes are rendered as draggable QGraphicsItems.
Edges are drawn as bezier curves between port sockets.
"""

from __future__ import annotations

import collections
from typing import Any

from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QObject
from PyQt6.QtGui import (
    QColor, QFont, QPainter, QPainterPath, QPen, QBrush,
    QLinearGradient, QCursor,
)
from PyQt6.QtWidgets import (
    QGraphicsItem, QGraphicsObject, QGraphicsScene, QGraphicsView,
    QGraphicsPathItem, QMenu, QStyleOptionGraphicsItem, QWidget,
)

from cognitive_automator.graph_model import (
    ActionGraph, AnyNode, EdgeLabel, FileDropNode,
    GlobalStartNode, GlobalEndNode, ForLoopNode, CSVDataLoaderNode,
)
from cognitive_automator.gui.constants import NODE_COLORS, APP_BG, APP_ACCENT

NODE_W = 200
NODE_H = 70
PORT_RADIUS = 6
GRID_SIZE = 40


# ---------------------------------------------------------------------------
# Port socket
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Node item
# ---------------------------------------------------------------------------

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
        self.setPos(node.x, node.y)

        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)

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
            end_port = PortItem(self, is_output=True, label="✓ End", edge_label=EdgeLabel.LOOP_END, parent=self)
            end_port.setPos(NODE_W, h / 2)
            
            self._output_ports = [body_port, end_port]
        elif isinstance(node, (IterateNode, DynamicIterateNode)):
            body_port = PortItem(self, is_output=True, label="↻", edge_label=EdgeLabel.LOOP_BODY, parent=self)
            body_port.setPos(NODE_W, h * 0.35)
            end_port = PortItem(self, is_output=True, label="✓", edge_label=EdgeLabel.LOOP_END, parent=self)
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
            painter.setPen(QPen(QColor("#FFFFFF"), 2.5, Qt.PenStyle.DashLine))
        elif self.isSelected():
            painter.setPen(QPen(QColor(APP_ACCENT), 2))
        elif self._success is True:
            painter.setPen(QPen(QColor("#00C9A7"), 1.5))
        elif self._success is False:
            painter.setPen(QPen(QColor("#FF6B6B"), 1.5))
        else:
            painter.setPen(QPen(border_color, 1.5))

        # Background
        painter.setBrush(QBrush(QColor(colors["bg"])))
        painter.drawRoundedRect(QRectF(0, 0, NODE_W, h), 12, 12)

        # Header stripe
        header_h = 24
        header_grad = QLinearGradient(0, 0, NODE_W, 0)
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
        painter.drawPath(path)

        # Header text
        header_text_color = QColor("#FFFFFF")
        if header_color.lightness() > 180:
            header_text_color = QColor("#1A1A1A")
        painter.setPen(header_text_color)
        
        font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        painter.setFont(font)
        type_name = type(self.node).__name__.replace("Node", "").upper()
        painter.drawText(QRectF(12, 2, NODE_W - 24, header_h - 4),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, type_name)

        # Node label
        painter.setPen(QColor("#495057"))
        font2 = QFont("Segoe UI", 10)
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
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Normal))
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
            painter.drawRoundedRect(QRectF(0, 0, NODE_W, h), 12, 12)

        # Port labels for multi-port nodes
        painter.setPen(QColor("#999"))
        label_font = QFont("Segoe UI", 8)
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
            cast_scene: GraphScene = self.scene()  # type: ignore[assignment]
            cast_scene.node_double_clicked.emit(self.node.id)


# ---------------------------------------------------------------------------
# Edge (bezier curve)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------

class GraphScene(QGraphicsScene):
    node_selected = pyqtSignal(str)          # node_id
    node_double_clicked = pyqtSignal(str)    # node_id
    graph_modified = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._graph: ActionGraph | None = None
        self._node_items: dict[str, NodeItem] = {}
        self._edge_items: list[EdgeItem] = []
        self.setBackgroundBrush(QBrush(QColor(APP_BG)))
        self._drag_port: PortItem | None = None
        self._temp_edge: QGraphicsPathItem | None = None

    def load_graph(self, graph: ActionGraph) -> None:
        self.clear()
        self._graph = graph
        self._node_items = {}
        self._edge_items = []

        # Create node items
        for node_id, node in graph.nodes.items():
            item = NodeItem(node)
            item.selected_changed.connect(lambda it: self.node_selected.emit(it.node.id))
            self.addItem(item)
            self._node_items[node_id] = item

        # Create edge items
        for edge in graph.edges:
            src_node_item = self._node_items.get(edge.source_id)
            tgt_node_item = self._node_items.get(edge.target_id)
            if not src_node_item or not tgt_node_item:
                continue
            # Find matching output port
            src_port = next(
                (p for p in src_node_item._output_ports if p.edge_label == edge.label),
                src_node_item._output_ports[0] if src_node_item._output_ports else None,
            )
            # Find matching input port
            tgt_port = tgt_node_item._input_ports[0] if tgt_node_item._input_ports else None
            if len(tgt_node_item._input_ports) > 1 and src_port:
                from cognitive_automator.graph_model import EdgeLabel
                
                if edge.label == EdgeLabel.DATA_BIND:
                    valid_ports = [p for p in tgt_node_item._input_ports if p.label == "Data"]
                else:
                    valid_ports = [p for p in tgt_node_item._input_ports if p.label != "Data"]
                
                if not valid_ports:
                    valid_ports = tgt_node_item._input_ports
                    
                src_p = src_port.center_scene_pos()
                tgt_port = min(valid_ports, 
                               key=lambda p: (p.center_scene_pos() - src_p).manhattanLength())

            if src_port and tgt_port:
                edge_item = EdgeItem(src_port, tgt_port, edge.label)
                self.addItem(edge_item)
                self._edge_items.append(edge_item)

        self._auto_layout()

    def _auto_layout(self) -> None:
        """BFS layered layout — fires only when all nodes sit at the default (0, 0)."""
        if not self._graph or not self._node_items:
            return
        if not all(abs(n.x) < 1 and abs(n.y) < 1 for n in self._graph.nodes.values()):
            return

        node_ids = list(self._graph.nodes.keys())
        entry = self._graph.entry_node_id or (node_ids[0] if node_ids else None)
        if not entry:
            return

        # BFS from entry to assign a layer (column) to each node
        layers: dict[str, int] = {}
        queue: collections.deque[tuple[str, int]] = collections.deque([(entry, 0)])
        visited = {entry}
        while queue:
            nid, layer = queue.popleft()
            layers[nid] = layer
            for edge in self._graph.edges:
                if edge.source_id == nid and edge.target_id not in visited:
                    visited.add(edge.target_id)
                    queue.append((edge.target_id, layer + 1))

        # Disconnected nodes land in column 0
        for nid in node_ids:
            layers.setdefault(nid, 0)

        # Group nodes by layer and assign positions
        layer_groups: dict[int, list[str]] = collections.defaultdict(list)
        for nid, layer in layers.items():
            layer_groups[layer].append(nid)

        H_STEP = NODE_W + 80
        V_STEP = NODE_H + 40
        OFFSET_X = 60
        OFFSET_Y = 60

        for layer, nids in layer_groups.items():
            for i, nid in enumerate(nids):
                x = OFFSET_X + layer * H_STEP
                y = OFFSET_Y + i * V_STEP
                self._graph.nodes[nid].x = x
                self._graph.nodes[nid].y = y
                self._node_items[nid].setPos(x, y)

        self.refresh_edges()

    def refresh_edges(self) -> None:
        for edge_item in self._edge_items:
            edge_item.update_path()

    def get_node_item(self, node_id: str) -> "NodeItem | None":
        return self._node_items.get(node_id)

    def set_node_executing(self, node_id: str) -> None:
        for nid, item in self._node_items.items():
            if nid == node_id:
                item.set_executing(True)

    def set_node_result(self, node_id: str, success: bool) -> None:
        if node_id in self._node_items:
            self._node_items[node_id].set_result(success)

    def reset_all_states(self) -> None:
        for item in self._node_items.values():
            item.reset_state()

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        super().drawBackground(painter, rect)
        # Dot grid
        painter.setPen(QPen(QColor("#D1D5DB"), 2))
        left = int(rect.left()) - (int(rect.left()) % GRID_SIZE)
        top = int(rect.top()) - (int(rect.top()) % GRID_SIZE)
        x = left
        while x < rect.right():
            y = top
            while y < rect.bottom():
                painter.drawPoint(int(x), int(y))
                y += GRID_SIZE
            x += GRID_SIZE

    def mousePressEvent(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            port_hits = [i for i in self.items(event.scenePos())
                         if isinstance(i, PortItem)]
            if port_hits:
                self._drag_port = port_hits[0]
                self._temp_edge = QGraphicsPathItem()
                self._temp_edge.setPen(QPen(QColor("#AAAAFF"), 2, Qt.PenStyle.DashLine))
                self._temp_edge.setZValue(10)
                self.addItem(self._temp_edge)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: Any) -> None:
        if self._drag_port is not None:
            p1 = self._drag_port.center_scene_pos()
            p2 = event.scenePos()
            
            # Determine tangent for start port
            lx, ly = self._drag_port.pos().x(), self._drag_port.pos().y()
            node_w = NODE_W
            node_h = self._drag_port.node_item.node_h
            
            vec = QPointF(1, 0)
            if lx <= 0: vec = QPointF(-1, 0)
            elif lx >= node_w: vec = QPointF(1, 0)
            elif ly <= 0: vec = QPointF(0, -1)
            elif ly >= node_h: vec = QPointF(0, 1)
            
            strength = max(abs(p2.x() - p1.x()), abs(p2.y() - p1.y())) * 0.4
            ctrl1 = p1 + vec * strength
            
            # For the moving end, we just use a horizontal tangent for now
            ctrl2 = QPointF(p2.x() - (p2.x() - p1.x())*0.4, p2.y())
            
            path = QPainterPath(p1)
            path.cubicTo(ctrl1, ctrl2, p2)
            if self._temp_edge:
                self._temp_edge.setPath(path)
            event.accept()
            return
        super().mouseMoveEvent(event)
        self.refresh_edges()

    def mouseReleaseEvent(self, event: Any) -> None:
        if self._drag_port is not None and event.button() == Qt.MouseButton.LeftButton:
            if self._temp_edge:
                self.removeItem(self._temp_edge)
                self._temp_edge = None
            
            # Find hits (PortItems have priority, then NodeItems for snapping)
            all_hits = self.items(event.scenePos())
            target_port: PortItem | None = None
            
            # 1. Exact port hit
            for item in all_hits:
                if isinstance(item, PortItem) and item.node_item is not self._drag_port.node_item:
                    target_port = item
                    break
            
            # 2. Snapping: if dropped on a node, find its closest compatible port
            if not target_port:
                for item in all_hits:
                    if isinstance(item, NodeItem) and item is not self._drag_port.node_item:
                        ports = item._input_ports if self._drag_port.is_output else item._output_ports
                        if ports:
                            # Strict Snapping Logic:
                            # 1. Prioritize flow ports (label "" or "In")
                            # 2. Data/Back ports only snap if the mouse is extremely close (threshold)
                            
                            mouse_pos = event.scenePos()
                            flow_ports = [p for p in ports if p.label in ("", "In")]
                            special_ports = [p for p in ports if p.label in ("Data", "Back")]
                            
                            # Threshold for special ports (in pixels)
                            SNAP_THRESHOLD = 20.0
                            
                            best_port = None
                            min_dist = float('inf')
                            
                            # Check special ports first with threshold
                            for p in special_ports:
                                d = (p.mapToScene(0,0) - mouse_pos).manhattanLength()
                                if d < SNAP_THRESHOLD and d < min_dist:
                                    min_dist = d
                                    best_port = p
                            
                            # If no special port hit within threshold, snap to flow port
                            if not best_port and flow_ports:
                                best_port = min(flow_ports, 
                                    key=lambda p: (p.mapToScene(0,0) - mouse_pos).manhattanLength())
                            
                            target_port = best_port
                        break

            if target_port and self._graph:
                p1 = self._drag_port
                p2 = target_port
                
                # Logic: Always add edge from Output -> Input
                if p1.is_output and not p2.is_output:
                    src, tgt = p1, p2
                elif not p1.is_output and p2.is_output:
                    src, tgt = p2, p1
                else:
                    self._drag_port = None
                    event.accept()
                    return
                
                src_id = src.node_item.node.id
                tgt_id = tgt.node_item.node.id
                label = src.edge_label
                
                # --- Auto-linking Logic ---
                from cognitive_automator.graph_model import LocateElementNode, MouseNode, FileDropNode
                src_node = src.node_item.node
                tgt_node = tgt.node_item.node
                
                # If connecting LocateElement -> Mouse/FileDrop, auto-fill the Vision ID
                if isinstance(src_node, LocateElementNode):
                    if isinstance(tgt_node, (MouseNode, FileDropNode)) and not tgt_node.vision_node_id:
                        tgt_node.vision_node_id = src_node.output_key

                # Special Logic: If connecting to a ForLoop "Data" port
                if isinstance(tgt.node_item.node, ForLoopNode) and tgt.label == "Data":
                    label = EdgeLabel.DATA_BIND

                self._graph.add_edge(src_id, tgt_id, label)
                self.load_graph(self._graph)
                self.graph_modified.emit()
                
            self._drag_port = None
            event.accept()
            return
        super().mouseReleaseEvent(event)


# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------

class GraphView(QGraphicsView):
    def __init__(self, scene: GraphScene, parent: QWidget | None = None) -> None:
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setStyleSheet(f"border: none; background: {APP_BG};")
        
        self._is_panning = False
        self._last_pan_pos = QPointF()

    def wheelEvent(self, event: Any) -> None:
        # Standard zoom on wheel
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
            
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event: Any) -> None:
        # Blender-style Pan: Ctrl + Left Click OR Middle Click
        is_ctrl = event.modifiers() & Qt.KeyboardModifier.ControlModifier
        if event.button() == Qt.MouseButton.MiddleButton or \
           (event.button() == Qt.MouseButton.LeftButton and is_ctrl):
            self._is_panning = True
            self._last_pan_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return
            
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: Any) -> None:
        if self._is_panning:
            delta = event.position() - self._last_pan_pos
            self._last_pan_pos = event.position()
            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() - delta.x()))
            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() - delta.y()))
            return
            
        super().mouseMoveEvent(event)
        self.scene().refresh_edges() if self.scene() else None

    def mouseReleaseEvent(self, event: Any) -> None:
        if self._is_panning:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return
            
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: Any) -> None:
        from PyQt6.QtCore import Qt
        modifiers = event.modifiers()
        
        if event.key() == Qt.Key.Key_Space:
            # Pan mode toggle
            if self.dragMode() == QGraphicsView.DragMode.RubberBandDrag:
                self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            else:
                self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        elif event.key() == Qt.Key.Key_F or event.key() == Qt.Key.Key_Home:
            if self.scene():
                # Fit to selected or all
                selected = self.scene().selectedItems()
                rect = self.scene().itemsBoundingRect()
                if selected:
                    # Calculate bounding rect of selection
                    sel_rect = selected[0].sceneBoundingRect()
                    for item in selected[1:]:
                        sel_rect = sel_rect.united(item.sceneBoundingRect())
                    rect = sel_rect
                
                self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        elif event.key() == Qt.Key.Key_D and modifiers == Qt.KeyboardModifier.ControlModifier:
            self._duplicate_selected()
        elif event.key() == Qt.Key.Key_Delete:
            scene_cast: GraphScene = self.scene()  # type: ignore[assignment]
            if not scene_cast or not scene_cast._graph:
                return
            selected = scene_cast.selectedItems()
            if not selected:
                return
                
            # Confirmation for multiple items
            if len(selected) > 1:
                from PyQt6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self, "Delete Multiple", 
                    f"Are you sure you want to delete {len(selected)} items?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return

            changed = False
            # Order deletions: edges first, then nodes
            for item in [i for i in selected if isinstance(i, EdgeItem)]:
                src_id = item.source_port.node_item.node.id
                tgt_id = item.target_port.node_item.node.id
                lbl = item.label
                scene_cast._graph.edges = [
                    e for e in scene_cast._graph.edges
                    if not (e.source_id == src_id
                            and e.target_id == tgt_id
                            and e.label == lbl)
                ]
                changed = True
            
            for item in [i for i in selected if isinstance(i, NodeItem)]:
                scene_cast._graph.remove_node(item.node.id)
                changed = True

            if changed:
                scene_cast.load_graph(scene_cast._graph)
                scene_cast.graph_modified.emit()
        else:
            super().keyPressEvent(event)

    def _duplicate_selected(self) -> None:
        scene_cast: GraphScene = self.scene()  # type: ignore[assignment]
        if not scene_cast or not scene_cast._graph:
            return
        selected = [i for i in scene_cast.selectedItems() if isinstance(i, NodeItem)]
        if not selected:
            return
        
        for item in selected:
            scene_cast._graph.duplicate_node(item.node.id)
        
        scene_cast.load_graph(scene_cast._graph)
        scene_cast.graph_modified.emit()

    def contextMenuEvent(self, event: Any) -> None:
        from cognitive_automator.graph_model import (
            CompareNode, KeyboardNode, LocateElementNode, LocateAndClickNode, MouseNode, WaitNode, NavigatorNode,
            GenerativeOCRNode, VisionExtractionNode, LLMJudgmentNode, LLMExtractionNode,
            LLMGenerativeNode, BranchNode, IterateNode, DynamicIterateNode, SubGraphNode,
            ClipboardNode, WriteFileNode, CSVWriterNode, ScreenshotterNode,
        )
        scene_cast: GraphScene = self.scene()  # type: ignore[assignment]
        if not scene_cast or not scene_cast._graph:
            return
        scene_pos = self.mapToScene(event.pos())

        def _add(node: Any) -> None:
            node.x = scene_pos.x()
            node.y = scene_pos.y()
            scene_cast._graph.add_node(node)  # type: ignore[union-attr]
            scene_cast.load_graph(scene_cast._graph)  # type: ignore[arg-type]
            scene_cast.graph_modified.emit()

        menu = QMenu()
        
        selected_nodes = [i for i in scene_cast.selectedItems() if isinstance(i, NodeItem)]
        if selected_nodes:
            menu.addAction("📋  Duplicate Node(s) [Ctrl+D]").triggered.connect(
                self._duplicate_selected
            )
            menu.addSeparator()

        # --- Vision Nodes ---
        vision_menu = menu.addMenu("👁  Vision")
        vision_menu.addAction("🔍  Locate Image on Screen").triggered.connect(
            lambda: _add(LocateElementNode(label="Find Element"))
        )
        vision_menu.addAction("🎯  Locate and Click").triggered.connect(
            lambda: _add(LocateAndClickNode(label="Find & Click"))
        )
        vision_menu.addAction("📝  Generative OCR (Text)").triggered.connect(
            lambda: _add(GenerativeOCRNode(label="Extract Text"))
        )
        vision_menu.addAction("📊  Vision Extraction (Table/JSON)").triggered.connect(
            lambda: _add(VisionExtractionNode(label="Extract Data"))
        )

        # --- LLM Nodes ---
        llm_menu = menu.addMenu("🧠  LLM Logic")
        llm_menu.addAction("⚖  LLM Judgment (Yes/No)").triggered.connect(
            lambda: _add(LLMJudgmentNode(label="Decision"))
        )
        llm_menu.addAction("🏗  LLM Extraction (Structured)").triggered.connect(
            lambda: _add(LLMExtractionNode(label="Extract JSON"))
        )
        llm_menu.addAction("✍  LLM Generative (Text)").triggered.connect(
            lambda: _add(LLMGenerativeNode(label="Generate Text"))
        )

        # --- Flow & Loops ---
        flow_menu = menu.addMenu("🔗  Flow & Loops")
        flow_menu.addAction("🔁  For Loop (Counter)").triggered.connect(
            lambda: _add(ForLoopNode(label="Counter Loop"))
        )
        flow_menu.addAction("📑  Iterate (List/CSV)").triggered.connect(
            lambda: _add(IterateNode(label="List Loop"))
        )
        flow_menu.addAction("⚡  Dynamic Iterate (Context)").triggered.connect(
            lambda: _add(DynamicIterateNode(label="Dynamic Loop"))
        )
        flow_menu.addAction("🔀  Branch (Boolean)").triggered.connect(
            lambda: _add(BranchNode(label="If/Else"))
        )
        flow_menu.addAction("⚖  Compare (Condition)").triggered.connect(
            lambda: _add(CompareNode(label="Check Condition"))
        )
        flow_menu.addAction("📦  Sub-Graph").triggered.connect(
            lambda: _add(SubGraphNode(label="Call Subroutine"))
        )
        flow_menu.addAction("⏱  Wait / Delay").triggered.connect(
            lambda: _add(WaitNode(label="Wait"))
        )

        # --- Physical Input ---
        input_menu = menu.addMenu("🖱  Input & IO")
        input_menu.addAction("🖱  Mouse").triggered.connect(
            lambda: _add(MouseNode(label="Mouse Action"))
        )
        input_menu.addAction("⌨  Keyboard").triggered.connect(
            lambda: _add(KeyboardNode(label="Keyboard Action"))
        )
        input_menu.addAction("📋  Clipboard").triggered.connect(
            lambda: _add(ClipboardNode(label="Clipboard"))
        )
        input_menu.addAction("🧭  Navigator (Scroll/Focus)").triggered.connect(
            lambda: _add(NavigatorNode(label="Navigator"))
        )
        input_menu.addAction("📁  File Drop / Upload").triggered.connect(
            lambda: _add(FileDropNode(label="File Upload"))
        )
        input_menu.addAction("📸  Screenshotter (Multi-Page)").triggered.connect(
            lambda: _add(ScreenshotterNode(label="Capturing Pages"))
        )
        input_menu.addAction("📂  Load CSV Data").triggered.connect(
            lambda: _add(CSVDataLoaderNode(label="Load Data"))
        )

        # --- System ---
        sys_menu = menu.addMenu("⚙  System")
        sys_menu.addAction("🏁  Global Start").triggered.connect(
            lambda: _add(GlobalStartNode(label="START"))
        )
        sys_menu.addAction("🛑  Global End").triggered.connect(
            lambda: _add(GlobalEndNode(label="END"))
        )
        sys_menu.addAction("💾  Write to File").triggered.connect(
            lambda: _add(WriteFileNode(label="Save Output"))
        )
        sys_menu.addAction("📊  Export to CSV").triggered.connect(
            lambda: _add(CSVWriterNode(label="CSV Writer"))
        )
        sys_menu.addAction("📂  Load CSV Data").triggered.connect(
            lambda: _add(CSVDataLoaderNode(label="Load Data"))
        )

        menu.addSeparator()
        menu.addAction("Fit View  [F]").triggered.connect(
            lambda: self.fitInView(
                self.scene().itemsBoundingRect(),  # type: ignore[union-attr]
                Qt.AspectRatioMode.KeepAspectRatio,
            )
        )
        menu.exec(event.globalPos())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _elide(text: str, max_width: int, font_size: int = 10) -> str:
    if len(text) * (font_size * 0.6) <= max_width:
        return text
    chars = int(max_width / (font_size * 0.6)) - 1
    return text[:max(chars, 4)] + "…"
