"""
=============================================================================
 BRANCH.PY (flow_components)
=============================================================================
This module is a microservice component for flow_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from cognitive_automator.graph_model import BranchNode

class BranchMixin:
    def _build_branch(self, node: BranchNode) -> None:
        self._form_layout.addRow("Condition Key", self._line_edit(node.condition_key, lambda v: self._set(node, "condition_key", v))) # type: ignore
        self._add_hint("This key must exist in the\nexecution context as a bool.") # type: ignore
