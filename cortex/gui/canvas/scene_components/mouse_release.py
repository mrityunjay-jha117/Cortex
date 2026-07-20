"""
=============================================================================
 MOUSE_RELEASE.PY (scene_components)
=============================================================================
This module is a microservice component for scene_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from typing import Any
from PyQt6.QtCore import Qt
from cortex.gui.canvas.port import PortItem
from cortex.gui.canvas.node import NodeItem
from cortex.gui.canvas.base import EdgeLabel

class SceneMouseRelease:
    @staticmethod
    def mouseReleaseEvent(scene, event: Any) -> bool:
        if scene._drag_port is not None and event.button() == Qt.MouseButton.LeftButton:
            if scene._temp_edge:
                scene.removeItem(scene._temp_edge)
                scene._temp_edge = None
            
            all_hits = scene.items(event.scenePos())
            target_port: PortItem | None = None
            
            for item in all_hits:
                if isinstance(item, PortItem) and item.node_item is not scene._drag_port.node_item:
                    target_port = item
                    break
            
            if not target_port:
                for item in all_hits:
                    if isinstance(item, NodeItem) and item is not scene._drag_port.node_item:
                        ports = item._input_ports if scene._drag_port.is_output else item._output_ports
                        if ports:
                            mouse_pos = event.scenePos()
                            flow_ports = [p for p in ports if p.label in ("", "In")]
                            special_ports = [p for p in ports if p.label in ("Data", "Back")]
                            
                            SNAP_THRESHOLD = 20.0
                            best_port = None
                            min_dist = float('inf')
                            
                            for p in special_ports:
                                d = (p.mapToScene(0,0) - mouse_pos).manhattanLength()
                                if d < SNAP_THRESHOLD and d < min_dist:
                                    min_dist = d
                                    best_port = p
                            
                            if not best_port and flow_ports:
                                best_port = min(flow_ports, 
                                    key=lambda p: (p.mapToScene(0,0) - mouse_pos).manhattanLength())
                            
                            target_port = best_port
                        break

            if target_port and scene._graph:
                p1 = scene._drag_port
                p2 = target_port
                
                if p1.is_output and not p2.is_output:
                    src, tgt = p1, p2
                elif not p1.is_output and p2.is_output:
                    src, tgt = p2, p1
                else:
                    scene._drag_port = None
                    event.accept()
                    return True
                
                src_id = src.node_item.node.id
                tgt_id = tgt.node_item.node.id
                label = src.edge_label
                
                from cortex.graph_model import LocateElementNode, MouseNode, FileDropNode, ForLoopNode
                src_node = src.node_item.node
                tgt_node = tgt.node_item.node
                
                if isinstance(src_node, LocateElementNode):
                    if isinstance(tgt_node, (MouseNode, FileDropNode)) and not tgt_node.vision_node_id:
                        tgt_node.vision_node_id = src_node.output_key

                if isinstance(tgt.node_item.node, ForLoopNode) and tgt.label == "Data":
                    label = EdgeLabel.DATA_BIND

                scene._graph.add_edge(src_id, tgt_id, label)
                scene.load_graph(scene._graph)
                scene.graph_modified.emit()
                
            scene._drag_port = None
            event.accept()
            return True
        return False
