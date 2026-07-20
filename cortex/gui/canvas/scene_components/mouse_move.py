"""
=============================================================================
 MOUSE_MOVE.PY (scene_components)
=============================================================================
This module is a microservice component for scene_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from typing import Any
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPainterPath
from cortex.gui.canvas.base import NODE_W

class SceneMouseMove:
    @staticmethod
    def mouseMoveEvent(scene, event: Any) -> bool:
        if scene._drag_port is not None:
            p1 = scene._drag_port.center_scene_pos()
            p2 = event.scenePos()
            
            lx, ly = scene._drag_port.pos().x(), scene._drag_port.pos().y()
            node_w = NODE_W
            node_h = scene._drag_port.node_item.node_h
            
            vec = QPointF(1, 0)
            if lx <= 0: vec = QPointF(-1, 0)
            elif lx >= node_w: vec = QPointF(1, 0)
            elif ly <= 0: vec = QPointF(0, -1)
            elif ly >= node_h: vec = QPointF(0, 1)
            
            strength = max(abs(p2.x() - p1.x()), abs(p2.y() - p1.y())) * 0.4
            ctrl1 = p1 + vec * strength
            
            ctrl2 = QPointF(p2.x() - (p2.x() - p1.x())*0.4, p2.y())
            
            path = QPainterPath(p1)
            path.cubicTo(ctrl1, ctrl2, p2)
            if scene._temp_edge:
                scene._temp_edge.setPath(path)
            event.accept()
            return True
        scene.refresh_edges()
        return False
