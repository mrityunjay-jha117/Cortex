from .base import *
from .scene import GraphScene
from .edge import EdgeItem
from .node import NodeItem
from .view_components import (
    handle_wheel_event, handle_mouse_press, handle_mouse_move, handle_mouse_release,
    handle_key_press, build_and_exec_menu, duplicate_selected
)

class GraphView(QGraphicsView):
    def __init__(self, scene: GraphScene, parent: QWidget | None = None) -> None:
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setStyleSheet(f"border: none; background: #FFFFFF;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self._is_panning = False
        self._last_pan_pos = QPointF()

    def wheelEvent(self, event: Any) -> None:
        if not handle_wheel_event(self, event):
            super().wheelEvent(event)

    def mousePressEvent(self, event: Any) -> None:
        if not handle_mouse_press(self, event):
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: Any) -> None:
        if not handle_mouse_move(self, event):
            super().mouseMoveEvent(event)
            self.scene().refresh_edges() if self.scene() else None

    def mouseReleaseEvent(self, event: Any) -> None:
        if not handle_mouse_release(self, event):
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: Any) -> None:
        if not handle_key_press(self, event):
            super().keyPressEvent(event)

    def _duplicate_selected(self) -> None:
        duplicate_selected(self)

    def contextMenuEvent(self, event: Any) -> None:
        build_and_exec_menu(self, event)
