"""
nodes/executors/flow/branch.py — Branch Node Executor

This file contains the execution logic for the BranchNode.
It evaluates a boolean condition key stored in the execution context and directs the graph's execution flow down either the TRUE or FALSE edge.
"""
from ..base import *

def execute_branch(node: BranchNode, context: dict[str, Any]) -> NodeResult:
    value = context.get(node.condition_key)
    if value is None:
        return NodeResult(success=False,
                          error=f"BranchNode: condition key '{node.condition_key}' not in context")
    is_true = bool(value) if not isinstance(value, dict) else bool(value.get("result", False))
    return NodeResult(success=True, next_edge=EdgeLabel.TRUE if is_true else EdgeLabel.FALSE)
