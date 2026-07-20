"""
=============================================================================
 WORKER.PY (main_window_components)
=============================================================================
This module is a microservice component for main_window_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from PyQt6.QtCore import pyqtSignal, QObject
from cortex.graph_model import ActionGraph
from cortex.runtime.executor import ExecutionConfig, ExecutionEvent, GraphExecutor

class ExecutionWorker(QObject):
    event_received = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(self, graph: ActionGraph, config: ExecutionConfig) -> None:
        super().__init__()
        self._graph = graph
        self._config = config
        self._executor: GraphExecutor | None = None

    def run(self) -> None:
        self._executor = GraphExecutor(
            self._graph, self._config, on_event=self._on_event
        )
        self._executor.run()
        self.finished.emit()

    def _on_event(self, event: ExecutionEvent) -> None:
        self.event_received.emit(event)

    def abort(self) -> None:
        if self._executor:
            self._executor.abort()

    def pause(self) -> None:
        if self._executor:
            self._executor.pause()

    def resume(self) -> None:
        if self._executor:
            self._executor.resume()
