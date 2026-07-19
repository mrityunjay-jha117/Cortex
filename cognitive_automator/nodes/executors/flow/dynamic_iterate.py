"""
nodes/executors/flow/dynamic_iterate.py — Dynamic Iterate Executor

This file contains the execution logic for the DynamicIterateNode.
It iterates over a runtime-resolved iterable (like a list) stored dynamically in the execution context, yielding one item per loop cycle until exhausted.
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
