"""
runtime/executor.py — Facade for Execution Engine

This module exposes the core GraphExecutor and its models.
It has been modularized into `engine.py`, `registry.py`, and `models.py`.
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
