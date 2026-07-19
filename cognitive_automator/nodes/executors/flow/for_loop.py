"""
=============================================================================
 FOR LOOP EXECUTOR
=============================================================================
This module executes standard numeric for-loops (e.g., repeating N times).
It tracks iterations and directs flow backwards to the loop body or forwards to exit.

Key Features:
1. Decrements/increments internal counters safely.
2. Emits loop-body and loop-end edge signals.

Think of this module as a metronome ticking down a set number of beats.
=============================================================================
"""

from ..base import *

def execute_for_loop(node: ForLoopNode, context: dict[str, Any], graph: ActionGraph) -> NodeResult:
    """
    C++ style counter loop: for (int i = start; i < end; i += step)
    Data is resolved from incoming DATA_BIND edges.
    """
    state_key = f"_for_{node.id}"
    current_val = context.get(state_key)

    # Resolve data sources from graph edges
    data_sources = [e.source_id for e in graph.edges if e.target_id == node.id and e.label == EdgeLabel.DATA_BIND]
    
    # Cap the loop end based on data length if sources exist
    loop_end = node.end
    for src_id in data_sources:
        src_node = graph.nodes.get(src_id)
        if src_node and hasattr(src_node, "output_key"):
            key = src_node.output_key
            if key in context:
                data = context[key]
                if isinstance(data, (list, dict)):
                    loop_end = min(loop_end, len(data))

    if current_val is None:
        current_val = node.start
    
    # Condition check (continues while i < loop_end)
    should_continue = False
    if node.step > 0:
        should_continue = current_val < loop_end
    else:
        should_continue = current_val > loop_end

    if not should_continue:
        context.pop(state_key, None)
        context.pop(node.output_key, None)  # Scope isolation: cleanup iterator
        return NodeResult(success=True, next_edge=EdgeLabel.LOOP_END)

    # Prepare for next pass
    next_val = current_val + node.step
    context[state_key] = next_val

    return NodeResult(
        success=True,
        next_edge=EdgeLabel.LOOP_BODY,
        output_key=node.output_key,
        output_value=current_val,
    )
