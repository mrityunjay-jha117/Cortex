"""
=============================================================================
 STATE.PY (helpers_components)
=============================================================================
This module is a microservice component for helpers_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from typing import Any

class StateHelpers:
    def _safe_set(self, setter: Any, value: Any) -> None:
        if self._updating:
            return
        try:
            setter(value)
            if self._current_node:
                self.node_changed.emit(self._current_node.id)
        except Exception:
            pass

    def _set(self, node: Any, attr: str, value: Any) -> None:
        setattr(node, attr, value)
        if not self._updating:
            self.node_changed.emit(node.id)
