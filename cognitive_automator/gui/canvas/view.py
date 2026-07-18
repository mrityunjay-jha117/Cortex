from .base import *
from .scene import GraphScene
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
            menu.addAction("  Duplicate Node(s) [Ctrl+D]").triggered.connect(
                self._duplicate_selected
            )
            menu.addSeparator()

        # --- Vision Nodes ---
        vision_menu = menu.addMenu("  Vision")
        vision_menu.addAction("  Locate Image on Screen").triggered.connect(
            lambda: _add(LocateElementNode(label="Find Element"))
        )
        vision_menu.addAction("  Locate and Click").triggered.connect(
            lambda: _add(LocateAndClickNode(label="Find & Click"))
        )
        vision_menu.addAction("  Generative OCR (Text)").triggered.connect(
            lambda: _add(GenerativeOCRNode(label="Extract Text"))
        )
        vision_menu.addAction("  Vision Extraction (Table/JSON)").triggered.connect(
            lambda: _add(VisionExtractionNode(label="Extract Data"))
        )

        # --- LLM Nodes ---
        llm_menu = menu.addMenu("  LLM Logic")
        llm_menu.addAction("  LLM Judgment (Yes/No)").triggered.connect(
            lambda: _add(LLMJudgmentNode(label="Decision"))
        )
        llm_menu.addAction("  LLM Extraction (Structured)").triggered.connect(
            lambda: _add(LLMExtractionNode(label="Extract JSON"))
        )
        llm_menu.addAction("  LLM Generative (Text)").triggered.connect(
            lambda: _add(LLMGenerativeNode(label="Generate Text"))
        )

        # --- Flow & Loops ---
        flow_menu = menu.addMenu("  Flow & Loops")
        flow_menu.addAction("  For Loop (Counter)").triggered.connect(
            lambda: _add(ForLoopNode(label="Counter Loop"))
        )
        flow_menu.addAction("  Iterate (List/CSV)").triggered.connect(
            lambda: _add(IterateNode(label="List Loop"))
        )
        flow_menu.addAction("  Dynamic Iterate (Context)").triggered.connect(
            lambda: _add(DynamicIterateNode(label="Dynamic Loop"))
        )
        flow_menu.addAction("  Branch (Boolean)").triggered.connect(
            lambda: _add(BranchNode(label="If/Else"))
        )
        flow_menu.addAction("  Compare (Condition)").triggered.connect(
            lambda: _add(CompareNode(label="Check Condition"))
        )
        flow_menu.addAction("  Sub-Graph").triggered.connect(
            lambda: _add(SubGraphNode(label="Call Subroutine"))
        )
        flow_menu.addAction("  Wait / Delay").triggered.connect(
            lambda: _add(WaitNode(label="Wait"))
        )

        # --- Physical Input ---
        input_menu = menu.addMenu("  Input & IO")
        input_menu.addAction("  Mouse").triggered.connect(
            lambda: _add(MouseNode(label="Mouse Action"))
        )
        input_menu.addAction("  Keyboard").triggered.connect(
            lambda: _add(KeyboardNode(label="Keyboard Action"))
        )
        input_menu.addAction("  Clipboard").triggered.connect(
            lambda: _add(ClipboardNode(label="Clipboard"))
        )
        input_menu.addAction("  Navigator (Scroll/Focus)").triggered.connect(
            lambda: _add(NavigatorNode(label="Navigator"))
        )
        input_menu.addAction("  File Drop / Upload").triggered.connect(
            lambda: _add(FileDropNode(label="File Upload"))
        )
        input_menu.addAction("  Screenshotter (Multi-Page)").triggered.connect(
            lambda: _add(ScreenshotterNode(label="Capturing Pages"))
        )
        input_menu.addAction("  Load CSV Data").triggered.connect(
            lambda: _add(CSVDataLoaderNode(label="Load Data"))
        )

        # --- System ---
        sys_menu = menu.addMenu("  System")
        sys_menu.addAction("  Global Start").triggered.connect(
            lambda: _add(GlobalStartNode(label="START"))
        )
        sys_menu.addAction("  Global End").triggered.connect(
            lambda: _add(GlobalEndNode(label="END"))
        )
        sys_menu.addAction("  Write to File").triggered.connect(
            lambda: _add(WriteFileNode(label="Save Output"))
        )
        sys_menu.addAction("  Export to CSV").triggered.connect(
            lambda: _add(CSVWriterNode(label="CSV Writer"))
        )
        sys_menu.addAction("  Load CSV Data").triggered.connect(
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
