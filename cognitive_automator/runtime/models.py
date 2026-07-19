"""
runtime/models.py — Execution Data Models

This file defines the data structures and enumerations used to track graph execution state,
configuration, and UI events.
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
