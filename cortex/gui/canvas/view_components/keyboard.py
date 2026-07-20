"""
=============================================================================
 KEYBOARD.PY (view_components)
=============================================================================
This module is a microservice component for view_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from typing import Any
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsView, QMessageBox
from cortex.gui.canvas.node import NodeItem
from cortex.gui.canvas.edge import EdgeItem
from cortex.gui.canvas.scene import GraphScene

def handle_key_press(view, event: Any) -> bool:
    modifiers = event.modifiers()
    
    if event.key() == Qt.Key.Key_Space:
        if view.dragMode() == QGraphicsView.DragMode.RubberBandDrag:
            view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        else:
            view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        return True
    elif event.key() == Qt.Key.Key_F or event.key() == Qt.Key.Key_Home:
        if view.scene():
            selected = view.scene().selectedItems()
            rect = view.scene().itemsBoundingRect()
            if selected:
                sel_rect = selected[0].sceneBoundingRect()
                for item in selected[1:]:
                    sel_rect = sel_rect.united(item.sceneBoundingRect())
                rect = sel_rect
            view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        return True
    elif event.key() == Qt.Key.Key_D and modifiers == Qt.KeyboardModifier.ControlModifier:
        duplicate_selected(view)
        return True
    elif event.key() == Qt.Key.Key_Delete:
        delete_selected(view)
        return True
    return False

def duplicate_selected(view) -> None:
    scene_cast: GraphScene = view.scene()  # type: ignore[assignment]
    if not scene_cast or not scene_cast._graph:
        return
    selected = [i for i in scene_cast.selectedItems() if isinstance(i, NodeItem)]
    if not selected:
        return
    
    for item in selected:
        scene_cast._graph.duplicate_node(item.node.id)
    
    scene_cast.load_graph(scene_cast._graph)
    scene_cast.graph_modified.emit()

def delete_selected(view) -> None:
    scene_cast: GraphScene = view.scene()  # type: ignore[assignment]
    if not scene_cast or not scene_cast._graph:
        return
    selected = scene_cast.selectedItems()
    if not selected:
        return
        
    if len(selected) > 1:
        reply = QMessageBox.question(
            view, "Delete Multiple", 
            f"Are you sure you want to delete {len(selected)} items?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return

    changed = False
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
