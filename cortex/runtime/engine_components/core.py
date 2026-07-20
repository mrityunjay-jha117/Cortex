"""
=============================================================================
 CORE.PY (engine_components)
=============================================================================
This module is a microservice component for engine_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from typing import Any
from cortex.graph_model import ActionGraph
from ..models import ExecutionConfig, ExecutionEvent, ExecutionStatus, StatusCallback

class CoreExecutorMixin:
    graph: ActionGraph
    config: ExecutionConfig
    on_event: StatusCallback
    _context: dict[str, Any]
    _paused: bool
    _abort: bool

    def pause(self) -> None: self._paused = True
    def resume(self) -> None: self._paused = False
    def abort(self) -> None: self._abort = True

    def _emit(self, status: ExecutionStatus, node_id: str = "", node_label: str = "", message: str = "") -> None:
        event = ExecutionEvent(status=status, node_id=node_id, node_label=node_label, message=message, context_snapshot=dict(self._context))
        try:
            self.on_event(event)
        except Exception:
            pass
