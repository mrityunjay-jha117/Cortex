"""
=============================================================================
 KEYBOARD.PY (physical_components)
=============================================================================
This module is a microservice component for physical_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from cortex.graph_model import KeyboardNode, KeyboardAction

class KeyboardBuilder:
    def _build_keyboard(self, node: KeyboardNode) -> None:
        action_combo = self._combo(
            [a.value for a in KeyboardAction], node.action.value,
            lambda v: [self._set(node, "action", KeyboardAction(v)), self._rebuild_form(node)]
        )
        self._form_layout.addRow("Action", action_combo)

        if node.action == KeyboardAction.TYPEWRITE:
            text_edit = self._plain_text(node.text, lambda v: self._set(node, "text", v))
            text_edit.setMaximumHeight(60)
            self._form_layout.addRow("Text", text_edit)
            self._form_layout.addRow("Interval (s)", self._dspin(node.interval, 0.0, 1.0, lambda v: self._set(node, "interval", v)))
        elif node.action == KeyboardAction.PRESS:
            self._form_layout.addRow("Key", self._line_edit(node.key, lambda v: self._set(node, "key", v)))
        elif node.action == KeyboardAction.HOTKEY:
            self._form_layout.addRow("Keys (hotkey)", self._line_edit(
                ",".join(node.keys),
                lambda v: self._set(node, "keys", [k.strip() for k in v.split(",") if k.strip()])
            ))
        elif node.action == KeyboardAction.PASTE:
            text_edit = self._plain_text(node.text, lambda v: self._set(node, "text", v))
            text_edit.setMaximumHeight(60)
            self._form_layout.addRow("Text to Paste", text_edit)
        elif node.action == KeyboardAction.SELECT_ALL:
            self._add_hint("Automatically performs Ctrl+A (or Cmd+A).")
