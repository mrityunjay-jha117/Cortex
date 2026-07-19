"""
nodes/executors/flow/global_start.py — Global Start Executor

This file contains the execution logic for the GlobalStartNode.
It serves as the initial entry point marker for an automation workflow to begin execution.
"""
from ..base import *

def execute_global_start(node: GlobalStartNode, context: dict[str, Any]) -> NodeResult:
    """Entry point marker. Does nothing but pass flow."""
    log.info("Automation started via GlobalStartNode")
    return NodeResult(success=True)
