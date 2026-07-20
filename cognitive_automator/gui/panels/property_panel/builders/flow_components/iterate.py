"""
=============================================================================
 ITERATE.PY (flow_components)
=============================================================================
This module is a microservice component for flow_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from cognitive_automator.graph_model import IterateNode

class IterateMixin:
    def _build_iterate(self, node: IterateNode) -> None:
        self._form_layout.addRow("CSV Path", self._line_edit(node.csv_file_path, lambda v: self._set(node, "csv_file_path", v))) # type: ignore
        self._form_layout.addRow("CSV Column", self._line_edit(node.csv_column, lambda v: self._set(node, "csv_column", v))) # type: ignore
        self._form_layout.addRow("Output Key", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v))) # type: ignore
