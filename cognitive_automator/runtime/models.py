"""
=============================================================================
 RUNTIME MODELS
=============================================================================
This module defines data structures used strictly during execution.
It holds the context dictionary that acts as the graph's memory.

Key Features:
1. Defines `RuntimeContext` for variable storage.
2. Defines `ExecutionResult` for standardizing node outputs.

Think of this module as the clipboard where the engine takes its notes.
=============================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

class ExecutionStatus(str, Enum):
    STARTED = "started"
    NODE_INFO = "node_info"
    NODE_ENTER = "node_enter"
    NODE_SUCCESS = "node_success"
    NODE_FAILED = "node_failed"
    NODE_RETRYING = "node_retrying"
    NODE_HEALED = "node_healed"
    GRAPH_COMPLETE = "graph_complete"
    GRAPH_ABORTED = "graph_aborted"
    PAUSED = "paused"

@dataclass
class ExecutionEvent:
    status: ExecutionStatus
    node_id: str = ""
    node_label: str = ""
    message: str = ""
    context_snapshot: dict[str, Any] = field(default_factory=dict)

StatusCallback = Callable[[ExecutionEvent], None]

@dataclass
class ExecutionConfig:
    max_retries_per_node: int = 2
    retry_delay_seconds: float = 1.0
    step_mode: bool = False
    dev_mode: bool = False
    initial_context: dict[str, Any] = field(default_factory=dict)

class AbortException(Exception):
    pass
