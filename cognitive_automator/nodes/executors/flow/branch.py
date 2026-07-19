"""
=============================================================================
 BRANCH EXECUTOR
=============================================================================
This module executes conditional logic to fork the graph's execution path.
It evaluates a boolean state and directs flow to either the True or False path.

Key Features:
1. Reads variables from the runtime context.
2. Returns specific edge labels to instruct the engine on which path to take.

Think of this module as the train track switch operator.
=============================================================================
"""

from ..base import *

def execute_branch(node: BranchNode, context: dict[str, Any]) -> NodeResult:
    value = context.get(node.condition_key)
    if value is None:
        return NodeResult(success=False,
                          error=f"BranchNode: condition key '{node.condition_key}' not in context")
    is_true = bool(value) if not isinstance(value, dict) else bool(value.get("result", False))
    return NodeResult(success=True, next_edge=EdgeLabel.TRUE if is_true else EdgeLabel.FALSE)
