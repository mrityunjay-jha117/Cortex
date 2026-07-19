"""
=============================================================================
 EXECUTOR DISPATCHER
=============================================================================
This module acts as the middleman between the Engine and specific node logic.
It finds the correct runner for a given node and executes it safely.

Key Features:
1. Handles try/except blocks to catch node-specific crashes.
2. Ensures the engine doesn't die if a single node misbehaves.

Think of this module as the foreman assigning tasks to specific workers.
=============================================================================
"""

from .models import ExecutionStatus, ExecutionEvent, ExecutionConfig, StatusCallback, AbortException
from .engine import GraphExecutor
from .registry import EXECUTOR_REGISTRY

__all__ = [
    "ExecutionStatus",
    "ExecutionEvent",
    "ExecutionConfig",
    "StatusCallback",
    "AbortException",
    "GraphExecutor",
    "EXECUTOR_REGISTRY"
]
