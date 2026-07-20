"""
=============================================================================
 SUBGRAPH.PY (flow_components)
=============================================================================
This module is a microservice component for flow_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from cortex.graph_model import SubGraphNode

class SubGraphMixin:
    def _build_subgraph(self, node: SubGraphNode) -> None:
        self._form_layout.addRow("Graph Path", self._line_edit(node.sub_graph_path, lambda v: self._set(node, "sub_graph_path", v))) # type: ignore
