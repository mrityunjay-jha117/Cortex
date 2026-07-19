"""
nodes/executors/flow/iterate.py — Iterate Executor

This file contains the execution logic for the IterateNode.
It manages stateful iteration over hardcoded item lists or loaded CSV columns, looping back to the LOOP_BODY edge until items are exhausted.
"""
from ..base import *
from .utils import _load_csv_column

def execute_iterate(node: IterateNode, context: dict[str, Any]) -> NodeResult:
    """
    Manages loop state in the context under '_iterate_{node_id}'.
    Returns LOOP_BODY edge while items remain, LOOP_END when exhausted.
    """
    state_key = f"_iterate_{node.id}"
    state = context.get(state_key, {"index": 0, "items": None})

    if state["items"] is None:
        # First call: load items
        if node.csv_file_path:
            items = _load_csv_column(node.csv_file_path, node.csv_column)
        else:
            items = list(node.items)
        state["items"] = items
        state["index"] = 0

    items: list[str] = state["items"]
    idx: int = state["index"]

    if idx >= len(items):
        # Reset state for potential re-run
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
