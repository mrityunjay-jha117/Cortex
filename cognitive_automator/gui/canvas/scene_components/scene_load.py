"""
=============================================================================
 SCENE_LOAD.PY (scene_components)
=============================================================================
This module is a microservice component for scene_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from cognitive_automator.graph_model import ActionGraph
from .layout import auto_layout_graph

class SceneLoadMixin:
    def load_graph(self, graph: ActionGraph) -> None:
        self.clear() # type: ignore
        self._graph = graph
        self._node_items = {}
        self._edge_items = []

        from ..node import NodeItem
        for node_id, node in graph.nodes.items():
            item = NodeItem(node)
            item.selected_changed.connect(lambda it: self.node_selected.emit(it.node.id)) # type: ignore
            self.addItem(item) # type: ignore
            self._node_items[node_id] = item

        from ..edge import EdgeItem
        for edge in graph.edges:
            src_node_item = self._node_items.get(edge.source_id)
            tgt_node_item = self._node_items.get(edge.target_id)
            if not src_node_item or not tgt_node_item:
                continue
            
            src_port = next(
                (p for p in src_node_item._output_ports if p.edge_label == edge.label),
                src_node_item._output_ports[0] if src_node_item._output_ports else None,
            )
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
                self.addItem(edge_item) # type: ignore
                self._edge_items.append(edge_item)

        self._auto_layout()

    def _auto_layout(self) -> None:
        auto_layout_graph(self) # type: ignore
