"""
=============================================================================
 DYNAMIC ITERATE EXECUTOR
=============================================================================
This module executes loops over dynamically generated collections of data.
It handles iteration state for variables defined at runtime.

Key Features:
1. Manages internal index counters for lists.
2. Determines when to exit the loop and continue the main graph execution.

Think of this module as the assembly line conveyor belt moving items one by one.
=============================================================================
"""

from ..base import *

def execute_dynamic_iterate(node: DynamicIterateNode, context: dict[str, Any]) -> NodeResult:
    """
    Iterates over a runtime list in context[source_key].
    Items can be (cx, cy) tuples (from LocateAll) or strings (from OCR/LLM).
    Returns LOOP_BODY with the current item, LOOP_END when exhausted.
    """
    state_key = f"_dyn_iterate_{node.id}"
    state = context.get(state_key, {"index": 0, "items": None})

    if state["items"] is None:
        raw = context.get(node.source_key, [])
        state["items"] = list(raw) if isinstance(raw, (list, tuple)) else [raw]
        state["index"] = 0

    items: list = state["items"]
    idx: int = state["index"]

    if idx >= len(items):
        context.pop(state_key, None)
        context.pop(node.output_key, None)  # Scope isolation: cleanup iterator
        return NodeResult(success=True, next_edge=EdgeLabel.LOOP_END)

    current_item = items[idx]
    state["index"] = idx + 1
    context[state_key] = state

    return NodeResult(
        success=True,
        next_edge=EdgeLabel.LOOP_BODY,
        output_key=node.output_key,
        output_value=current_item,
    )
