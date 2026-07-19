"""
=============================================================================
 CANVAS SCENE
=============================================================================
This module manages the QGraphicsScene which holds all canvas items.
It tracks the logical placement of nodes, edges, and handles background grids.

Key Features:
1. Manages addition and removal of visual items.
2. Syncs the visual state with the underlying `ActionGraph` data model.

Think of this module as the physical whiteboard where everything is drawn.
=============================================================================
"""

from .base import *
from .port import PortItem
from .node import NodeItem
from .edge import EdgeItem
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
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#D1D5DB")))
        
        radius = 2.0  # 6px diameter
        
        left = int(rect.left()) - (int(rect.left()) % GRID_SIZE)
        top = int(rect.top()) - (int(rect.top()) % GRID_SIZE)
        x = left
        while x < rect.right():
            y = top
            while y < rect.bottom():
                painter.drawEllipse(QPointF(x, y), radius, radius)
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
