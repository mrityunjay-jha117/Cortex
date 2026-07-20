"""
=============================================================================
 RUNTIME ENGINE
=============================================================================
This module defines the core execution loop that traverses the Action Graph.
It manages state, calls node executors, and determines the next node to run.

Key Features:
1. Maintains the `RuntimeContext` holding all variable state.
2. Resolves edges based on executor results (e.g., branching).

Think of this module as the heartbeat and brain stem of the running automation.
=============================================================================
"""

from typing import Any
from cognitive_automator.graph_model import ActionGraph
from .models import ExecutionConfig, StatusCallback
from .engine_components import CoreExecutorMixin, DispatchMixin, ExecutionMixin

class GraphExecutor(CoreExecutorMixin, DispatchMixin, ExecutionMixin):
    def __init__(self, graph: ActionGraph, config: ExecutionConfig | None = None, on_event: StatusCallback | None = None) -> None:
        self.graph = graph
        self.config = config or ExecutionConfig()
        self.on_event = on_event or (lambda e: None)
        self._context: dict[str, Any] = dict(self.config.initial_context)
        self._paused = False
        self._abort = False
