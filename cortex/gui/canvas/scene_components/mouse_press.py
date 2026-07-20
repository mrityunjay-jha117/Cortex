"""
=============================================================================
 MOUSE_PRESS.PY (scene_components)
=============================================================================
This module is a microservice component for scene_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from typing import Any
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPen, QColor
from PyQt6.QtWidgets import QGraphicsPathItem
from cortex.gui.canvas.port import PortItem

class SceneMousePress:
    @staticmethod
    def mousePressEvent(scene, event: Any) -> bool:
        if event.button() == Qt.MouseButton.LeftButton:
            port_hits = [i for i in scene.items(event.scenePos())
                         if isinstance(i, PortItem)]
            if port_hits:
                scene._drag_port = port_hits[0]
                scene._temp_edge = QGraphicsPathItem()
                scene._temp_edge.setPen(QPen(QColor("#000000"), 2, Qt.PenStyle.SolidLine))
                scene._temp_edge.setZValue(10)
                scene.addItem(scene._temp_edge)
                event.accept()
                return True
        return False
