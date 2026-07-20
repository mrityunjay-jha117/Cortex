"""
=============================================================================
 DYNAMIC_ITERATE.PY (flow_components)
=============================================================================
This module is a microservice component for flow_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from cortex.graph_model import DynamicIterateNode

class DynamicIterateMixin:
    def _build_dynamic_iterate(self, node: DynamicIterateNode) -> None:
        self._form_layout.addRow("Source Key", self._line_edit( # type: ignore
            node.source_key, lambda v: self._set(node, "source_key", v) # type: ignore
        ))
        self._form_layout.addRow("Output Key", self._line_edit( # type: ignore
            node.output_key, lambda v: self._set(node, "output_key", v) # type: ignore
        ))
        self._add_hint( # type: ignore
            "source_key must match the output_key of a\n"
            "LocateElement (find_all) or LLM extraction node.\n"
            "Each iteration puts the current item into output_key."
        )
