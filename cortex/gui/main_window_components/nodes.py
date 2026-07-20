"""
=============================================================================
 NODES.PY (main_window_components)
=============================================================================
This module is a microservice component for main_window_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from typing import Any
from cortex.graph_model import LocateElementNode

class NodesMixin:
    def _add_node(self, node: Any) -> None:
        # Place at centre of view
        centre = self._view.mapToScene(
            self._view.viewport().rect().center()
        )
        node.x = centre.x()
        node.y = centre.y()
        self._graph.add_node(node)
        self._refresh_canvas()
        self._mark_modified()

    def _on_node_selected(self, node_id: str) -> None:
        node = self._graph.nodes.get(node_id)
        if node:
            self._prop_panel.show_node(node)

    def _on_node_double_clicked(self, node_id: str) -> None:
        node = self._graph.nodes.get(node_id)
        if node:
            self._prop_panel.show_node(node)

    def _on_node_changed(self, node_id: str) -> None:
        self._mark_modified()

    def _refresh_canvas(self) -> None:
        self._scene.load_graph(self._graph)
        self._prop_panel.clear()

    def _mark_modified(self) -> None:
        self._modified = True
        self._update_title()

    def _update_title(self) -> None:
        name = self._graph.metadata.name
        file_part = f" — {self._current_file.name}" if self._current_file else ""
        mod_part = " *" if self._modified else ""
        self.setWindowTitle(f"Cortex  ·  {name}{file_part}{mod_part}")

    def _toggle_global_ai_fallback(self, checked: bool) -> None:
        state_text = "ON" if checked else "OFF"
        self._ai_toggle_btn.setText(f" AI Fallback: {state_text}")
        
        count = 0
        from cortex.graph_model import LLMProvider
        for node in self._graph.nodes.values():
            if isinstance(node, LocateElementNode):
                node.use_fallback = checked
                node.fallback_provider_override = LLMProvider.OPENROUTER
                count += 1
        
        self._status.showMessage(f"AI Fallback {'enabled' if checked else 'disabled'} for {count} nodes")
        self._mark_modified()
        
        # Refresh property panel if a LocateElementNode is selected
        if self._prop_panel._current_node and isinstance(self._prop_panel._current_node, LocateElementNode):
            self._prop_panel.show_node(self._prop_panel._current_node)
