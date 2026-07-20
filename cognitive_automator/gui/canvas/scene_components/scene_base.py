"""
=============================================================================
 SCENE_BASE.PY (scene_components)
=============================================================================
This module is a microservice component for scene_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtWidgets import QGraphicsScene
from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QColor, QPainter, QBrush
from PyQt6.QtCore import Qt, QRectF
from cognitive_automator.graph_model import ActionGraph
from ..base import GRID_SIZE

class SceneBaseMixin(QGraphicsScene):
    node_selected = pyqtSignal(str)
    node_double_clicked = pyqtSignal(str)
    graph_modified = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.setSceneRect(-5000, -5000, 10000, 10000)
        self._graph: ActionGraph | None = None
        self._node_items = {}
        self._edge_items = []
        
        bg_pixmap = QPixmap(GRID_SIZE, GRID_SIZE)
        bg_pixmap.fill(QColor("#c5c2b2"))
        p = QPainter(bg_pixmap)
        p.setBrush(QBrush(QColor("#000000")))
        p.setPen(Qt.PenStyle.NoPen)
        size = 4.0
        p.drawRect(QRectF(0, 0, size, size))
        p.end()
        
        self.setBackgroundBrush(QBrush(bg_pixmap))
        self._drag_port = None
        self._temp_edge = None
