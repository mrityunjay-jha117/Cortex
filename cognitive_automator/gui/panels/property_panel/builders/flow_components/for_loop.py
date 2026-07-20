"""
=============================================================================
 FOR_LOOP.PY (flow_components)
=============================================================================
This module is a microservice component for flow_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from cognitive_automator.graph_model import ForLoopNode

class ForLoopMixin:
    def _build_for_loop(self, node: ForLoopNode) -> None:
        self._form_layout.addRow("Variable Name", self._line_edit(node.output_key, lambda v: self._set(node, "output_key", v))) # type: ignore
        self._form_layout.addRow("Start (i =)", self._spin(node.start, -999999, 999999, lambda v: self._set(node, "start", v))) # type: ignore
        self._form_layout.addRow("End (while i <)", self._spin(node.end, -999999, 999999, lambda v: self._set(node, "end", v))) # type: ignore
        self._form_layout.addRow("Step (i +=)", self._spin(node.step, -9999, 9999, lambda v: self._set(node, "step", v))) # type: ignore
        self._add_hint( # type: ignore
            "Connect Data nodes (CSV Loader, File Drop) to the top port.\n"
            "This will show a visual BLUE connection.\n"
            "Access data via ${data[i].column}."
        )
