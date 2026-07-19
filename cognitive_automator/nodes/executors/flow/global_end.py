"""
nodes/executors/flow/global_end.py — Global End Executor

This file contains the execution logic for the GlobalEndNode.
It serves as the definitive exit marker for an automation workflow, signaling successful completion to the runtime engine.
"""
from ..base import *

def execute_global_end(node: GlobalEndNode, context: dict[str, Any]) -> NodeResult:
    """Exit point marker. Signals completion."""
    log.info("Automation completed via GlobalEndNode")
    return NodeResult(success=True)
