"""
=============================================================================
 METHODS.PY (graph_components)
=============================================================================
This module is a microservice component for graph_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

import uuid
import networkx as nx
from typing import Any
from ..enums import EdgeLabel
from ..edges import GraphEdge
from ..system import GlobalStartNode

class GraphMethodsMixin:
    def _build_nx_graph(self, exclude_loop_edges: bool = False) -> nx.DiGraph:
        G: nx.DiGraph = nx.DiGraph()
        G.add_nodes_from(self.nodes.keys()) # type: ignore
        for edge in self.edges: # type: ignore
            if exclude_loop_edges and edge.label in (
                EdgeLabel.LOOP_BODY, EdgeLabel.LOOP_END,
                EdgeLabel.TRUE, EdgeLabel.FALSE,
            ):
                continue
            G.add_edge(edge.source_id, edge.target_id, label=edge.label.value)
        return G

    def to_nx(self) -> nx.DiGraph:
        return self._build_nx_graph(exclude_loop_edges=False)

    def add_node(self, node: Any) -> None:
        self.nodes[node.id] = node # type: ignore
        if getattr(self, "entry_node_id", None) is None or isinstance(node, GlobalStartNode):
            self.entry_node_id = node.id # type: ignore

    def duplicate_node(self, node_id: str) -> str | None:
        node = self.nodes.get(node_id) # type: ignore
        if not node:
            return None
        new_node = node.model_copy(deep=True, update={"id": str(uuid.uuid4())})
        new_node.x += 30
        new_node.y += 30
        self.nodes[new_node.id] = new_node # type: ignore
        return new_node.id

    def add_edge(self, source_id: str, target_id: str, label: EdgeLabel = EdgeLabel.DEFAULT) -> None:
        self.edges.append(GraphEdge(source_id=source_id, target_id=target_id, label=label)) # type: ignore

    def remove_node(self, node_id: str) -> None:
        self.nodes.pop(node_id, None) # type: ignore
        self.edges = [e for e in self.edges if e.source_id != node_id and e.target_id != node_id] # type: ignore
        if getattr(self, "entry_node_id", None) == node_id:
            self.entry_node_id = next(iter(self.nodes), None) # type: ignore

    def model_dump_with_types(self) -> dict[str, Any]:
        d = self.model_dump(mode="json") # type: ignore
        for node_id, node in self.nodes.items(): # type: ignore
            d["nodes"][node_id]["_type"] = type(node).__name__
        return d
