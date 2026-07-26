"""
=============================================================================
 BASIC ITERATE EXECUTOR
=============================================================================
This module provides simple iteration over static lists or predefined arrays.
It handles state injection for the current item in a loop.

Key Features:
1. Extracts the current element and stores it in context.
2. Moves to the next item automatically on the next cycle.

Think of this module as dealing cards one by one from a deck.
=============================================================================
"""

from ..base import *
from .utils import _load_csv_column
from typing import Any
from cortex.graph_model import IterateNode, EdgeLabel

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

    items_list: list[str] = state["items"]
    idx: int = state["index"]

    if idx >= len(items_list):
        # Reset state for potential re-run
        context.pop(state_key, None)
        context.pop(node.output_key, None)  # Scope isolation: cleanup iterator
        return NodeResult(success=True, next_edge=EdgeLabel.LOOP_END)

    current_item = items_list[idx]
    state["index"] = idx + 1
    context[state_key] = state

    return NodeResult(
        success=True,
        next_edge=EdgeLabel.LOOP_BODY,
        output_key=node.output_key,
        output_value=current_item,
    )
