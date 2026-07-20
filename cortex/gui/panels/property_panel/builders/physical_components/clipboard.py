"""
=============================================================================
 CLIPBOARD.PY (physical_components)
=============================================================================
This module is a microservice component for physical_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from cortex.graph_model import ClipboardNode, ClipboardAction

class ClipboardBuilder:
    def _build_clipboard(self, node: ClipboardNode) -> None:
        action_combo = self._combo(
            [a.value for a in ClipboardAction], node.action.value,
            lambda v: self._set(node, "action", ClipboardAction(v))
        )
        self._form_layout.addRow("Action", action_combo)
        text_edit = self._plain_text(node.write_text, lambda v: self._set(node, "write_text", v))
        text_edit.setMaximumHeight(60)
        self._form_layout.addRow("Write Text", text_edit)
