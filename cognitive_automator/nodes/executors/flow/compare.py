"""
=============================================================================
 COMPARE EXECUTOR
=============================================================================
This module performs logical comparisons (e.g., greater than, equals) between values.
It injects the boolean result back into the runtime state for branching.

Key Features:
1. Evaluates standard operators (==, !=, >, <) on variables.
2. Supports type coercion to ensure robust comparisons.

Think of this module as the scale weighing two pieces of data against each other.
=============================================================================
"""

from ..base import *

def execute_compare(node: CompareNode, context: dict[str, Any]) -> NodeResult:
    """
    Resolves both operands from context (supports {{key}} templates),
    applies the operator, and returns TRUE or FALSE edge.
    """
    def _resolve(template: str) -> str:
        from cognitive_automator.llm.templates import render_prompt
        return render_prompt(template, context)

    left = _resolve(node.left_operand)
    right = _resolve(node.right_operand)

    op = node.operator
    cs = node.case_sensitive

    try:
        if op == CompareOp.IS_EMPTY:
            passed = left.strip() == ""
        elif op == CompareOp.IS_NOT_EMPTY:
            passed = left.strip() != ""
        elif op in (CompareOp.NUM_GT, CompareOp.NUM_LT,
                    CompareOp.NUM_GTE, CompareOp.NUM_LTE, CompareOp.NUM_EQUALS):
            lv, rv = float(left), float(right)
            passed = {
                CompareOp.NUM_GT:     lv > rv,
                CompareOp.NUM_LT:     lv < rv,
                CompareOp.NUM_GTE:    lv >= rv,
                CompareOp.NUM_LTE:    lv <= rv,
                CompareOp.NUM_EQUALS: lv == rv,
            }[op]
        else:
            # String operators
            left_val, right_val = (left, right) if cs else (left.lower(), right.lower())
            passed = {
                CompareOp.EQUALS:      left_val == right_val,
                CompareOp.NOT_EQUALS:  left_val != right_val,
                CompareOp.CONTAINS:    right_val in left_val,
                CompareOp.NOT_CONTAINS: right_val not in left_val,
                CompareOp.STARTS_WITH: left_val.startswith(right_val),
                CompareOp.ENDS_WITH:   left_val.endswith(right_val),
            }[op]
    except (ValueError, KeyError) as exc:
        return NodeResult(success=False, error=f"CompareNode error: {exc}")

    log.debug("CompareNode: %r %s %r → %s", left, op.value, right, passed)
    return NodeResult(success=True, next_edge=EdgeLabel.TRUE if passed else EdgeLabel.FALSE)
